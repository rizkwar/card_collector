import csv
from collections import defaultdict
from pathlib import Path

from django.conf import settings
from django.core.management.base import BaseCommand, CommandError
from django.db import transaction

from cards.models import Card, Franchise, Pack, PackCard, Rarity


REQUIRED_COLUMNS = {
    "franchise",
    "pack",
    "cards_per_pack",
    "is_active",
    "card_name",
    "rarity",
    "weight",
    "image_url",
}
RARITY_VALUES = {choice.value for choice in Rarity}


class Command(BaseCommand):
    help = "Seed franchises, packs, cards, and pack weights from a CSV spreadsheet."

    def add_arguments(self, parser):
        parser.add_argument(
            "--file",
            type=Path,
            default=Path(settings.BASE_DIR) / "data" / "cards.csv",
            help="Path to the CSV spreadsheet.",
        )

    def handle(self, *args, **options):
        spreadsheet_path = Path(options["file"])
        if not spreadsheet_path.exists():
            raise CommandError(f"Spreadsheet not found: {spreadsheet_path}")

        rows = self.read_rows(spreadsheet_path)
        if not rows:
            raise CommandError("The spreadsheet does not contain any card rows.")

        franchises = defaultdict(list)
        packs = {}
        cards = {}

        for row_number, row in enumerate(rows, start=2):
            normalized = {
                key: (value or "").strip()
                for key, value in row.items()
            }
            self.validate_row(normalized, row_number)

            franchise_name = normalized["franchise"]
            pack_name = normalized["pack"]
            card_name = normalized["card_name"]
            pack_key = (franchise_name, pack_name)
            card_key = (franchise_name, card_name)

            pack_values = (
                int(normalized["cards_per_pack"]),
                self.parse_boolean(normalized["is_active"]),
            )
            if pack_key in packs and packs[pack_key] != pack_values:
                raise CommandError(
                    f"Row {row_number}: pack settings differ for {pack_name}."
                )
            packs[pack_key] = pack_values

            card_values = (
                normalized["rarity"],
                normalized["image_url"],
            )
            if card_key in cards and cards[card_key] != card_values:
                raise CommandError(
                    f"Row {row_number}: card details differ for {card_name}."
                )
            cards[card_key] = card_values
            franchises[franchise_name].append(
                (pack_key, card_key, int(normalized["weight"]))
            )

        with transaction.atomic():
            for franchise_name, franchise_rows in franchises.items():
                franchise, _ = Franchise.objects.get_or_create(name=franchise_name)
                PackCard.objects.filter(pack__franchise=franchise).delete()
                Pack.objects.filter(franchise=franchise).delete()
                Card.objects.filter(franchise=franchise).delete()

                pack_models = {}
                for pack_key, (cards_per_pack, is_active) in packs.items():
                    if pack_key[0] != franchise_name:
                        continue
                    pack_models[pack_key] = Pack.objects.create(
                        franchise=franchise,
                        name=pack_key[1],
                        cards_per_pack=cards_per_pack,
                        is_active=is_active,
                    )

                card_models = {}
                for card_key, (rarity, image_url) in cards.items():
                    if card_key[0] != franchise_name:
                        continue
                    card_models[card_key] = Card.objects.create(
                        franchise=franchise,
                        name=card_key[1],
                        rarity=rarity,
                        image_url=image_url,
                    )

                for pack_key, card_key, weight in franchise_rows:
                    PackCard.objects.create(
                        pack=pack_models[pack_key],
                        card=card_models[card_key],
                        weight=weight,
                    )

        self.stdout.write(
            self.style.SUCCESS(
                f"Seeded {len(franchises)} franchise(s), "
                f"{len(packs)} pack(s), and {len(cards)} card(s) "
                f"from {spreadsheet_path}."
            )
        )

    @staticmethod
    def read_rows(spreadsheet_path):
        with spreadsheet_path.open("r", encoding="utf-8-sig", newline="") as file:
            reader = csv.DictReader(file)
            columns = set(reader.fieldnames or [])
            missing = REQUIRED_COLUMNS - columns
            if missing:
                raise CommandError(
                    "Spreadsheet is missing columns: "
                    + ", ".join(sorted(missing))
                )
            return list(reader)

    @staticmethod
    def parse_boolean(value):
        if value.lower() in {"true", "1", "yes", "active"}:
            return True
        if value.lower() in {"false", "0", "no", "inactive"}:
            return False
        raise CommandError(f"Invalid is_active value: {value}")

    def validate_row(self, row, row_number):
        for column in REQUIRED_COLUMNS - {"image_url"}:
            if not row[column]:
                raise CommandError(f"Row {row_number}: {column} cannot be empty.")
        if row["rarity"] not in RARITY_VALUES:
            raise CommandError(f"Row {row_number}: invalid rarity {row['rarity']}.")
        try:
            if int(row["cards_per_pack"]) < 1 or int(row["weight"]) < 1:
                raise ValueError
        except ValueError as error:
            raise CommandError(
                f"Row {row_number}: cards_per_pack and weight must be positive integers."
            ) from error
        self.parse_boolean(row["is_active"])

import csv
from pathlib import Path

from django.conf import settings
from django.core.management.base import BaseCommand, CommandError


REQUIRED_COLUMNS = {
    "card_name",
    "image_url",
}


class Command(BaseCommand):
    help = "Check that every spreadsheet card has a matching local PNG image."

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

        missing = []
        checked = 0
        with spreadsheet_path.open("r", encoding="utf-8-sig", newline="") as file:
            reader = csv.DictReader(file)
            columns = set(reader.fieldnames or [])
            missing_columns = REQUIRED_COLUMNS - columns
            if missing_columns:
                raise CommandError(
                    "Spreadsheet is missing columns: "
                    + ", ".join(sorted(missing_columns))
                )

            for row_number, row in enumerate(reader, start=2):
                card_name = (row.get("card_name") or "").strip()
                folder = (row.get("image_url") or "").strip()
                image_path = settings.BASE_DIR / "static" / "img" / folder / f"{card_name}.png"
                checked += 1
                if not image_path.is_file():
                    missing.append((row_number, image_path))

        if missing:
            self.stdout.write(self.style.ERROR(f"Missing {len(missing)} of {checked} card images:"))
            for row_number, image_path in missing:
                self.stdout.write(f"  row {row_number}: {image_path}")
            raise CommandError("Add the missing local PNG files before using card artwork.")

        self.stdout.write(self.style.SUCCESS(f"All {checked} spreadsheet card images are present."))

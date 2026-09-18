from django.core.management.base import BaseCommand

from cards.models import Card, Franchise, Pack, PackCard, Rarity


FRANCHISE_NAME = "Reverend Insanity"
PACK_NAME = "Starter Pack"

STARTER_CARDS = (
    ("Fang Yuan", Rarity.LEGENDARY, 5),
    ("Bai Ning Bing", Rarity.RARE, 15),
    ("Hei Luo Lan", Rarity.RARE, 15),
    ("Ying Wu Xie", Rarity.UNCOMMON, 20),
    ("Fairy Miao Yin", Rarity.UNCOMMON, 20),
    ("Laddy White Rabbit", Rarity.COMMON, 50),
)


class Command(BaseCommand):
    help = "Create the starter Reverend Insanity cards, pack, and pack weights."

    def handle(self, *args, **options):
        Franchise.objects.filter(name="Naruto").delete()
        Pack.objects.filter(franchise__name="Naruto").delete()
        Card.objects.filter(franchise__name="Naruto").delete()

        franchise, _ = Franchise.objects.get_or_create(name=FRANCHISE_NAME)

        PackCard.objects.filter(pack__franchise=franchise).delete()
        Pack.objects.filter(franchise=franchise).delete()
        Card.objects.filter(franchise=franchise).delete()

        pack = Pack.objects.create(
            franchise=franchise,
            name=PACK_NAME,
            cards_per_pack=5,
            is_active=True,
        )

        for name, rarity, weight in STARTER_CARDS:
            card = Card.objects.create(
                franchise=franchise,
                name=name,
                rarity=rarity,
            )
            PackCard.objects.create(
                pack=pack,
                card=card,
                weight=weight,
            )

        self.stdout.write(
            self.style.SUCCESS(
                "Starter Reverend Insanity data is ready: 6 cards and 1 pack.",
            ),
        )

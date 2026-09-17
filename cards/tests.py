from unittest.mock import patch

from django.core.management import call_command
from django.test import TestCase
from django.urls import reverse

from .models import Card, Franchise, Pack, PackCard
from .views import PROTOTYPE_CARDS, draw_card


class PrototypePackTests(TestCase):
    def test_open_pack_only_accepts_post(self):
        response = self.client.get(reverse("open_pack"))

        self.assertEqual(response.status_code, 405)

    @patch("cards.views.draw_card")
    def test_opening_a_pack_counts_duplicate_cards_in_the_session(self, mock_draw_card):
        call_command("seed_cards")
        fang_yuan = PROTOTYPE_CARDS[0]
        mock_draw_card.side_effect = [fang_yuan] * 5

        response = self.client.post(reverse("open_pack"))

        self.assertEqual(response.status_code, 200)
        self.assertEqual(self.client.session["collection"], {"Fang Yuan": 5})
        self.assertContains(response, "Copy #5")

    def test_collection_page_calculates_progress_from_the_session(self):
        session = self.client.session
        session["collection"] = {
            "Fang Yuan": 2,
            "Fairy Miao Yin": 1,
        }
        session.save()

        response = self.client.get(reverse("collection"))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "2 of 6 unique cards found")
        self.assertContains(response, "3 cards collected")


class SeedCardsCommandTests(TestCase):
    def test_seed_cards_creates_starter_data_without_duplicates(self):
        call_command("seed_cards")
        call_command("seed_cards")

        franchise = Franchise.objects.get(name="Reverend Insanity")
        pack = Pack.objects.get(franchise=franchise, name="Starter Pack")

        self.assertEqual(Card.objects.filter(franchise=franchise).count(), 6)
        self.assertEqual(PackCard.objects.filter(pack=pack).count(), 6)
        self.assertEqual(
            PackCard.objects.get(
                pack=pack,
                card__name="Fang Yuan",
            ).weight,
            5,
        )

    def test_draw_card_uses_database_pack_cards(self):
        call_command("seed_cards")
        pack = Pack.objects.get(name="Starter Pack")

        cards = [draw_card(pack) for _ in range(pack.cards_per_pack)]

        self.assertEqual(len(cards), 5)
        self.assertTrue(all(isinstance(card, Card) for card in cards))
        self.assertTrue(all(card.franchise.name == "Reverend Insanity" for card in cards))

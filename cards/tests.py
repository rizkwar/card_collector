from unittest.mock import patch

from django.test import TestCase
from django.urls import reverse

from .views import PROTOTYPE_CARDS


class PrototypePackTests(TestCase):
    def test_open_pack_only_accepts_post(self):
        response = self.client.get(reverse("open_pack"))

        self.assertEqual(response.status_code, 405)

    @patch("cards.views.draw_card")
    def test_opening_a_pack_counts_duplicate_cards_in_the_session(self, mock_draw_card):
        naruto = PROTOTYPE_CARDS[0]
        mock_draw_card.side_effect = [naruto] * 5

        response = self.client.post(reverse("open_pack"))

        self.assertEqual(response.status_code, 200)
        self.assertEqual(self.client.session["collection"], {"Naruto Uzumaki": 5})
        self.assertContains(response, "Copy #5")

    def test_collection_page_calculates_progress_from_the_session(self):
        session = self.client.session
        session["collection"] = {
            "Naruto Uzumaki": 2,
            "Madara Uchiha": 1,
        }
        session.save()

        response = self.client.get(reverse("collection"))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "2 of 6 unique cards found")
        self.assertContains(response, "3 cards collected")

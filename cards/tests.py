import os
import tempfile
from unittest.mock import patch

from django.contrib.auth import get_user_model
from django.core.management import call_command
from django.test import TestCase
from django.urls import reverse

from .models import Card, Franchise, Pack, PackCard, UserCard
from .views import draw_card


class PrototypePackTests(TestCase):
    def test_home_page_prompts_login_when_logged_out(self):
        response = self.client.get(reverse("home"))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Log in to open a pack")

    def test_open_pack_requires_login(self):
        response = self.client.get(reverse("open_pack"))

        self.assertEqual(response.status_code, 302)
        self.assertIn("/accounts/login/", response.url)

    def test_login_page_renders_login_form(self):
        response = self.client.get(reverse("login"))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Log in")
        self.assertContains(response, "username")
        self.assertContains(response, "password")

    def test_signup_creates_and_logs_in_user(self):
        response = self.client.post(
            reverse("signup"),
            {
                "username": "new-player",
                "password1": "strong-password-123",
                "password2": "strong-password-123",
            },
        )

        self.assertRedirects(response, reverse("pack_list"))
        self.assertTrue(self.client.session.get("_auth_user_id"))
        self.assertTrue(
            get_user_model().objects.filter(username="new-player").exists()
        )

    @patch("cards.views.draw_card")
    def test_opening_a_pack_saves_duplicate_cards_to_user_collection(self, mock_draw_card):
        call_command("seed_cards")
        user = get_user_model().objects.create_user(
            username="session-user",
            password="secret-pass-123",
        )
        card = Card.objects.order_by("pk").first()
        pack = Pack.objects.order_by("pk").first()
        mock_draw_card.side_effect = [card] * 5
        self.client.login(username="session-user", password="secret-pass-123")

        response = self.client.post(reverse("open_pack"))

        self.assertEqual(response.status_code, 200)
        self.assertEqual(
            UserCard.objects.get(
                user=user,
                card=card,
            ).amount,
            5,
        )
        self.assertContains(response, f"Copy #{pack.cards_per_pack}")

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

        franchise = Franchise.objects.order_by("pk").first()
        pack = Pack.objects.filter(franchise=franchise).first()

        self.assertGreater(Card.objects.filter(franchise=franchise).count(), 0)
        self.assertGreater(PackCard.objects.filter(pack=pack).count(), 0)
        self.assertTrue(PackCard.objects.filter(pack=pack).exists())
        self.assertTrue(
            Card.objects.filter(
                franchise=franchise,
                image_url__startswith="/static/img/",
            ).exists()
        )

    def test_seed_cards_creates_new_pack_from_spreadsheet(self):
        spreadsheet = tempfile.NamedTemporaryFile(
            mode="w",
            suffix=".csv",
            encoding="utf-8",
            newline="",
            delete=False,
        )
        try:
            spreadsheet.write(
                "franchise,pack,cards_per_pack,is_active,card_name,rarity,weight,image_url\n"
                "Reverend Insanity,Expansion Pack,3,true,Fang Yuan,LEGENDARY,10,reverend insanity\n"
            )
            spreadsheet.close()

            call_command("seed_cards", file=spreadsheet.name)

            pack = Pack.objects.get(
                franchise__name="Reverend Insanity",
                name="Expansion Pack",
            )
            self.assertEqual(pack.cards_per_pack, 3)
            self.assertTrue(
                PackCard.objects.filter(
                    pack=pack,
                    card__name="Fang Yuan",
                    weight=10,
                ).exists()
            )
        finally:
            os.unlink(spreadsheet.name)

    def test_draw_card_uses_database_pack_cards(self):
        call_command("seed_cards")
        pack = Pack.objects.order_by("pk").first()

        cards = [draw_card(pack) for _ in range(pack.cards_per_pack)]

        self.assertEqual(len(cards), pack.cards_per_pack)
        self.assertTrue(all(isinstance(card, Card) for card in cards))
        self.assertTrue(all(card.franchise == pack.franchise for card in cards))

    def test_pack_list_page_renders_seeded_pack(self):
        call_command("seed_cards")

        response = self.client.get(reverse("pack_list"))

        self.assertEqual(response.status_code, 200)
        pack = Pack.objects.order_by("pk").first()
        self.assertContains(response, pack.name)

    def test_selecting_a_pack_updates_the_homepage(self):
        call_command("seed_cards")
        pack = Pack.objects.order_by("-pk").first()

        response = self.client.get(reverse("pack_select", args=[pack.pk]))

        self.assertRedirects(response, reverse("home"))
        self.assertEqual(self.client.session["selected_pack_id"], pack.pk)
        homepage = self.client.get(reverse("home"))
        self.assertContains(homepage, pack.name)

    @patch("cards.views.draw_card")
    def test_pack_detail_opens_the_selected_pack(self, mock_draw_card):
        call_command("seed_cards")
        user = get_user_model().objects.create_user(
            username="pack-user",
            password="secret-pass-123",
        )
        pack = Pack.objects.order_by("pk").first()
        card = Card.objects.order_by("pk").first()
        mock_draw_card.return_value = card
        self.client.login(username="pack-user", password="secret-pass-123")

        response = self.client.post(reverse("pack_open", args=[pack.pk]))

        self.assertEqual(response.status_code, 200)
        self.assertEqual(UserCard.objects.get(user=user, card=card).amount, pack.cards_per_pack)
        self.assertContains(response, card.name)

    def test_card_detail_page_renders_card_information(self):
        call_command("seed_cards")
        card = Card.objects.order_by("pk").first()

        response = self.client.get(reverse("card_detail", args=[card.pk]))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, card.name)
        self.assertContains(response, card.franchise.name)


class UserCollectionTests(TestCase):
    def setUp(self):
        call_command("seed_cards")
        self.user = get_user_model().objects.create_user(
            username="tester",
            password="secret-pass-123",
        )
        self.pack = Pack.objects.order_by("pk").first()
        self.card = Card.objects.order_by("pk").first()

    @patch("cards.views.draw_card")
    def test_pack_open_requires_login(self, mock_draw_card):
        mock_draw_card.return_value = self.card

        response = self.client.post(reverse("pack_open", args=[self.pack.pk]))

        self.assertEqual(response.status_code, 302)
        self.assertIn("/accounts/login/", response.url)

    @patch("cards.views.draw_card")
    def test_pack_open_updates_user_collection(self, mock_draw_card):
        mock_draw_card.return_value = self.card
        self.client.login(username="tester", password="secret-pass-123")

        response = self.client.post(reverse("pack_open", args=[self.pack.pk]))

        self.assertEqual(response.status_code, 200)
        self.assertEqual(
            UserCard.objects.get(user=self.user, card=self.card).amount,
            self.pack.cards_per_pack,
        )
        self.assertContains(response, self.card.name)

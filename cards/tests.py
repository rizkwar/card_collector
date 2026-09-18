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
        fang_yuan = Card.objects.get(name="Fang Yuan")
        mock_draw_card.side_effect = [fang_yuan] * 5
        self.client.login(username="session-user", password="secret-pass-123")

        response = self.client.post(reverse("open_pack"))

        self.assertEqual(response.status_code, 200)
        self.assertEqual(
            UserCard.objects.get(
                user=user,
                card=Card.objects.get(name="Fang Yuan"),
            ).amount,
            5,
        )
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

    def test_pack_list_page_renders_seeded_pack(self):
        call_command("seed_cards")

        response = self.client.get(reverse("pack_list"))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Starter Pack")

    @patch("cards.views.draw_card")
    def test_pack_detail_opens_the_selected_pack(self, mock_draw_card):
        call_command("seed_cards")
        user = get_user_model().objects.create_user(
            username="pack-user",
            password="secret-pass-123",
        )
        pack = Pack.objects.get(name="Starter Pack")
        fang_yuan = Card.objects.get(name="Fang Yuan")
        mock_draw_card.return_value = fang_yuan
        self.client.login(username="pack-user", password="secret-pass-123")

        response = self.client.post(reverse("pack_open", args=[pack.pk]))

        self.assertEqual(response.status_code, 200)
        self.assertEqual(UserCard.objects.get(user=user, card=fang_yuan).amount, 5)
        self.assertContains(response, "Fang Yuan")

    def test_card_detail_page_renders_card_information(self):
        call_command("seed_cards")
        card = Card.objects.filter(franchise__name="Reverend Insanity").first()

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

    @patch("cards.views.draw_card")
    def test_pack_open_requires_login(self, mock_draw_card):
        pack = Pack.objects.get(name="Starter Pack")
        mock_draw_card.return_value = Card.objects.get(name="Fang Yuan")

        response = self.client.post(reverse("pack_open", args=[pack.pk]))

        self.assertEqual(response.status_code, 302)
        self.assertIn("/accounts/login/", response.url)

    @patch("cards.views.draw_card")
    def test_pack_open_updates_user_collection(self, mock_draw_card):
        pack = Pack.objects.get(name="Starter Pack")
        fang_yuan = Card.objects.get(name="Fang Yuan")
        mock_draw_card.return_value = fang_yuan
        self.client.login(username="tester", password="secret-pass-123")

        response = self.client.post(reverse("pack_open", args=[pack.pk]))

        self.assertEqual(response.status_code, 200)
        self.assertEqual(UserCard.objects.get(user=self.user, card=fang_yuan).amount, 5)
        self.assertContains(response, "Fang Yuan")

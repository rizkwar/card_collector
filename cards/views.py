import random

from django.contrib.auth import login
from django.contrib.auth.decorators import login_required
from django.contrib.auth.forms import UserCreationForm
from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.http import require_POST

from .models import Card, Pack, PackCard, UserCard


def signup(request):
    if request.user.is_authenticated:
        return redirect("home")

    form = UserCreationForm(request.POST or None)
    if request.method == "POST" and form.is_valid():
        user = form.save()
        login(request, user)
        return redirect("pack_list")

    return render(request, "registration/signup.html", {"form": form})


PROTOTYPE_CARDS = [
    {
        "name": "Fang Yuan",
        "franchise": "Reverend Insanity",
        "rarity": "LEGENDARY",
    },
    {
        "name": "Bai Ning Bing",
        "franchise": "Reverend Insanity",
        "rarity": "RARE",
    },
    {
        "name": "Hei Luo Lan",
        "franchise": "Reverend Insanity",
        "rarity": "RARE",
    },
    {
        "name": "Ying Wu Xie",
        "franchise": "Reverend Insanity",
        "rarity": "UNCOMMON",
    },
    {
        "name": "Fairy Miao Yin",
        "franchise": "Reverend Insanity",
        "rarity": "UNCOMMON",
    },
    {
        "name": "Laddy White Rabbit",
        "franchise": "Reverend Insanity",
        "rarity": "COMMON",
    },
]


RARITY_WEIGHTS = {
    "COMMON": 100,
    "UNCOMMON": 40,
    "RARE": 15,
    "LEGENDARY": 5,
}


def roll_rarity():
    rarities = list(RARITY_WEIGHTS.keys())
    weights = list(RARITY_WEIGHTS.values())

    return random.choices(
        rarities,
        weights=weights,
        k=1,
    )[0]


def draw_card(pack):
    pack_cards = list(
        pack.pack_cards.select_related("card", "card__franchise")
    )

    if not pack_cards:
        raise ValueError(f"No cards are configured for pack: {pack.name}")

    total_weight = sum(entry.weight for entry in pack_cards)
    if total_weight <= 0:
        raise ValueError(f"Pack weights must be positive for {pack.name}")

    selected_entry = random.choices(
        population=pack_cards,
        weights=[entry.weight for entry in pack_cards],
        k=1,
    )[0]

    return selected_entry.card


def prototype_home(request):
    return render(
        request,
        "prototype/home.html",
    )


def _open_pack_for_session(request, pack):
    drawn_cards = [
        draw_card(pack)
        for _ in range(pack.cards_per_pack)
    ]

    collection = request.session.get("collection", {})
    pulled_cards = []

    for card in drawn_cards:
        if hasattr(card, "name"):
            card_name = card.name
            franchise_name = card.franchise.name
            rarity = card.rarity
        else:
            card_name = card["name"]
            franchise_name = card["franchise"]
            rarity = card["rarity"]

        previous_amount = collection.get(card_name, 0)
        collection[card_name] = previous_amount + 1

        pulled_cards.append(
            {
                "name": card_name,
                "franchise": franchise_name,
                "rarity": rarity,
                "is_duplicate": previous_amount > 0,
                "collection_amount": collection[card_name],
            }
        )

    request.session["collection"] = collection

    return render(
        request,
        "prototype/result.html",
        {
            "drawn_cards": pulled_cards,
        },
    )


@login_required
@require_POST
def prototype_open_pack(request):
    pack = Pack.objects.filter(is_active=True).order_by("pk").first()
    if pack is None:
        raise ValueError("No active pack is available in the database.")

    return _open_pack_for_user(request, pack)


def _open_pack_for_user(request, pack):
    drawn_cards = [draw_card(pack) for _ in range(pack.cards_per_pack)]
    pulled_cards = []

    for card in drawn_cards:
        user_card, created = UserCard.objects.get_or_create(
            user=request.user,
            card=card,
            defaults={"amount": 0},
        )
        previous_amount = user_card.amount
        user_card.amount += 1
        user_card.save()

        pulled_cards.append(
            {
                "name": card.name,
                "franchise": card.franchise.name,
                "rarity": card.rarity,
                "is_duplicate": previous_amount > 0 or not created,
                "collection_amount": user_card.amount,
            }
        )

    return render(
        request,
        "prototype/result.html",
        {
            "drawn_cards": pulled_cards,
        },
    )


@login_required
@require_POST
def open_pack(request, pk):
    pack = get_object_or_404(Pack, pk=pk, is_active=True)
    return _open_pack_for_user(request, pack)


def prototype_collection(request):
    collection = request.session.get(
        "collection",
        {},
    )

    owned_cards = [
        card
        for card in PROTOTYPE_CARDS
        if card["name"] in collection
    ]

    total_unique_possible = len(PROTOTYPE_CARDS)
    unique_owned = len(owned_cards)
    total_copies = sum(collection[card["name"]] for card in owned_cards)

    percent = (
        round(
            (unique_owned / total_unique_possible) * 100,
            1,
        )
        if total_unique_possible
        else 0
    )

    by_franchise = {}

    for card in PROTOTYPE_CARDS:
        card_name = card["name"]

        if card_name not in collection:
            continue

        franchise = card["franchise"]

        by_franchise.setdefault(
            franchise,
            [],
        ).append(
            {
                "name": card_name,
                "amount": collection[card_name],
                "rarity": card["rarity"],
            }
        )

    return render(
        request,
        "prototype/collection.html",
        {
            "by_franchise": by_franchise,
            "unique_owned": unique_owned,
            "total_unique_possible": total_unique_possible,
            "total_copies": total_copies,
            "percent": percent,
        },
    )


def collection(request):
    if request.user.is_authenticated:
        owned_entries = (
            UserCard.objects.filter(user=request.user)
            .select_related("card", "card__franchise")
            .order_by("card__name")
        )
        total_unique_possible = Card.objects.count()
        unique_owned = owned_entries.count()
        total_copies = sum(entry.amount for entry in owned_entries)
        percent = (
            round((unique_owned / total_unique_possible) * 100, 1)
            if total_unique_possible
            else 0
        )

        by_franchise = {}
        for entry in owned_entries:
            franchise_name = entry.card.franchise.name
            by_franchise.setdefault(franchise_name, []).append(
                {
                    "name": entry.card.name,
                    "amount": entry.amount,
                    "rarity": entry.card.rarity,
                }
            )

        return render(
            request,
            "prototype/collection.html",
            {
                "by_franchise": by_franchise,
                "unique_owned": unique_owned,
                "total_unique_possible": total_unique_possible,
                "total_copies": total_copies,
                "percent": percent,
            },
        )

    return prototype_collection(request)


def pack_list(request):
    packs = Pack.objects.filter(is_active=True).select_related("franchise")
    return render(
        request,
        "packs/pack_list.html",
        {"packs": packs},
    )


def pack_detail(request, pk):
    pack = get_object_or_404(
        Pack.objects.select_related("franchise"),
        pk=pk,
    )
    pack_cards = (
        PackCard.objects.filter(pack=pack)
        .select_related("card", "card__franchise")
        .order_by("card__rarity", "card__name")
    )
    return render(
        request,
        "packs/pack_detail.html",
        {"pack": pack, "pack_cards": pack_cards},
    )


def card_detail(request, pk):
    card = get_object_or_404(
        Card.objects.select_related("franchise"),
        pk=pk,
    )
    pack_entries = (
        PackCard.objects.filter(card=card)
        .select_related("pack", "pack__franchise")
        .order_by("pack__name")
    )
    return render(
        request,
        "cards/card_detail.html",
        {"card": card, "pack_entries": pack_entries},
    )

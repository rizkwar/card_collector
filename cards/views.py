import random

from django.shortcuts import render
from django.views.decorators.http import require_POST


PROTOTYPE_CARDS = [
    {
        "name": "Naruto Uzumaki",
        "franchise": "Naruto",
        "rarity": "COMMON",
    },
    {
        "name": "Sakura Haruno",
        "franchise": "Naruto",
        "rarity": "COMMON",
    },
    {
        "name": "Sasuke Uchiha",
        "franchise": "Naruto",
        "rarity": "UNCOMMON",
    },
    {
        "name": "Kakashi Hatake",
        "franchise": "Naruto",
        "rarity": "UNCOMMON",
    },
    {
        "name": "Madara Uchiha",
        "franchise": "Naruto",
        "rarity": "RARE",
    },
    {
        "name": "Hashirama Senju",
        "franchise": "Naruto",
        "rarity": "LEGENDARY",
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


def draw_card():
    rarity = roll_rarity()

    pool = [
        card
        for card in PROTOTYPE_CARDS
        if card["rarity"] == rarity
    ]

    if not pool:
        raise ValueError(f"No cards exist for rarity {rarity}")

    return random.choice(pool)


def prototype_home(request):
    return render(
        request,
        "prototype/home.html",
    )


@require_POST
def prototype_open_pack(request):
    drawn_cards = [
        draw_card()
        for _ in range(5)
    ]

    collection = request.session.get("collection", {})
    pulled_cards = []

    for card in drawn_cards:
        card_name = card["name"]
        previous_amount = collection.get(card_name, 0)
        collection[card_name] = previous_amount + 1

        pulled_cards.append(
            {
                **card,
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

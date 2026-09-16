import random

from django.shortcuts import render


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


def prototype_open_pack(request):
    drawn_cards = [
        draw_card()
        for _ in range(5)
    ]

    return render(
        request,
        "prototype/result.html",
        {
            "drawn_cards": drawn_cards,
        },
    )
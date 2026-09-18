# Card Collector

A Django trading card collection game.

## Seed data from a spreadsheet

Card and pack data lives in `data/cards.csv`, which can be edited in Excel or
Google Sheets and exported as CSV.

The spreadsheet must contain these columns:

```text
franchise,pack,cards_per_pack,is_active,card_name,rarity,weight,image_url
```

Each row connects one card to one pack. `rarity` must be one of `COMMON`,
`UNCOMMON`, `RARE`, or `LEGENDARY`. The final `image_url` column stores the
lowercase local franchise folder name, such as `honkai star rail`. The seed
command resolves it to `/static/img/<folder>/<card name>.png`.

Adding a new `pack` value to the spreadsheet automatically creates that pack
when the seed command runs. The pack does not need to exist in the database
first.

Run the default spreadsheet with:

```powershell
python manage.py seed_cards
```

Use another spreadsheet with:

```powershell
python manage.py seed_cards --file path\to\cards.csv
```

Check that local artwork exists for every spreadsheet card with:

```powershell
python manage.py validate_card_images
```

The command expects each image at
`static/img/<image_url>/<card_name>.png`. For example, a row with
`image_url=honkai star rail` and `card_name=Acheron` requires
`static/img/honkai star rail/Acheron.png`.

Missing images are allowed. Cards without a matching PNG use the normal
rarity placeholder and still display their card name.

Seeding replaces the packs and cards for the franchises included in the
spreadsheet, so run it before collecting cards or use it only with data you
intend to refresh.
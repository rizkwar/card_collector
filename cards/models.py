from django.conf import settings
from django.core.validators import MinValueValidator
from django.db import models


class Rarity(models.TextChoices):
    COMMON = "COMMON", "Common"
    UNCOMMON = "UNCOMMON", "Uncommon"
    RARE = "RARE", "Rare"
    LEGENDARY = "LEGENDARY", "Legendary"


class Franchise(models.Model):
    """A card universe, such as Naruto or Pokemon."""

    name = models.CharField(max_length=100, unique=True)

    class Meta:
        ordering = ["name"]
        verbose_name_plural = "franchises"

    def __str__(self):
        return self.name


class Card(models.Model):
    """A unique collectible card belonging to one franchise."""

    franchise = models.ForeignKey(
        Franchise,
        on_delete=models.CASCADE,
        related_name="cards",
    )
    name = models.CharField(max_length=150)
    rarity = models.CharField(max_length=20, choices=Rarity.choices)
    image_url = models.URLField(blank=True)

    class Meta:
        ordering = ["franchise__name", "name"]
        constraints = [
            models.UniqueConstraint(
                fields=["franchise", "name"],
                name="unique_card_name_per_franchise",
            ),
        ]

    def __str__(self):
        return f"{self.name} ({self.franchise.name})"


class Pack(models.Model):
    """A purchasable pack that contains cards from one franchise."""

    franchise = models.ForeignKey(
        Franchise,
        on_delete=models.CASCADE,
        related_name="packs",
    )
    name = models.CharField(max_length=100)
    cards_per_pack = models.PositiveSmallIntegerField(default=5)
    is_active = models.BooleanField(default=True)

    class Meta:
        ordering = ["franchise__name", "name"]
        constraints = [
            models.UniqueConstraint(
                fields=["franchise", "name"],
                name="unique_pack_name_per_franchise",
            ),
        ]

    def __str__(self):
        return f"{self.franchise.name} — {self.name}"


class PackCard(models.Model):
    """A card's inclusion and relative probability within a pack."""

    pack = models.ForeignKey(
        Pack,
        on_delete=models.CASCADE,
        related_name="pack_cards",
    )
    card = models.ForeignKey(
        Card,
        on_delete=models.CASCADE,
        related_name="pack_entries",
    )
    weight = models.PositiveIntegerField(
        validators=[MinValueValidator(1)],
    )

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["pack", "card"],
                name="unique_card_per_pack",
            ),
        ]

    def __str__(self):
        return f"{self.pack}: {self.card.name} (weight {self.weight})"


class UserCard(models.Model):
    """The quantity of one card owned by one authenticated user."""

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="user_cards",
    )
    card = models.ForeignKey(
        Card,
        on_delete=models.CASCADE,
        related_name="owner_entries",
    )
    amount = models.PositiveIntegerField(
        default=1,
        validators=[MinValueValidator(1)],
    )

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["user", "card"],
                name="unique_card_per_user",
            ),
        ]

    def __str__(self):
        return f"{self.user} owns {self.amount} × {self.card.name}"

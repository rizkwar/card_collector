from django.contrib import admin

from .models import Card, Franchise, Pack, PackCard, UserCard


class PackCardInline(admin.TabularInline):
    """Edit a pack's card list and weights directly on the pack page."""

    model = PackCard
    extra = 1
    autocomplete_fields = ("card",)


@admin.register(Franchise)
class FranchiseAdmin(admin.ModelAdmin):
    list_display = ("name",)
    search_fields = ("name",)


@admin.register(Card)
class CardAdmin(admin.ModelAdmin):
    list_display = ("name", "franchise", "rarity", "has_image")
    list_filter = ("franchise", "rarity")
    search_fields = ("name", "franchise__name")
    list_select_related = ("franchise",)

    @admin.display(boolean=True, description="Image URL")
    def has_image(self, card):
        return bool(card.image_url)


@admin.register(Pack)
class PackAdmin(admin.ModelAdmin):
    list_display = ("name", "franchise", "cards_per_pack", "is_active")
    list_filter = ("franchise", "is_active")
    search_fields = ("name", "franchise__name")
    list_select_related = ("franchise",)
    inlines = (PackCardInline,)


@admin.register(PackCard)
class PackCardAdmin(admin.ModelAdmin):
    list_display = ("pack", "card", "card_franchise", "weight")
    list_filter = ("pack", "card__franchise")
    search_fields = ("pack__name", "card__name")
    list_select_related = ("pack__franchise", "card__franchise")
    autocomplete_fields = ("pack", "card")

    @admin.display(ordering="card__franchise__name", description="Franchise")
    def card_franchise(self, pack_card):
        return pack_card.card.franchise


@admin.register(UserCard)
class UserCardAdmin(admin.ModelAdmin):
    list_display = ("user", "card", "card_franchise", "amount")
    list_filter = ("card__franchise", "card__rarity")
    search_fields = ("user__username", "card__name")
    list_select_related = ("user", "card__franchise")
    autocomplete_fields = ("user", "card")

    @admin.display(ordering="card__franchise__name", description="Franchise")
    def card_franchise(self, user_card):
        return user_card.card.franchise

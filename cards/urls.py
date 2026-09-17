from django.urls import path

from . import views


urlpatterns = [
    path(
        "",
        views.prototype_home,
        name="home",
    ),
    path(
        "open-pack/",
        views.prototype_open_pack,
        name="open_pack",
    ),
    path(
        "collection/",
        views.prototype_collection,
        name="collection",
    ),
    path(
        "packs/",
        views.pack_list,
        name="pack_list",
    ),
    path(
        "packs/<int:pk>/",
        views.pack_detail,
        name="pack_detail",
    ),
    path(
        "cards/<int:pk>/",
        views.card_detail,
        name="card_detail",
    ),
]
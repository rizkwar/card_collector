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
]
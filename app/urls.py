from django.urls import path

from . import views

urlpatterns = [
    path("", views.index, name="index"),
    path("forbidden", views.forbidden, name="forbidden"),
    path("catalog", views.catalog, name="catalog"),
]

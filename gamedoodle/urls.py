"""gamedoodle URL Configuration

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/3.1/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import include, path

from gamedoodle.core import views

urlpatterns = [
    path("admin/", admin.site.urls),
    path("whoareyou/", views.who_are_you, name="who-are-you"),
    path("logout/", views.logout, name="logout"),
    path("events/<uuid:uuid>", views.EventDetailView.as_view(), name="event-detail"),
    path("events/<uuid:uuid>/votegame", views.vote_game, name="event-vote-game"),
    path("events/<uuid:uuid>/addgame", views.add_game, name="event-add-game"),
    path(
        "events/<uuid:uuid>/notifications",
        views.setup_email_notifications,
        name="event-notifications-setup",
    ),
    path(
        "events/<uuid:uuid>/notifications/subscribe",
        views.subscribe_to_email_notifications,
        name="event-notifications-subscribe",
    ),
    path(
        "events/<uuid:uuid>/addgame/matching",
        views.add_matching_game,
        name="event-add-matching-game",
    ),
    path(
        "events/<uuid:uuid>/addgame/manually",
        views.add_game_manually,
        name="event-add-game-manually",
    ),
    path("events/", views.EventListView.as_view(), name="event-list"),
    path("", views.EventListView.as_view(), name="event-list-fallback"),
]

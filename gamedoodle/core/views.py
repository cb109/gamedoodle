from django.conf import settings
from django.http import HttpResponse
from django.shortcuts import redirect, render
from django.urls import reverse
from django.views import generic

from gamedoodle.core.models import Event, Vote


class EventListView(generic.ListView):
    model = Event
    ordering = ("-date",)


class EventDetailView(generic.DetailView):
    model = Event
    slug_url_kwarg = "uuid"
    slug_field = "uuid"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        event = self.get_object()
        games = list(event.games.all())

        # Augment the instances
        for game in games:
            game.votes = Vote.objects.filter(game=game, event=event).order_by(
                "username"
            )
        games = sorted(
            games, key=lambda game: f"{len(game.votes)}-{game.name}", reverse=True
        )

        context["games"] = games
        context["last_username"] = self.request.session.get("last_username", "")
        return context


def format_username(username):
    if settings.AUTO_FORMAT_USERNAMES:
        username = username.lower().capitalize()
    return username


def vote(request, uuid):
    event = Event.objects.get(uuid=uuid)

    username = format_username(request.POST["username"])

    vote_id = request.POST.get("vote_id")
    if vote_id:
        vote = Vote.objects.get(id=vote_id)
        if vote.username == username:
            vote.delete()

    game_id = request.POST.get("game_id")
    if game_id:
        Vote.objects.get_or_create(event=event, game_id=game_id, username=username)

    request.session["last_username"] = username
    return redirect(reverse("event-detail", kwargs={"uuid": uuid}))

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
        games = list(event.games.all().order_by("name"))

        # Augment the instances
        for game in games:
            game.votes = Vote.objects.filter(game=game, event=event).order_by(
                "username"
            )

        context["games"] = games
        return context


def vote(request, uuid):
    event = Event.objects.get(uuid=uuid)

    Vote.objects.get_or_create(
        event=event,
        game_id=request.POST["game_id"],
        username=request.POST["username"],
    )

    return redirect(reverse("event-detail", kwargs={"uuid": uuid}))

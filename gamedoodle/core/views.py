from django.conf import settings
from django.http import HttpResponse
from django.shortcuts import redirect, render
from django.urls import reverse
from django.views import generic

from gamedoodle.core.models import Event, Vote


def _has_username(request):
    return request.session.get("username") is not None


def _format_username(username):
    if settings.AUTO_FORMAT_USERNAMES:
        username = username.lower().capitalize()
    return username


def who_are_you(request):
    next_url = request.GET["next"]

    if request.method == "POST":
        request.session["username"] = _format_username(request.POST["username"])
        return redirect(next_url)

    return render(request, "core/who_are_you.html")


class EventListView(generic.ListView):
    model = Event
    ordering = ("-date",)


class EventDetailView(generic.DetailView):
    model = Event
    slug_url_kwarg = "uuid"
    slug_field = "uuid"

    def get(self, request, *args, **kargs):
        if not _has_username(request):
            who_are_you_url = reverse("who-are-you") + "?next=" + request.path
            return redirect(who_are_you_url)
        return super().get(request, *args, **kargs)

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
        return context


def vote(request, uuid):
    event = Event.objects.get(uuid=uuid)

    username = _format_username(request.POST["username"])

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

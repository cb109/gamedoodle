from django.conf import settings
from django.http import HttpRequest, HttpResponse
from django.shortcuts import redirect, render
from django.urls import reverse
from django.views import generic

from gamedoodle.core.models import Event, Vote


def _get_username(request):
    return request.session.get("username")


def _format_username(username):
    if settings.AUTO_FORMAT_USERNAMES:
        username = username.lower().capitalize()
    return username.strip()


def username_required(view):
    """Decorator for view functions and generic View http handlers."""

    def wrapper(*args, **kwargs):
        # Handle these different signatures:
        #   view(request, *args, **kwargs)
        #   .view(self, request, *args, **kwargs)
        request = args[0]
        if len(args) > 1 and isinstance(args[1], HttpRequest):
            request = args[1]

        if _get_username(request) in (None, ""):
            who_are_you_url = reverse("who-are-you") + "?next=" + request.path
            return redirect(who_are_you_url)

        return view(*args, **kwargs)

    return wrapper


def logout(request):
    request.session.flush()
    next_url = request.GET["next"]
    return redirect(next_url)


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

    @username_required
    def get(self, request, *args, **kargs):
        return super().get(request, *args, **kargs)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        event = self.get_object()
        username = _get_username(self.request)
        games = list(event.games.all())

        # Augment the instances
        for game in games:
            votes = Vote.objects.filter(game=game, event=event).order_by("username")
            game.votes = votes
            game.current_user_can_vote = not votes.filter(username=username).exists()
        games = sorted(
            games, key=lambda game: f"{len(game.votes)}-{game.name}", reverse=True
        )

        context["username"] = username
        context["games"] = games
        return context


@username_required
def vote(request, uuid):
    event = Event.objects.get(uuid=uuid)
    username = _get_username(request)

    vote_id = request.POST.get("vote_id")
    if vote_id:
        vote = Vote.objects.get(id=vote_id)
        if vote.username == username:
            vote.delete()

    game_id = request.POST.get("game_id")
    if game_id:
        Vote.objects.get_or_create(event=event, game_id=game_id, username=username)

    return redirect(reverse("event-detail", kwargs={"uuid": uuid}))

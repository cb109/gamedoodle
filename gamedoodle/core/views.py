from django.conf import settings
from django.http import HttpRequest, HttpResponse
from django.shortcuts import redirect, render
from django.urls import reverse
from django.views import generic

import requests
from gamedoodle.core.models import Event, Game, Vote


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
def vote_game(request, uuid):
    """Handle both voting and unvoting for a Game."""
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


@username_required
def add_game(request, uuid):
    """Display form to add a Game to an Event."""
    event = Event.objects.get(uuid=uuid)

    search_text = request.GET.get("q", "").strip()
    games = []
    if search_text:
        games = Game.objects.filter(name__icontains=search_text).order_by("name")[:100]

    return render(
        request,
        "core/event_add_game.html",
        {"event": event, "steam_games": games, "search_text": search_text},
    )


@username_required
def add_game_manually(request, uuid):
    """Add actual game as specified."""
    event = Event.objects.get(uuid=uuid)

    name = request.POST["name"].strip()
    image_url = request.POST.get("image_url", "")
    store_url = request.POST.get("store_url", "")
    is_free = request.POST.get("is_free", None) == "on"

    # Ensure Game exists.
    game, created = Game.objects.get_or_create(name=name)
    game.is_free = is_free
    if game.image_url != image_url and image_url.strip() != "":
        game.image_url = image_url
    if game.store_url != store_url and store_url.strip() != "":
        game.store_url = store_url
    game.save()

    event.games.add(game)
    return redirect(reverse("event-detail", kwargs={"uuid": uuid}))


@username_required
def add_game_steam(request, uuid):
    """Add actual game selected from Steam search results."""
    event = Event.objects.get(uuid=uuid)

    appid = request.POST["appid"]
    game = Game.objects.get(appid=appid)

    if not game.store_url:
        game.store_url = settings.STEAM_STORE_PAGE_BASE_URL + appid
        game.save()

    # Fetch to set/update details.
    url = settings.STEAM_API_BASE_URL_APPDETAILS + appid
    response = requests.get(url)
    data = response.json()[appid]["data"]

    screenshots = data.get("screenshots", [])
    if game.image_url == "" and screenshots:
        first_thumbnail = screenshots[0]["path_thumbnail"]
        game.image_url = first_thumbnail

    game.is_free = data["is_free"]
    game.save()

    event.games.add(game)
    return redirect(reverse("event-detail", kwargs={"uuid": uuid}))

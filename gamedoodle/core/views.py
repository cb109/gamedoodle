import textwrap

import requests
from django.conf import settings
from django.core.exceptions import ValidationError
from django.http import HttpRequest
from django.shortcuts import redirect, render
from django.urls import NoReverseMatch
from django.urls import resolve, reverse
from django.views import generic
from django.views.decorators.http import require_http_methods

from gamedoodle.core.models import Event, EventSubscription, Game, Vote
from gamedoodle.core.mailing import send_email_via_gmail


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


def _raise_if_event_not_writable(event):
    if event.read_only:
        raise ValidationError(f"{event} is in read-only mode")


def logout(request):
    request.session.flush()
    next_url = request.GET["next"]
    return redirect(next_url)


@require_http_methods(("GET", "POST"))
def who_are_you(request):
    next_url = request.GET["next"]

    if request.method == "POST":
        request.session["username"] = _format_username(request.POST["username"])
        return redirect(next_url)

    # If we are moving to an Event, let's get the list of usernames
    # and offer them to choose by the User, so it's easier to reuse
    # the same one across multiple devices.
    existing_usernames = []
    event = None
    try:
        match = resolve(next_url)
        if match.url_name == "event-detail":
            event = Event.objects.get(uuid=match.kwargs["uuid"])
            existing_usernames = sorted(
                list(
                    Vote.objects.filter(event=event)
                    .values_list("username", flat=True)
                    .distinct()
                )
            )
    except NoReverseMatch:
        pass

    return render(
        request,
        "core/who_are_you.html",
        {"event": event, "existing_usernames": existing_usernames},
    )


class EventListView(generic.ListView):
    model = Event
    queryset = Event.objects.filter(listed=True).order_by("-created_at")[:10]

    @username_required
    def get(self, request, *args, **kargs):
        return super().get(request, *args, **kargs)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["username"] = _get_username(self.request)
        context["events"] = self.get_queryset()
        return context


def calculate_votes_value_for_event_and_game(game, event):
    value = game.votes.count()
    if game.votes.filter(is_superlike=True).exists():
        num_event_participants = (
            event.vote_set.all().values_list("username", flat=True).distinct().count()
        )
        fraction = 1 / num_event_participants
        value += sum([fraction for _ in game.votes.filter(is_superlike=True)])
    return value


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

        subscribed = self.request.GET.get("subscribed") == "true"
        unsubscribed = self.request.GET.get("unsubscribed") == "true"

        # Augment the instances
        for game in games:
            votes = Vote.objects.filter(game=game, event=event).order_by("username")
            game.votes = votes
            game.votes_value = calculate_votes_value_for_event_and_game(game, event)
            game.current_user_can_vote = not votes.filter(username=username).exists()
            game.current_user_can_superlike = (
                votes.filter(username=username, is_superlike=False).exists()
                and not Vote.objects.filter(
                    event=event, username=username, is_superlike=True
                ).exists()
            )

        games = sorted(
            games, key=lambda game: f"{game.votes_value}-{game.name}", reverse=True
        )
        sorted_unique_votes_value = sorted(
            list(set([game.votes_value for game in games])), reverse=True
        )
        for game in games:
            game.voting_rank = sorted_unique_votes_value.index(game.votes_value) + 1

        context["username"] = username
        context["games"] = games

        context["subscribed"] = subscribed
        context["unsubscribed"] = unsubscribed

        return context


@require_http_methods(("GET",))
@username_required
def setup_email_notifications(request, uuid):
    """Setup email notifications for this event.

    Will send a short heads-up to given email address if something has
    changed on this event, e.g. a Game has been added or a new Vote.

    """
    event = Event.objects.get(uuid=uuid)
    return render(
        request, "core/event_setup_email_notifications.html", {"event": event}
    )


@require_http_methods(("POST",))
@username_required
def subscribe_to_email_notifications(request, uuid):
    event = Event.objects.get(uuid=uuid)
    email = request.POST["email"].strip()
    username = _get_username(request)

    subscription, created = EventSubscription.objects.get_or_create(
        event=event, email=email
    )
    if created and username:
        subscription.username = username
        subscription.save(update_fields=["username"])

    confirmation_url = request.build_absolute_uri(
        reverse("event-notifications-confirm", args=[subscription.uuid])
    )
    unsubscription_url = request.build_absolute_uri(
        reverse("event-notifications-unsubscribe", args=[subscription.uuid])
    )

    send_email_via_gmail(
        recipient=email,
        subject=f'[gamedoodle] Please confirm subscription for "{event.name}"',
        body=textwrap.dedent(
            f"""
            Please click this link to activate notifications: {confirmation_url}

            Unsubscribe from these notifications: {unsubscription_url}
        """
        ),
        html=textwrap.dedent(
            f"""
            Please click <a href="{confirmation_url}">this link to activate</a> notifications.

            <p>
              <small>
                If activated already, you can <a href="{unsubscription_url}">unsubscribe here</a>.
              </small>
            </p>
        """
        ),
    )

    return render(
        request,
        "core/event_setup_email_notifications.html",
        {"event": event, "email": email, "subscribed": True},
    )


@require_http_methods(("GET",))
def confirm_email_notifications(request, subscription_uuid):
    subscription = EventSubscription.objects.get(uuid=subscription_uuid)
    subscription.active = True
    subscription.save(update_fields=["active"])

    url = reverse("event-detail", args=[subscription.event.uuid]) + "?subscribed=true"
    return redirect(url)


@require_http_methods(("GET",))
def unsubscribe_email_notifications(request, subscription_uuid):
    subscription = EventSubscription.objects.get(uuid=subscription_uuid)
    subscription.active = False
    subscription.save(update_fields=["active"])

    url = reverse("event-detail", args=[subscription.event.uuid]) + "?unsubscribed=true"
    return redirect(url)


@require_http_methods(("POST",))
@username_required
def vote_game(request, uuid):
    """Handle both voting and unvoting for a Game."""
    event = Event.objects.get(uuid=uuid)
    _raise_if_event_not_writable(event)

    username = _get_username(request)

    vote_id = request.POST.get("vote_id")
    if vote_id:
        vote = Vote.objects.get(id=vote_id)
        if vote.username == username:
            vote.delete()

    superlike_vote_id = request.POST.get("superlike_vote_id")
    if superlike_vote_id:
        vote = Vote.objects.get(id=superlike_vote_id)
        if vote.username == username:
            vote.is_superlike = False
            vote.save()

    game_id = request.POST.get("game_id")
    if game_id:
        Vote.objects.get_or_create(event=event, game_id=game_id, username=username)

    superlike_game_id = request.POST.get("superlike_game_id")
    if superlike_game_id:
        vote = Vote.objects.get(
            event=event, game_id=superlike_game_id, username=username
        )
        vote.is_superlike = True
        vote.save()

    return redirect(reverse("event-detail", kwargs={"uuid": uuid}))


@require_http_methods(("GET",))
@username_required
def add_game(request, uuid):
    """Display form to add a Game to an Event.

    This just shows a form and maybe some search results: Nothing is
    added here yet, there is another step to confirm.

    """
    event = Event.objects.get(uuid=uuid)

    search_text = request.GET.get("q", "").strip()
    matching_games = []
    if search_text:
        matching_games = Game.objects.filter(name__icontains=search_text).order_by(
            "name"
        )[:100]

    return render(
        request,
        "core/event_add_game.html",
        {"event": event, "matching_games": matching_games, "search_text": search_text},
    )


@require_http_methods(("POST",))
@username_required
def add_game_manually(request, uuid):
    """Add actual game as specified."""
    event = Event.objects.get(uuid=uuid)
    _raise_if_event_not_writable(event)

    name = request.POST["name"].strip()
    image_url = request.POST.get("image_url", "")
    store_url = request.POST.get("store_url", "")
    is_free = request.POST.get("is_free", None) == "on"

    # Ensure Game exists.
    game, _ = Game.objects.get_or_create(name=name)
    game.is_free = is_free
    if game.image_url != image_url and image_url.strip() != "":
        game.image_url = image_url
    if game.store_url != store_url and store_url.strip() != "":
        game.store_url = store_url
    game.save()

    event.games.add(game)
    return redirect(reverse("event-detail", kwargs={"uuid": uuid}))


@require_http_methods(("POST",))
@username_required
def add_matching_game(request, uuid):
    """Add actual game selected from Steam search results or an existing one."""
    event = Event.objects.get(uuid=uuid)
    _raise_if_event_not_writable(event)

    game_id = request.POST["game_id"]
    game = Game.objects.get(id=game_id)

    is_steam_game = game.appid is not None
    if is_steam_game:
        steam_appid_str = str(game.appid)
        if not game.store_url:
            game.store_url = settings.STEAM_STORE_PAGE_BASE_URL + steam_appid_str
            game.save()

        # Fetch to set/update details.
        url = settings.STEAM_API_BASE_URL_APPDETAILS + steam_appid_str
        response = requests.get(url)
        data = response.json()[steam_appid_str]["data"]

        screenshots = data.get("screenshots", [])
        if game.image_url == "" and screenshots:
            first_thumbnail = screenshots[0]["path_thumbnail"]
            game.image_url = first_thumbnail

        game.is_free = data["is_free"]
        game.save()

    event.games.add(game)
    return redirect(reverse("event-detail", kwargs={"uuid": uuid}))

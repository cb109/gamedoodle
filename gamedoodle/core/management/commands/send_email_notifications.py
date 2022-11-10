from datetime import datetime, timedelta
import json
import textwrap

from django.contrib.contenttypes.models import ContentType
from django.contrib.sites.models import Site
from django.core.management.base import BaseCommand
from django.urls import reverse

from easyaudit.models import CRUDEvent

from gamedoodle.core.models import EventSubscription, Event, Game, Comment
from gamedoodle.core.mailing import send_email_via_gmail

event_content_type_id = ContentType.objects.get(app_label="core", model="event").id
vote_content_type_id = ContentType.objects.get(app_label="core", model="vote").id


class Command(BaseCommand):
    def handle(self, *args, **options):
        recently = datetime.now() - timedelta(days=1)
        site = Site.objects.get_current()

        for subscription in EventSubscription.objects.filter(
            active=True,
            event__read_only=False,
        ):
            recent_changes_detected = False

            # These are not yet filtered for the subscribed Event.
            event_descriptions = []

            recent_crud_events = CRUDEvent.objects.filter(
                datetime__gte=recently,
                content_type_id__in=[
                    event_content_type_id,
                    vote_content_type_id,
                ],
            ).order_by("datetime")
            for crud_event in recent_crud_events:
                is_event_crud_event = (
                    crud_event.content_type_id == event_content_type_id
                )
                is_vote_crud_event = crud_event.content_type_id == vote_content_type_id

                if is_event_crud_event:
                    event_id = json.loads(crud_event.object_json_repr)[0]["pk"]
                    event = Event.objects.get(id=event_id)
                elif is_vote_crud_event:
                    fields = json.loads(crud_event.object_json_repr)[0]["fields"]

                    event_id = fields["event"]
                    event = Event.objects.get(id=event_id)

                    vote_game = Game.objects.get(id=fields["game"])
                    vote_username = fields["username"]
                    vote_is_superlike = fields["is_superlike"]

                    if crud_event.is_create() or crud_event.is_update():
                        event_descriptions.append(
                            f"{vote_username} voted for {vote_game.name}"
                            + (" (superliked)" if vote_is_superlike else "")
                        )
                    elif crud_event.is_delete():
                        event_descriptions.append(
                            f"{vote_username} removed his vote for {vote_game.name}"
                        )

                if event == subscription.event:
                    recent_changes_detected = True

            recent_comments = (
                Comment.objects.filter(created_at__gte=recently)
                .exclude(softdeleted=True)
                .order_by("created_at")
            )
            if recent_comments.exists():
                recent_changes_detected = True
            for comment in recent_comments:
                event_descriptions.append(
                    f"{comment.username} commented on {comment.game.name}: "
                    f"{comment.short_preview}"
                )

            if recent_changes_detected:
                event_url = site.domain + reverse(
                    "event-detail", args=[subscription.event.uuid]
                )
                unsubscription_url = site.domain + reverse(
                    "event-notifications-unsubscribe", args=[subscription.uuid]
                )

                condensed_event_descriptions = []
                for event_description in event_descriptions:
                    if event_description in condensed_event_descriptions:
                        continue
                    condensed_event_descriptions.append(event_description)

                event_descriptions_text = ""
                event_descriptions_html = "<ul>"
                for event_description in condensed_event_descriptions:
                    event_descriptions_text += f"- {event_description}"
                    event_descriptions_html += f"<li>{event_description}</li>"
                event_descriptions_html += "</ul>"

                send_email_via_gmail(
                    recipient=subscription.email,
                    subject=(
                        f'[gamedoodle] "{event.name}" has '
                        f"seen some recent activity, check it out"
                    ),
                    body=textwrap.dedent(
                        f"""
                        Here are a few of the things that happened:

                        {event_descriptions_text}

                        Go to event: {event_url}

                        Unsubscribe from these notifications: {unsubscription_url}
                    """
                    ),
                    html=textwrap.dedent(
                        f"""
                        Here are a few of the things that happened:

                        {event_descriptions_html}

                        <a href="{event_url}"><h3>Go to event</h3></a>

                        <p>
                           <small>
                             <a href="{unsubscription_url}">Unsubscribe from these notifications</a>.
                           </small>
                        </p>
                    """
                    ),
                )

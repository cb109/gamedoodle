from datetime import datetime, timedelta
import json
import textwrap

from django.contrib.contenttypes.models import ContentType
from django.contrib.sites.models import Site
from django.core.management.base import BaseCommand
from django.urls import reverse

from easyaudit.models import CRUDEvent

from gamedoodle.core.models import EventSubscription, Event, Vote
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
            recent_crud_events = CRUDEvent.objects.filter(
                datetime__gte=recently,
                content_type_id__in=[
                    event_content_type_id,
                    vote_content_type_id,
                ],
            )
            for crud_event in recent_crud_events:
                is_event_crud_event = (
                    crud_event.content_type_id == event_content_type_id
                )
                is_vote_crud_event = crud_event.content_type_id == vote_content_type_id

                if is_event_crud_event:
                    event_id = json.loads(crud_event.object_json_repr)[0]["pk"]
                    event = Event.objects.get(id=event_id)
                elif is_vote_crud_event:
                    event_id = json.loads(crud_event.object_json_repr)[0]["fields"][
                        "event"
                    ]
                    event = Event.objects.get(id=event_id)

                if event == subscription.event:
                    recent_changes_detected = True
                    break

            if recent_changes_detected:
                event_url = site.domain + reverse("event-detail", args=[event.uuid])
                unsubscription_url = site.domain + reverse(
                    "event-notifications-unsubscribe", args=[subscription.id]
                )

                send_email_via_gmail(
                    recipient=subscription.email,
                    subject=(
                        f'[gamedoodle] "{event.name}" has '
                        f"seen some recent activity, check it out"
                    ),
                    body=textwrap.dedent(
                        f"""
                        Go to event: {event_url}

                        Unsubscribe from these notifications: {unsubscription_url}

                    """
                    ),
                )

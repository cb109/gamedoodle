from django.shortcuts import render
from django.views import generic

from gamedoodle.core.models import Event


class EventListView(generic.ListView):
    model = Event
    ordering = ("-date",)


class EventDetailView(generic.DetailView):
    model = Event
    slug_url_kwarg = "uuid"
    slug_field = "uuid"

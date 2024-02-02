from django.urls import path
from .views import jira_view

urlpatterns = [
    path('', jira_view, name='jira'),
]
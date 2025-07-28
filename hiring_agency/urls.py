from django.urls import path
from .views import add_user, list_users

urlpatterns = [
    path('add_user/', add_user, name='add_user'),
    path('list_users/', list_users, name='list_users'),
]

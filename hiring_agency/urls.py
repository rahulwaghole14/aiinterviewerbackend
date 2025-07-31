from django.urls import path
from .views import CreateUserDataView

urlpatterns = [
    path('add_user/', CreateUserDataView.as_view(), name='add_user'),
]

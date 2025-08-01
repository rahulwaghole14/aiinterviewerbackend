from django.urls import path
from .views import CreateUserDataView
from rest_framework.routers import DefaultRouter
from .views import UserDataViewSet

router = DefaultRouter()
router.register(r'hiring_agency', UserDataViewSet, basename='hiring_agency')

urlpatterns = [
    path('add_user/', CreateUserDataView.as_view(), name='add_user'),
]
urlpatterns += router.urls

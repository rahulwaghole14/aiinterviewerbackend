from django.urls import path
from .views import CreateUserDataView, UserDataViewSet
from rest_framework.routers import DefaultRouter

router = DefaultRouter()
router.register(r'', UserDataViewSet, basename='hiring_agency')

urlpatterns = [
    path('add_user/', CreateUserDataView.as_view(), name='add_user'),
]
urlpatterns += router.urls

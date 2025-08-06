from django.urls import path
from .views import CreateUserDataView, UserDataViewSet
from rest_framework.routers import DefaultRouter

router = DefaultRouter()
router.register(r'hiring_agency', UserDataViewSet, basename='hiring_agency')

urlpatterns = [
    path('add_user/', CreateUserDataView.as_view(), name='add_user'),
    path('', UserDataViewSet.as_view({'get': 'list'}), name='hiring-agency-list'),  # Add this line for root list
]
urlpatterns += router.urls

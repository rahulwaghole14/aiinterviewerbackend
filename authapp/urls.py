from django.urls import path
from .views import LogoutView
from .views import CustomLoginView



from .views import (
    RegisterView,
    ProfileView,
    CreateUserByRoleView,
    AdminLoginView,
    CompanyLoginView,
    RecruiterLoginView,
)

urlpatterns = [
    path('register/', RegisterView.as_view(), name='register'),
    path('profile/', ProfileView.as_view(), name='profile'),
    path('register-user/', CreateUserByRoleView.as_view(), name='register-user'),
    # path('admin/login/', AdminLoginView.as_view(), name='admin-login'),
    # path('company/login/', CompanyLoginView.as_view(), name='company-login'),
    # path('recruiter/login/', RecruiterLoginView.as_view(), name='recruiter-login'),
    path('login/', CustomLoginView.as_view(), name='custom-login'),
    path('logout/', LogoutView.as_view(), name='logout'),

]



from django.urls import path
from rest_framework_simplejwt.views import TokenRefreshView
from .views import StaffLoginView, StaffLogoutView, StaffMeView

urlpatterns = [
    path('token/', StaffLoginView.as_view(), name='token_obtain_pair'),
    path('token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
    path('logout/', StaffLogoutView.as_view(), name='auth_logout'),
    path('me/', StaffMeView.as_view(), name='auth_me'),
]

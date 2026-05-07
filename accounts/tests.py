from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse
from rest_framework.test import APIClient
from rest_framework_simplejwt.token_blacklist.models import BlacklistedToken
from rest_framework_simplejwt.tokens import RefreshToken


class StaffAuthTests(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.user_model = get_user_model()
        self.staff_user = self.user_model.objects.create_user(
            username='staff-user',
            password='StrongPass123!',
            is_staff=True,
        )

    def test_staff_login_rejects_non_staff_user(self):
        self.user_model.objects.create_user(
            username='student-user',
            password='StrongPass123!',
            is_staff=False,
        )

        response = self.client.post(
            reverse('token_obtain_pair'),
            {'username': 'student-user', 'password': 'StrongPass123!'},
            format='json',
        )

        assert response.status_code == 403, response.json()
        assert response.json()['detail'] == 'Staff access only.'
        assert 'access' not in response.json()

    def test_staff_logout_blacklists_refresh_token(self):
        refresh_token = RefreshToken.for_user(self.staff_user)
        self.client.force_authenticate(user=self.staff_user)

        response = self.client.post(
            reverse('auth_logout'),
            {'refresh': str(refresh_token)},
            format='json',
        )

        assert response.status_code == 200, response.json()
        assert response.json()['detail'] == 'Logged out.'
        assert BlacklistedToken.objects.filter(token__jti=refresh_token['jti']).exists()

    def test_staff_logout_requires_refresh_token(self):
        self.client.force_authenticate(user=self.staff_user)

        response = self.client.post(reverse('auth_logout'), {}, format='json')

        assert response.status_code == 400, response.json()
        assert response.json()['detail'] == 'Refresh token is required.'

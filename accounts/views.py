from django.contrib.auth import authenticate
from rest_framework import status
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework_simplejwt.exceptions import TokenError
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework_simplejwt.views import TokenObtainPairView


class StaffLoginView(TokenObtainPairView):
    """JWT login restricted to staff users."""
    permission_classes = [AllowAny]

    def post(self, request, *args, **kwargs):
        user = authenticate(
            request=request,
            username=request.data.get('username'),
            password=request.data.get('password'),
        )
        if user and not user.is_staff:
            return Response(
                {'detail': 'Staff access only.'},
                status=status.HTTP_403_FORBIDDEN,
            )
        return super().post(request, *args, **kwargs)


class StaffLogoutView(APIView):
    """Blacklist a valid refresh token during logout."""
    permission_classes = [IsAuthenticated]

    def post(self, request):
        refresh_token = request.data.get('refresh')
        if not refresh_token:
            return Response(
                {'detail': 'Refresh token is required.'},
                status=status.HTTP_400_BAD_REQUEST,
            )

        try:
            token = RefreshToken(refresh_token)
            token.blacklist()
        except TokenError:
            return Response(
                {'detail': 'Invalid refresh token.'},
                status=status.HTTP_400_BAD_REQUEST,
            )

        return Response({'detail': 'Logged out.'}, status=status.HTTP_200_OK)


class StaffMeView(APIView):
    """Return the authenticated user's basic info."""
    permission_classes = [IsAuthenticated]

    def get(self, request):
        user = request.user
        return Response({
            'id': user.id,
            'username': user.username,
            'email': user.email,
            'first_name': user.first_name,
            'last_name': user.last_name,
            'is_staff': user.is_staff,
            'is_superuser': user.is_superuser,
        })

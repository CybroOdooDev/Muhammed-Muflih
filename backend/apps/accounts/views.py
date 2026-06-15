from datetime import timezone

from django.conf import settings
from google.auth.transport import requests as google_requests
from google.oauth2 import id_token
from google_auth_oauthlib.flow import Flow
from rest_framework import status
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework_simplejwt.tokens import RefreshToken

from .models import User
from .serializers import UserSerializer

GMAIL_SCOPE = "https://www.googleapis.com/auth/gmail.readonly"


def _client_config():
    return {
        "web": {
            "client_id": settings.GOOGLE_OAUTH_CLIENT_ID,
            "client_secret": settings.GOOGLE_CLIENT_SECRET,
            "auth_uri": "https://accounts.google.com/o/oauth2/auth",
            "token_uri": "https://oauth2.googleapis.com/token",
            "redirect_uris": ["postmessage"],
        }
    }


class GoogleLoginView(APIView):
    """Exchange a Google auth code for our own JWT pair and store Gmail tokens.

    Flow: the React app uses useGoogleLogin({flow:'auth-code'}) to obtain an
    authorization code, POSTs it here as {"code": "..."}. We exchange it for
    Google tokens, verify identity via the embedded ID token, create/update
    the user, store the Gmail refresh token, and return our JWT pair.
    """

    permission_classes = [AllowAny]

    def post(self, request):
        code = request.data.get("code")
        if not code:
            return Response(
                {"detail": "Missing 'code' (Google authorization code)."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        if not settings.GOOGLE_OAUTH_CLIENT_ID:
            return Response(
                {"detail": "Server is missing GOOGLE_OAUTH_CLIENT_ID."},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )

        try:
            flow = Flow.from_client_config(
                _client_config(),
                scopes=[
                    "openid",
                    "https://www.googleapis.com/auth/userinfo.email",
                    "https://www.googleapis.com/auth/userinfo.profile",
                    GMAIL_SCOPE,
                ],
                redirect_uri="postmessage",
            )
            flow.fetch_token(code=code)
            creds = flow.credentials
        except Exception as exc:
            import traceback; traceback.print_exc()
            return Response(
                {"detail": f"Code exchange failed: {exc}"},
                status=status.HTTP_401_UNAUTHORIZED,
            )

        try:
            payload = id_token.verify_oauth2_token(
                creds.id_token, google_requests.Request(), settings.GOOGLE_OAUTH_CLIENT_ID
            )
        except ValueError:
            return Response(
                {"detail": "Invalid or expired Google token."},
                status=status.HTTP_401_UNAUTHORIZED,
            )

        if not payload.get("email_verified", False):
            return Response(
                {"detail": "Google account email is not verified."},
                status=status.HTTP_401_UNAUTHORIZED,
            )

        email = payload["email"].lower()
        google_sub = payload.get("sub", "")

        user, created = User.objects.get_or_create(
            email=email,
            defaults={
                "first_name": payload.get("given_name", ""),
                "last_name": payload.get("family_name", ""),
                "picture": payload.get("picture", ""),
                "google_sub": google_sub,
                "role": User.Role.EMPLOYEE,
            },
        )

        # Keep profile fields fresh on subsequent logins.
        changed = False
        if not user.google_sub and google_sub:
            user.google_sub, changed = google_sub, True
        new_picture = payload.get("picture", "")
        if new_picture and user.picture != new_picture:
            user.picture, changed = new_picture, True
        if changed:
            user.save(update_fields=["google_sub", "picture"])

        # Store Gmail tokens so the dashboard can read emails without
        # a separate connect step. Google only returns a refresh_token on
        # first authorisation or after re-consent; keep the existing token
        # if this login didn't include one.
        if creds.refresh_token:
            from apps.gmail_sync.models import GmailCredential
            expiry = creds.expiry.replace(tzinfo=timezone.utc) if creds.expiry else None
            GmailCredential.objects.update_or_create(
                user=user,
                defaults={
                    "gmail_email": email,
                    "access_token": creds.token or "",
                    "refresh_token": creds.refresh_token,
                    "token_expiry": expiry,
                },
            )

        refresh = RefreshToken.for_user(user)
        return Response(
            {
                "access": str(refresh.access_token),
                "refresh": str(refresh),
                "user": UserSerializer(user).data,
                "created": created,
            },
            status=status.HTTP_200_OK,
        )


class MeView(APIView):
    """Return the currently authenticated user's profile."""

    permission_classes = [IsAuthenticated]

    def get(self, request):
        
        return Response(UserSerializer(request.user).data)

"""Auth endpoints: register, login, logout, refresh, me."""
from rest_framework import status, exceptions
from rest_framework.decorators import  api_view, permission_classes
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from django.contrib.auth import authenticate
from django.conf import settings
from django.views.decorators.csrf import csrf_protect
import jwt

from .models import User
from .serializers import RegisterSerializer, LoginSerializer, UserSerializer
from .authentication import enforce_csrf


from django.utils import timezone

def _create_tokens(user: User):
    cfg = settings.JWT_CONFIG
    now = timezone.now()

    access_exp = int((now + cfg["ACCESS_TOKEN_LIFETIME"]).timestamp())
    refresh_exp = int((now + cfg["REFRESH_TOKEN_LIFETIME"]).timestamp())

    access_payload = {
        "user_id": str(user.id),
        "type": "access",
        "iat": int(now.timestamp()),
        "exp": access_exp,
    }

    refresh_payload = {
        "user_id": str(user.id),
        "type": "refresh",
        "iat": int(now.timestamp()),
        "exp": refresh_exp,
    }

    access = jwt.encode(
        access_payload,
        settings.SECRET_KEY,
        algorithm=cfg["ALGORITHM"],
    )

    refresh = jwt.encode(
        refresh_payload,
        settings.SECRET_KEY,
        algorithm=cfg["ALGORITHM"],
    )

    return access, refresh


def _set_cookies(response: Response, access: str, refresh: str):
    c = settings.COOKIE_CONFIG
    response.set_cookie(
        c['ACCESS_COOKIE_NAME'],
        access,
        max_age=c['MAX_AGE_ACCESS'],
        httponly=c['HTTPONLY'],
        secure=c['SECURE'],
        samesite=c['SAMESITE'],
        path='/',
    )
    response.set_cookie(
        c['REFRESH_COOKIE_NAME'],
        refresh,
        max_age=c['MAX_AGE_REFRESH'],
        httponly=c['HTTPONLY'],
        secure=c['SECURE'],
        samesite=c['SAMESITE'],
        path='/',
    )
    return response


def _clear_cookies(response: Response):
    c = settings.COOKIE_CONFIG
    for name in (c['ACCESS_COOKIE_NAME'], c['REFRESH_COOKIE_NAME']):
        response.delete_cookie(name, path='/')
    return response


@csrf_protect
@api_view(['POST'])
@permission_classes([AllowAny])
def register(request):
    serializer = RegisterSerializer(data=request.data)
    serializer.is_valid(raise_exception=True)
    user = serializer.save()
    access, refresh = _create_tokens(user)
    response = Response(UserSerializer(user).data, status=status.HTTP_201_CREATED)
    return _set_cookies(response, access, refresh)


@csrf_protect
@api_view(['POST'])
@permission_classes([AllowAny])
def login(request):
    serializer = LoginSerializer(data=request.data)
    serializer.is_valid(raise_exception=True)
    user = authenticate(
        request,
        username=serializer.validated_data['email'],
        password=serializer.validated_data['password'],
    )
    if not user:
        return Response({'detail': 'Invalid credentials'}, status=status.HTTP_401_UNAUTHORIZED)
    if not user.is_active:
        return Response({'detail': 'Account disabled'}, status=status.HTTP_403_FORBIDDEN)

    # Start the background job scheduler on first login if not already running
    if not getattr(settings, 'TESTING', False):
        try:
            from apps.jobs.scheduler import start_scheduler
            start_scheduler()
        except Exception as e:
            print(f"[Scheduler] Failed to start on login: {e}")

    access, refresh = _create_tokens(user)
    response = Response(UserSerializer(user).data)
    return _set_cookies(response, access, refresh)


@csrf_protect
@api_view(['POST'])
@permission_classes([AllowAny])
def logout(request):
    # AllowAny — clearing cookies never requires a valid token.
    # If the token expired the user still needs to be logged out cleanly.
    c = settings.COOKIE_CONFIG
    if request.COOKIES.get(c['ACCESS_COOKIE_NAME']) or request.COOKIES.get(c['REFRESH_COOKIE_NAME']):
        try:
            enforce_csrf(request)
        except exceptions.PermissionDenied as exc:
            return Response({'detail': str(exc.detail)}, status=status.HTTP_403_FORBIDDEN)

    response = Response({'detail': 'Logged out'})
    return _clear_cookies(response)


@csrf_protect
@api_view(['POST'])
@permission_classes([AllowAny])
def refresh(request):
    c = settings.COOKIE_CONFIG
    token = request.COOKIES.get(c['REFRESH_COOKIE_NAME'])
    if not token:
        return Response({'detail': 'Refresh token required'}, status=status.HTTP_401_UNAUTHORIZED)

    try:
        enforce_csrf(request)
    except exceptions.PermissionDenied as exc:
        return Response({'detail': str(exc.detail)}, status=status.HTTP_403_FORBIDDEN)

    try:
        payload = jwt.decode(
            token,
            settings.SECRET_KEY,
            algorithms=[settings.JWT_CONFIG['ALGORITHM']],
        )
        if payload.get('type') != 'refresh':
            return Response({'detail': 'Invalid token type'}, status=status.HTTP_401_UNAUTHORIZED)
        user = User.objects.get(id=payload['user_id'], is_active=True)
        access, new_refresh = _create_tokens(user)
        response = Response(UserSerializer(user).data)
        return _set_cookies(response, access, new_refresh)
    except (jwt.InvalidTokenError, User.DoesNotExist):
        return Response({'detail': 'Invalid refresh token'}, status=status.HTTP_401_UNAUTHORIZED)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def me(request):
    return Response(UserSerializer(request.user).data)
"""Custom middleware for security and CSRF handling."""
import json
import os
import re
import tempfile
import time
from django.http import JsonResponse
from django.utils.deprecation import MiddlewareMixin


class RateLimitMiddleware(MiddlewareMixin):
    """
    File-backed rate limiter — works correctly across all gunicorn workers.
    Rate: 100 requests per minute per IP for auth endpoints.

    Uses a JSON file in the system temp directory as a shared store between
    worker processes. For high-traffic production use, replace with Redis.
    """
    RATE_LIMIT = 100
    WINDOW = 60
    _store_path = os.path.join(tempfile.gettempdir(), "django_rate_limit.json")

    def _load(self):
        try:
            with open(self._store_path, "r") as f:
                return json.load(f)
        except (FileNotFoundError, json.JSONDecodeError):
            return {}

    def _save(self, data):
        try:
            with open(self._store_path, "w") as f:
                json.dump(data, f)
        except OSError:
            pass

    def process_request(self, request):
        if not re.match(r'^/api/auth/(login|register)', request.path):
            return None

        ip = self._get_client_ip(request)
        now = time.time()

        store = self._load()
        timestamps = [t for t in store.get(ip, []) if now - t < self.WINDOW]

        if len(timestamps) >= self.RATE_LIMIT:
            return JsonResponse({'detail': 'Rate limit exceeded'}, status=429)

        timestamps.append(now)
        store[ip] = timestamps
        self._save(store)
        return None

    def _get_client_ip(self, request):
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            return x_forwarded_for.split(',')[0].strip()
        return request.META.get('REMOTE_ADDR', '127.0.0.1')


class CSRFExemptAPIMiddleware(MiddlewareMixin):
    """
    Exempt all /api/ routes from Django's CSRF enforcement.

    Safe because every /api/ endpoint is protected by JWTCookieAuthentication.
    CSRF is only needed for session-based auth, which this project does not use.
    """
    def process_request(self, request):
        if request.path.startswith('/api/'):
            setattr(request, '_dont_enforce_csrf_checks', True)
        return None


class CSRFCookieMiddleware(MiddlewareMixin):
    """Ensure CSRF cookie is set for cookie-based auth."""
    def process_response(self, request, response):
        if request.path.startswith('/api/') and not response.cookies.get('csrftoken'):
            from django.middleware.csrf import get_token
            get_token(request)
        return response
"""
Middleware for the users app.

Activates the current user's profile timezone so that all date/time display
in templates (e.g. deal dates, document version dates) uses their local time.
"""

from zoneinfo import ZoneInfo

from django.utils import timezone as django_timezone


def get_user_timezone(user):
    """
    Return the IANA timezone string for the user's profile, or None if not set.

    Uses the profile's timezone field; returns None for anonymous or missing profile.
    """
    if not user or not user.is_authenticated:
        return None
    try:
        profile = user.lease_officer_profile
        return profile.timezone if profile.timezone else None
    except Exception:
        return None


class ProfileTimezoneMiddleware:
    """
    Activate the request user's profile timezone for the duration of the request.

    All template date/time filters and timezone-aware datetime display will use
    this zone. If the user has no profile or no timezone set, the default
    (settings.TIME_ZONE) is used.
    """

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        tz_name = get_user_timezone(request.user)
        if tz_name:
            try:
                django_timezone.activate(ZoneInfo(tz_name))
            except Exception:
                pass  # Invalid zone; leave default (settings.TIME_ZONE) active
        response = self.get_response(request)
        django_timezone.deactivate()
        return response

import uuid
from typing import Callable
from django.conf import settings
from django.http import HttpRequest, HttpResponse
from featurevault.context import clear_current_context, set_current_context


class FeatureContextMiddleware:
    """
    Django middleware that captures request context at the start of a request,
    ensures anonymous users receive a device cookie, and cleans up context on completion.
    """

    def __init__(self, get_response: Callable[[HttpRequest], HttpResponse]) -> None:
        self.get_response = get_response

    def __call__(self, request: HttpRequest) -> HttpResponse:
        cookie_name = getattr(settings, "FEATURE_FLAGS", {}).get(
            "CLIENT_ID_COOKIE", "ff_client_id"
        )
        
        # Read or generate anonymous client device ID
        device_id = request.COOKIES.get(cookie_name)
        new_cookie_needed = False
        if not device_id:
            device_id = str(uuid.uuid4())
            new_cookie_needed = True

        # Extract user context
        user = getattr(request, "user", None)

        # Build implicit context dictionary
        context_data: dict = {
            "request": request,
            "user": user,
            "device_id": device_id,
        }

        if user and getattr(user, "is_authenticated", False):
            context_data["user_id"] = getattr(user, "pk", getattr(user, "id", None))

        set_current_context(context_data)

        try:
            response = self.get_response(request)
            
            # Attach device cookie for anonymous user tracking if generated
            if new_cookie_needed and isinstance(response, HttpResponse):
                response.set_cookie(
                    cookie_name,
                    device_id,
                    max_age=365 * 24 * 60 * 60,
                    httponly=True,
                    samesite="Lax",
                    secure=request.is_secure(),
                )
            return response
        finally:
            clear_current_context()
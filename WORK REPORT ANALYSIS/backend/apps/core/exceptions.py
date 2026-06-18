import logging

from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import exception_handler

logger = logging.getLogger(__name__)


def custom_exception_handler(exc, context):
    """DRF exception handler that returns JSON for unhandled 500 errors."""
    response = exception_handler(exc, context)
    if response is not None:
        return response

    logger.exception("Unhandled exception in %s", context.get("view"))
    return Response(
        {"detail": "An unexpected server error occurred."},
        status=status.HTTP_500_INTERNAL_SERVER_ERROR,
    )

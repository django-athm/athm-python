"""Webhook utilities for ATH Movil.

This module provides the parse_webhook() function for validating and
normalizing incoming webhook payloads.

Ref: https://github.com/evertec/athmovil-webhooks
"""

from typing import Any

from athm.exceptions import ValidationError
from athm.models.webhooks import (
    WebhookEventType,
    WebhookItem,
    WebhookPayload,
    WebhookStatus,
    WebhookSubscriptionRequest,
)

# Re-export models for convenience
__all__ = [
    "WebhookEventType",
    "WebhookItem",
    "WebhookPayload",
    "WebhookStatus",
    "WebhookSubscriptionRequest",
    "parse_webhook",
]


def parse_webhook(payload: dict[str, Any]) -> WebhookPayload:
    """Parse and validate a webhook payload from ATH Movil.

    This function normalizes the various inconsistencies in the ATH Movil
    webhook API and returns a strongly-typed WebhookPayload object.

    Ref: https://github.com/evertec/athmovil-webhooks

    Args:
        payload: Raw JSON payload from webhook request body

    Returns:
        Validated and normalized WebhookPayload

    Raises:
        ValidationError: If payload is invalid or missing required fields

    Example:
        ```python
        from athm.webhooks import parse_webhook, WebhookEventType

        @app.post("/webhook")
        async def handle_webhook(request: Request):
            payload = await request.json()
            event = parse_webhook(payload)

            if event.transaction_type == WebhookEventType.PAYMENT:
                process_payment(event)
        ```
    """
    try:
        return WebhookPayload.model_validate(payload)
    except Exception as e:
        raise ValidationError(f"Invalid webhook payload: {e}") from e

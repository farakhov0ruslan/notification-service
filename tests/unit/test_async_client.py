from unittest.mock import AsyncMock
from unittest.mock import MagicMock

import pytest
from notification_registry import NotificationChannel
from notification_registry import NotificationPriority
from notification_registry import NotificationType

from notification_service.service.client.async_client import grpc_send_notification
from notification_service.service.client.dto import SendNotificationRequest
from tests.utils.factories import WEBHOOK_URL
from tests.utils.factories import WebhookAnalyticsPayloadFactory
from tests.utils.factories import WebhookResetPasswordPayloadFactory


def _mock_grpc_response(
    *, success=True, notification_id="test-id-123", status="pending", message="ok"
):
    resp = MagicMock()
    resp.success = success
    resp.notification_id = notification_id
    resp.status = status
    resp.message = message
    return resp


def _make_webhook_request(
    payload=None, notification_type=NotificationType.RESET_PASSWORD, priority=None
):
    p = payload or WebhookResetPasswordPayloadFactory.build()
    return SendNotificationRequest(
        notification_type=notification_type,
        channel=NotificationChannel.WEBHOOK,
        payload=p,
        recipient_address=WEBHOOK_URL,
        priority=priority,
    )


@pytest.fixture
def mock_grpc(mocker):
    mock = AsyncMock(return_value=_mock_grpc_response())
    mocker.patch(
        "notification_service.service.client.async_client.async_call_grpc", mock
    )
    return mock


def _grpc_kwargs(mock_grpc) -> dict:
    return (
        mock_grpc.call_args.kwargs["request"].__class__.__dict__
        or mock_grpc.call_args[0][2].__dict__
    )


def _pb2_request(mock_grpc):
    return mock_grpc.call_args[0][2]


class TestGrpcSendNotificationWebhook:
    @pytest.mark.asyncio
    async def test_recipient_address_forwarded_to_grpc(self, mock_grpc):
        await grpc_send_notification(_make_webhook_request())

        pb2_req = _pb2_request(mock_grpc)
        assert pb2_req.recipient_address == WEBHOOK_URL

    @pytest.mark.asyncio
    async def test_channel_is_webhook(self, mock_grpc):
        await grpc_send_notification(_make_webhook_request())

        pb2_req = _pb2_request(mock_grpc)
        assert pb2_req.channel == NotificationChannel.WEBHOOK.value

    @pytest.mark.asyncio
    async def test_notification_type_reset_password(self, mock_grpc):
        await grpc_send_notification(_make_webhook_request())

        pb2_req = _pb2_request(mock_grpc)
        assert pb2_req.notification_type == NotificationType.RESET_PASSWORD.value

    @pytest.mark.asyncio
    async def test_payload_json_is_serialized(self, mock_grpc):
        payload = WebhookResetPasswordPayloadFactory.build()
        await grpc_send_notification(_make_webhook_request(payload=payload))

        pb2_req = _pb2_request(mock_grpc)
        assert pb2_req.payload_json == payload.model_dump_json()

    @pytest.mark.asyncio
    async def test_priority_forwarded_when_set(self, mock_grpc):
        request = _make_webhook_request(priority=NotificationPriority.HIGH)

        await grpc_send_notification(request)

        pb2_req = _pb2_request(mock_grpc)
        assert pb2_req.priority == NotificationPriority.HIGH.value

    @pytest.mark.asyncio
    async def test_no_priority_field_when_not_set(self, mock_grpc):
        await grpc_send_notification(_make_webhook_request(priority=None))

        pb2_req = _pb2_request(mock_grpc)
        assert not hasattr(pb2_req, "priority") or pb2_req.priority == ""

    @pytest.mark.asyncio
    async def test_returns_send_notification_result_on_success(self, mock_grpc):
        nid = "abc-123"
        mock_grpc.return_value = _mock_grpc_response(
            success=True, notification_id=nid, status="pending"
        )

        result = await grpc_send_notification(_make_webhook_request())

        assert result.success is True
        assert result.notification_id == nid
        assert result.status == "pending"

    @pytest.mark.asyncio
    async def test_returns_failure_result_on_grpc_error(self, mock_grpc):
        mock_grpc.return_value = _mock_grpc_response(
            success=False, notification_id="", status="", message="invalid payload"
        )

        result = await grpc_send_notification(_make_webhook_request())

        assert result.success is False
        assert "invalid payload" in result.message

    @pytest.mark.asyncio
    async def test_analytics_payload_webhook(self, mock_grpc):
        payload = WebhookAnalyticsPayloadFactory.build()
        request = SendNotificationRequest(
            notification_type=NotificationType.ANALYTICS,
            channel=NotificationChannel.WEBHOOK,
            payload=payload,
            recipient_address=WEBHOOK_URL,
        )

        await grpc_send_notification(request)

        pb2_req = _pb2_request(mock_grpc)
        assert pb2_req.channel == NotificationChannel.WEBHOOK.value
        assert pb2_req.notification_type == NotificationType.ANALYTICS.value
        assert pb2_req.recipient_address == WEBHOOK_URL

    @pytest.mark.asyncio
    async def test_recipient_address_none_not_forwarded(self, mock_grpc):
        payload = WebhookResetPasswordPayloadFactory.build()
        request = SendNotificationRequest(
            notification_type=NotificationType.RESET_PASSWORD,
            channel=NotificationChannel.WEBHOOK,
            payload=payload,
            recipient_address=None,
        )

        await grpc_send_notification(request)

        pb2_req = _pb2_request(mock_grpc)
        assert (
            not hasattr(pb2_req, "recipient_address") or pb2_req.recipient_address == ""
        )

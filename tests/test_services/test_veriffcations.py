import pytest
from unittest.mock import MagicMock, AsyncMock, patch

from app.services.verifications import send_email_code, send_sms_code


@pytest.fixture
def mock_smtp():
    with patch("smtplib.SMTP_SSL") as mock_smtp:
        mock_server = AsyncMock()
        mock_smtp.return_value.__enter__.return_value = mock_server
        yield mock_server


@pytest.mark.asyncio
async def test_email_content_generation(mock_smtp):
    await send_email_code("user@domain.com", "ABCD")

    email_content = mock_smtp.send_message.call_args[0][0]
    assert email_content.get("Subject") == "Код подтверждения бронирования"
    assert email_content.get("To") == "user@domain.com"
    assert "Ваш код подтверждения: ABCD" in email_content.get_payload()


@pytest.mark.parametrize("phone, code", [
    ("+79001234567", "1234"),
    ("+79998765432", "ZYXW"),
    ("+77777777777", "1A2B3C")
])
@pytest.mark.asyncio
async def test_different_formats(phone, code):
    with patch("app.lib.notisend.SMS") as mock_sms:
        mock_sms.return_value.sendSMS.return_value = MagicMock(sid="test")
        await send_sms_code(phone, code)
        mock_sms.return_value.sendSMS.assert_called_with(
            recipients=phone,
            message=f"Ваш код подтверждения: {code}"
        )
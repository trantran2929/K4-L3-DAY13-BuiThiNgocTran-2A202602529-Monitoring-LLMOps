from app.pii import scrub_text
import pytest


def test_scrub_email() -> None:
    out = scrub_text("Email me at student@vinuni.edu.vn")
    assert "student@" not in out
    assert "REDACTED_EMAIL" in out


def test_scrub_common_vietnamese_phone_formats() -> None:
    phone_numbers = (
        "0901234567",
        "090 123 4567",
        "090.123.4567",
        "090-123-4567",
        "+84 90 123 4567",
    )

    for phone_number in phone_numbers:
        out = scrub_text(f"Contact: {phone_number}")
        assert phone_number not in out
        assert "REDACTED_PHONE_VN" in out

@pytest.mark.parametrize(
    ("raw", "expected"),
    [
        ("student+lab@example.com", "[REDACTED_EMAIL]"),
        ("0901234567", "[REDACTED_PHONE_VN]"),
        ("090 123 4567", "[REDACTED_PHONE_VN]"),
        ("090.123.4567", "[REDACTED_PHONE_VN]"),
        ("090-123-4567", "[REDACTED_PHONE_VN]"),
        ("+84 90 123 4567", "[REDACTED_PHONE_VN]"),
        ("0084 90 123 4567", "[REDACTED_PHONE_VN]"),
        ("012345678901", "[REDACTED_CCCD]"),
        ("4111111111111111", "[REDACTED_CREDIT_CARD]"),
        ("4111 1111 1111 1111", "[REDACTED_CREDIT_CARD]"),
        ("4111-1111-1111-1111", "[REDACTED_CREDIT_CARD]"),
    ],
)
def test_scrub_pii_variants(raw: str, expected: str) -> None:
    assert scrub_text(f"Contact: {raw}") == f"Contact: {expected}"


def test_non_pii_unchanged() -> None:
    text = "Monitoring request req-ab12cd34"
    assert scrub_text(text) == text


def test_scrub_nested_log_payload() -> None:
    from app.logging_config import scrub_event

    event = {
        "event": "request_received",
        "payload": {
            "contacts": [
                {"email": "student+lab@example.com"}
            ]
        },
        "exception": "Contact 0901234567",
    }

    result = scrub_event(None, "info", event)

    assert result["payload"]["contacts"][0]["email"] == (
        "[REDACTED_EMAIL]"
    )
    assert result["exception"] == "Contact [REDACTED_PHONE_VN]"

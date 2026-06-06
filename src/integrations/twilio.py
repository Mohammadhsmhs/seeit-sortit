"""Twilio integration — outbound call stub."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Optional

import requests

from src.config import TWILIO_ACCOUNT_SID, TWILIO_AUTH_TOKEN, TWILIO_FROM_NUMBER


@dataclass
class CallResult:
    """Shape of a Twilio Calls API response."""
    sid: str = ""
    status: str = ""
    from_number: str = ""
    to_number: str = ""
    direction: str = "outbound-api"


class TwilioClient:
    """Client for Twilio outbound calls.

    Endpoint: POST https://api.twilio.com/2010-04-01/Accounts/{sid}/Calls.json
    Auth: HTTP Basic (account_sid : auth_token)
    Body (form-encoded): To, From, Url (TwiML), StatusCallback
    """

    def __init__(
        self,
        account_sid: str = TWILIO_ACCOUNT_SID,
        auth_token: str = TWILIO_AUTH_TOKEN,
        from_number: str = TWILIO_FROM_NUMBER,
        stub: bool = True,
    ) -> None:
        self.account_sid = account_sid
        self.auth_token = auth_token
        self.from_number = from_number
        self.stub = stub or not account_sid

    def make_call(
        self,
        to_number: str,
        twiml_url: str = "",
        status_callback: str = "",
    ) -> CallResult:
        """Place an outbound call.

        Endpoint: POST /2010-04-01/Accounts/{sid}/Calls.json
        Body: To, From, Url, StatusCallback
        """
        if self.stub:
            return CallResult(
                sid="CA_stub_00000000000000000000000000000001",
                status="queued",
                from_number=self.from_number or "+441234567890",
                to_number=to_number,
            )

        url = f"https://api.twilio.com/2010-04-01/Accounts/{self.account_sid}/Calls.json"
        data = {
            "To": to_number,
            "From": self.from_number,
            "Url": twiml_url,
        }
        if status_callback:
            data["StatusCallback"] = status_callback

        resp = requests.post(
            url,
            data=data,
            auth=(self.account_sid, self.auth_token),
            timeout=30,
        )
        resp.raise_for_status()
        body = resp.json()
        return CallResult(
            sid=body.get("sid", ""),
            status=body.get("status", ""),
            from_number=body.get("from", self.from_number),
            to_number=body.get("to", to_number),
            direction=body.get("direction", "outbound-api"),
        )

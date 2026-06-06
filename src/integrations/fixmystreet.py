"""FixMyStreet /import API client — stub mode returns mock responses."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional

import requests

from src.config import FIXMYSTREET_API_KEY, FIXMYSTREET_API_URL
from src.models.base import CivicIssue


@dataclass
class SubmissionResult:
    """Shape of a FixMyStreet import response."""
    success: bool
    report_url: str = ""
    report_id: str = ""
    message: str = ""
    errors: list[str] = field(default_factory=list)
    submitted_at: str = ""


class FixMyStreetClient:
    """Client for the FixMyStreet /import endpoint.

    See: https://www.fixmystreet.com/import
    The /import endpoint accepts multipart form data with these fields:
      - service: API key
      - subject: title
      - detail: description
      - lat / lon: coordinates
      - name / email: reporter info
      - photo: optional image upload
    """

    def __init__(
        self,
        api_url: str = FIXMYSTREET_API_URL,
        api_key: str = FIXMYSTREET_API_KEY,
        stub: bool = True,
    ) -> None:
        self.api_url = api_url
        self.api_key = api_key
        self.stub = stub or not api_key

    def submit_report(
        self,
        issue: CivicIssue,
        reporter_name: str = "London Civic Agent",
        reporter_email: str = "agent@londoncivic.example.com",
    ) -> SubmissionResult:
        """Submit a civic issue to FixMyStreet."""
        if self.stub:
            return self._stub_response(issue)
        return self._live_submit(issue, reporter_name, reporter_email)

    def _stub_response(self, issue: CivicIssue) -> SubmissionResult:
        """Return a realistic mock response."""
        return SubmissionResult(
            success=True,
            report_url=f"https://www.fixmystreet.com/report/{issue.id}",
            report_id=issue.id,
            message="Report submitted successfully (stub mode).",
            submitted_at=datetime.now().isoformat(),
        )

    def _live_submit(
        self,
        issue: CivicIssue,
        reporter_name: str,
        reporter_email: str,
    ) -> SubmissionResult:
        """POST to the real /import endpoint."""
        data = {
            "service": self.api_key,
            "subject": issue.title,
            "detail": issue.description,
            "lat": issue.latitude,
            "lon": issue.longitude,
            "name": reporter_name,
            "email": reporter_email,
        }

        files = None
        if issue.photos:
            # Attach the first photo
            try:
                files = {"photo": open(issue.photos[0], "rb")}
            except FileNotFoundError:
                pass

        try:
            resp = requests.post(self.api_url, data=data, files=files, timeout=30)
            if resp.ok:
                return SubmissionResult(
                    success=True,
                    report_url=resp.headers.get("Location", ""),
                    message=resp.text[:200],
                    submitted_at=datetime.now().isoformat(),
                )
            return SubmissionResult(
                success=False,
                message=f"HTTP {resp.status_code}",
                errors=[resp.text[:500]],
            )
        except requests.RequestException as e:
            return SubmissionResult(
                success=False,
                message="Request failed",
                errors=[str(e)],
            )
        finally:
            if files:
                for f in files.values():
                    f.close()

"""Sub-client for the Auto Apply endpoints (sessions and profiles)."""

from __future__ import annotations

from typing import List, Union
from uuid import UUID

import httpx

from jobo_enterprise.exceptions import _handle_error
from jobo_enterprise.models import (
    AutoApplyProfileRequest,
    AutoApplyProfileResponse,
    AutoApplySessionResponse,
    FieldAnswer,
    RunAutoApplyRequest,
    RunAutoApplyResponse,
    SetAutoApplyAnswersRequest,
    StartAutoApplySessionRequest,
)


class AutoApplyClient:
    """Synchronous sub-client for the Auto Apply endpoints.

    Access via ``client.auto_apply``.
    """

    def __init__(self, http: httpx.Client) -> None:
        self._client = http

    # ── Sessions ─────────────────────────────────────────────────────

    def start_session(self, apply_url: str) -> AutoApplySessionResponse:
        """Start a new auto-apply session for a job posting.

        Args:
            apply_url: The apply URL from the job listing.

        Returns:
            An :class:`AutoApplySessionResponse` with session details and form fields.
        """
        request = StartAutoApplySessionRequest(apply_url=apply_url)
        resp = self._client.post("/api/auto-apply/start", json=request.model_dump(mode="json"))
        if resp.status_code != 200:
            _handle_error(resp)
        return AutoApplySessionResponse.model_validate(resp.json())

    def set_answers(
        self,
        session_id: Union[UUID, str],
        answers: List[FieldAnswer],
    ) -> AutoApplySessionResponse:
        """Set answers for an active auto-apply session.

        Args:
            session_id: The session ID from :meth:`start_session`.
            answers: List of field answers.

        Returns:
            An :class:`AutoApplySessionResponse` with updated session state.
        """
        request = SetAutoApplyAnswersRequest(session_id=UUID(str(session_id)), answers=answers)
        resp = self._client.post("/api/auto-apply/set-answers", json=request.model_dump(mode="json"))
        if resp.status_code != 200:
            _handle_error(resp)
        return AutoApplySessionResponse.model_validate(resp.json())

    def run(
        self,
        profile_id: Union[UUID, str],
        apply_url: str,
    ) -> RunAutoApplyResponse:
        """Run the full auto-apply flow end-to-end against a stored profile.

        Args:
            profile_id: An existing auto-apply profile ID.
            apply_url: The apply URL from the job listing.

        Returns:
            A :class:`RunAutoApplyResponse` summarizing the run.
        """
        request = RunAutoApplyRequest(profile_id=UUID(str(profile_id)), apply_url=apply_url)
        resp = self._client.post("/api/auto-apply/run", json=request.model_dump(mode="json"))
        if resp.status_code != 200:
            _handle_error(resp)
        return RunAutoApplyResponse.model_validate(resp.json())

    def end_session(self, session_id: Union[UUID, str]) -> bool:
        """End an auto-apply session and release browser resources.

        Args:
            session_id: The session ID to end.

        Returns:
            True if the session was ended, False if it was not found.
        """
        resp = self._client.delete(f"/api/auto-apply/sessions/{session_id}")
        if resp.status_code == 200:
            return True
        if resp.status_code == 404:
            return False
        _handle_error(resp)
        return False

    # ── Profiles ─────────────────────────────────────────────────────

    def create_profile(self, profile: AutoApplyProfileRequest) -> AutoApplyProfileResponse:
        """Create a new applicant profile (POST /api/auto-apply/profiles)."""
        resp = self._client.post(
            "/api/auto-apply/profiles", json=profile.model_dump(mode="json", exclude_none=True)
        )
        if resp.status_code not in (200, 201):
            _handle_error(resp)
        return AutoApplyProfileResponse.model_validate(resp.json())

    def list_profiles(self) -> List[AutoApplyProfileResponse]:
        """List all profiles for the authenticated user (GET /api/auto-apply/profiles)."""
        resp = self._client.get("/api/auto-apply/profiles")
        if resp.status_code != 200:
            _handle_error(resp)
        return [AutoApplyProfileResponse.model_validate(item) for item in resp.json()]

    def get_profile(self, profile_id: Union[UUID, str]) -> AutoApplyProfileResponse:
        """Get a specific profile by ID (GET /api/auto-apply/profiles/{id})."""
        resp = self._client.get(f"/api/auto-apply/profiles/{profile_id}")
        if resp.status_code != 200:
            _handle_error(resp)
        return AutoApplyProfileResponse.model_validate(resp.json())

    def update_profile(
        self,
        profile_id: Union[UUID, str],
        profile: AutoApplyProfileRequest,
    ) -> AutoApplyProfileResponse:
        """Update an existing profile (PUT /api/auto-apply/profiles/{id})."""
        resp = self._client.put(
            f"/api/auto-apply/profiles/{profile_id}",
            json=profile.model_dump(mode="json", exclude_none=True),
        )
        if resp.status_code != 200:
            _handle_error(resp)
        return AutoApplyProfileResponse.model_validate(resp.json())

    def delete_profile(self, profile_id: Union[UUID, str]) -> bool:
        """Delete a profile (DELETE /api/auto-apply/profiles/{id})."""
        resp = self._client.delete(f"/api/auto-apply/profiles/{profile_id}")
        if resp.status_code == 200:
            return True
        if resp.status_code == 404:
            return False
        _handle_error(resp)
        return False


class AsyncAutoApplyClient:
    """Asynchronous sub-client for the Auto Apply endpoints.

    Access via ``client.auto_apply``.
    """

    def __init__(self, http: httpx.AsyncClient) -> None:
        self._client = http

    # ── Sessions ─────────────────────────────────────────────────────

    async def start_session(self, apply_url: str) -> AutoApplySessionResponse:
        """Start a new auto-apply session for a job posting."""
        request = StartAutoApplySessionRequest(apply_url=apply_url)
        resp = await self._client.post("/api/auto-apply/start", json=request.model_dump(mode="json"))
        if resp.status_code != 200:
            _handle_error(resp)
        return AutoApplySessionResponse.model_validate(resp.json())

    async def set_answers(
        self,
        session_id: Union[UUID, str],
        answers: List[FieldAnswer],
    ) -> AutoApplySessionResponse:
        """Set answers for an active auto-apply session."""
        request = SetAutoApplyAnswersRequest(session_id=UUID(str(session_id)), answers=answers)
        resp = await self._client.post("/api/auto-apply/set-answers", json=request.model_dump(mode="json"))
        if resp.status_code != 200:
            _handle_error(resp)
        return AutoApplySessionResponse.model_validate(resp.json())

    async def run(
        self,
        profile_id: Union[UUID, str],
        apply_url: str,
    ) -> RunAutoApplyResponse:
        """Run the full auto-apply flow end-to-end against a stored profile."""
        request = RunAutoApplyRequest(profile_id=UUID(str(profile_id)), apply_url=apply_url)
        resp = await self._client.post("/api/auto-apply/run", json=request.model_dump(mode="json"))
        if resp.status_code != 200:
            _handle_error(resp)
        return RunAutoApplyResponse.model_validate(resp.json())

    async def end_session(self, session_id: Union[UUID, str]) -> bool:
        """End an auto-apply session and release browser resources."""
        resp = await self._client.delete(f"/api/auto-apply/sessions/{session_id}")
        if resp.status_code == 200:
            return True
        if resp.status_code == 404:
            return False
        _handle_error(resp)
        return False

    # ── Profiles ─────────────────────────────────────────────────────

    async def create_profile(self, profile: AutoApplyProfileRequest) -> AutoApplyProfileResponse:
        """Create a new applicant profile (POST /api/auto-apply/profiles)."""
        resp = await self._client.post(
            "/api/auto-apply/profiles", json=profile.model_dump(mode="json", exclude_none=True)
        )
        if resp.status_code not in (200, 201):
            _handle_error(resp)
        return AutoApplyProfileResponse.model_validate(resp.json())

    async def list_profiles(self) -> List[AutoApplyProfileResponse]:
        """List all profiles for the authenticated user (GET /api/auto-apply/profiles)."""
        resp = await self._client.get("/api/auto-apply/profiles")
        if resp.status_code != 200:
            _handle_error(resp)
        return [AutoApplyProfileResponse.model_validate(item) for item in resp.json()]

    async def get_profile(self, profile_id: Union[UUID, str]) -> AutoApplyProfileResponse:
        """Get a specific profile by ID (GET /api/auto-apply/profiles/{id})."""
        resp = await self._client.get(f"/api/auto-apply/profiles/{profile_id}")
        if resp.status_code != 200:
            _handle_error(resp)
        return AutoApplyProfileResponse.model_validate(resp.json())

    async def update_profile(
        self,
        profile_id: Union[UUID, str],
        profile: AutoApplyProfileRequest,
    ) -> AutoApplyProfileResponse:
        """Update an existing profile (PUT /api/auto-apply/profiles/{id})."""
        resp = await self._client.put(
            f"/api/auto-apply/profiles/{profile_id}",
            json=profile.model_dump(mode="json", exclude_none=True),
        )
        if resp.status_code != 200:
            _handle_error(resp)
        return AutoApplyProfileResponse.model_validate(resp.json())

    async def delete_profile(self, profile_id: Union[UUID, str]) -> bool:
        """Delete a profile (DELETE /api/auto-apply/profiles/{id})."""
        resp = await self._client.delete(f"/api/auto-apply/profiles/{profile_id}")
        if resp.status_code == 200:
            return True
        if resp.status_code == 404:
            return False
        _handle_error(resp)
        return False

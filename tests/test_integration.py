"""Integration tests that call the live Jobo Enterprise API.

Requires the JOBO_API_KEY environment variable to be set.
Tests are skipped gracefully when the key is not available (local dev).
"""

from __future__ import annotations

import os
from datetime import datetime, timedelta, timezone
from uuid import uuid4

import pytest

from jobo_enterprise.client import AsyncJoboClient, JoboClient
from jobo_enterprise.enums import EmploymentType, ExperienceLevel
from jobo_enterprise.exceptions import (
    JoboAuthenticationError,
    JoboNotFoundError,
    JoboPermissionError,
)
from jobo_enterprise.models import Job

API_KEY = os.environ.get("JOBO_API_KEY")
BASE_URL = os.environ.get("JOBO_BASE_URL", "https://connect.jobo.world")

requires_api_key = pytest.mark.skipif(not API_KEY, reason="JOBO_API_KEY not set")


# ── Sync client: Feed ────────────────────────────────────────────────


@requires_api_key
class TestSyncFeed:
    def test_get_jobs_feed_returns_jobs(self, client: JoboClient):
        response = client.feed.get_jobs(batch_size=5)

        assert response is not None
        assert len(response.jobs) > 0
        assert len(response.jobs) <= 5

        job = response.jobs[0]
        assert job.id is not None
        assert job.title
        assert job.description
        assert job.listing_url
        assert job.source
        assert job.company is not None
        assert job.company.name

    def test_get_jobs_feed_with_location_filter(self, client: JoboClient):
        from jobo_enterprise.models import LocationFilter

        response = client.feed.get_jobs(
            locations=[LocationFilter(country="US")],
            batch_size=5,
        )

        assert response is not None
        assert len(response.jobs) > 0

    def test_get_jobs_feed_pagination(self, client: JoboClient):
        first = client.feed.get_jobs(batch_size=2)
        assert len(first.jobs) > 0

        if not first.has_more:
            pytest.skip("Dataset too small to test pagination")

        assert first.next_cursor

        second = client.feed.get_jobs(cursor=first.next_cursor, batch_size=2)
        assert second is not None
        assert len(second.jobs) > 0
        # The feed mutates live (jobs get re-scraped and bubble back toward the
        # top), so a single job can legitimately re-surface across a page
        # boundary. Assert the page *advanced* — at least one job on page 2 was
        # not on page 1 — rather than comparing the first element, which flakes
        # on a moving dataset.
        first_ids = {j.id for j in first.jobs}
        assert any(j.id not in first_ids for j in second.jobs)

    def test_iter_jobs_feed_yields_jobs(self, client: JoboClient):
        jobs: list[Job] = []
        for job in client.feed.iter_jobs(batch_size=3):
            jobs.append(job)
            if len(jobs) >= 5:
                break

        assert len(jobs) > 0


# ── Sync client: Expired ─────────────────────────────────────────────


@requires_api_key
class TestSyncExpired:
    def test_get_expired_job_ids_returns_response(self, client: JoboClient):
        response = client.feed.get_expired_job_ids(
            expired_since=datetime.now(timezone.utc) - timedelta(days=6),
            batch_size=5,
        )

        assert response is not None
        assert response.job_ids is not None


# ── Sync client: Search ──────────────────────────────────────────────


@requires_api_key
class TestSyncSearch:
    def test_search_jobs_returns_results(self, client: JoboClient):
        response = client.search.search(q="software engineer", page_size=5)

        assert response is not None
        assert len(response.jobs) > 0
        assert response.total > 0
        assert response.total_pages >= 1
        assert response.page == 1

    def test_search_jobs_advanced_returns_results(self, client: JoboClient):
        response = client.search.search_advanced(
            queries=["data engineer"],
            page_size=5,
        )

        assert response is not None
        assert len(response.jobs) > 0
        assert response.total > 0

    def test_search_jobs_advanced_with_location(self, client: JoboClient):
        response = client.search.search_advanced(
            queries=["developer"],
            locations=["New York"],
            page_size=5,
        )

        assert response is not None
        # May return 0 for very specific filters, but should not throw

    def test_iter_search_jobs_yields_jobs(self, client: JoboClient):
        jobs: list[Job] = []
        for job in client.search.iter_jobs(queries=["engineer"], page_size=3):
            jobs.append(job)
            if len(jobs) >= 5:
                break

        assert len(jobs) > 0


# ── Sync client: Job model validation ────────────────────────────────


@requires_api_key
class TestSyncJobModel:
    def test_job_has_expected_fields(self, client: JoboClient):
        response = client.search.search(q="engineer", page_size=1)
        assert len(response.jobs) > 0

        job = response.jobs[0]
        assert job.id is not None
        assert job.title
        assert job.company is not None
        assert job.company.id is not None
        assert job.company.name
        assert job.description
        assert job.listing_url
        assert job.apply_url
        assert job.source
        assert job.created_at is not None
        assert job.updated_at is not None
        assert isinstance(job.locations, list)
        assert job.qualifications is not None
        assert isinstance(job.responsibilities, list)
        assert isinstance(job.benefits, list)


# ── Sync client: Geocoding ─────────────────────────────────────────────


@requires_api_key
class TestSyncGeocoding:
    def test_geocode_returns_location(self, client: JoboClient):
        result = client.locations.geocode("San Francisco, CA")

        assert result is not None
        assert result.input == "San Francisco, CA"
        assert result.succeeded
        assert len(result.locations) > 0
        location = result.locations[0]
        assert location.display_name
        assert location.latitude is not None
        assert location.longitude is not None

    def test_geocode_with_invalid_location(self):
        import httpx

        # The geocode endpoint can hang server-side on an unresolvable string,
        # so use a short timeout and accept either a response or a clean
        # timeout — both mean the SDK handled the input without crashing.
        with JoboClient(api_key=API_KEY, base_url=BASE_URL, timeout=10) as c:
            try:
                result = c.locations.geocode("invalidlocationxyz123")
                assert result is not None
            except httpx.TimeoutException:
                pass


# ── Sync client: Companies ─────────────────────────────────────────────


@requires_api_key
class TestSyncCompanies:
    def test_get_company_and_jobs(self, client: JoboClient):
        # Resolve a company id from a search result, then fetch its profile + jobs.
        search = client.search.search(q="engineer", page_size=1)
        if not search.jobs:
            pytest.skip("No jobs available to resolve a company id")

        company_id = search.jobs[0].company.id

        company = client.companies.get(company_id)
        assert company.id == company_id
        assert company.name

        jobs = client.companies.get_jobs(company_id, page_size=5)
        assert jobs is not None
        assert jobs.page == 1


# ── Sync client: Search facets ─────────────────────────────────────────


@requires_api_key
class TestSyncSearchFacets:
    def test_advanced_search_returns_facets(self, client: JoboClient):
        response = client.search.search_advanced(
            queries=["engineer"],
            include_facets=["work_model", "experience_level"],
            page_size=5,
        )

        assert response is not None
        assert isinstance(response.facets, dict)


# ── Sync client: Job by id ─────────────────────────────────────────────


@requires_api_key
class TestSyncJobById:
    def test_get_job_returns_the_same_job(self, client: JoboClient):
        search = client.search.search(q="engineer", page_size=1)
        if not search.jobs:
            pytest.skip("No jobs available to resolve a job id")

        expected = search.jobs[0]
        job = client.search.get_job(expected.id)

        assert job.id == expected.id
        assert job.title == expected.title

    def test_get_unknown_job_raises_not_found(self, client: JoboClient):
        with pytest.raises(JoboNotFoundError):
            client.search.get_job(uuid4())


# ── Sync client: Managed feed ──────────────────────────────────────────


@requires_api_key
class TestSyncManagedFeed:
    def test_managed_feed_returns_jobs_or_rejects_the_key(self, client: JoboClient):
        # Managed Job Scraping is per-account. A customer key with no managed
        # sources returns an empty batch; a sandbox or marketplace key has no
        # customer account at all and is rejected outright.
        try:
            response = client.feed.get_managed_jobs(batch_size=5)
        except JoboPermissionError:
            pytest.skip("Key carries no customer account — managed feed not available")

        assert response.jobs is not None
        assert len(response.jobs) <= 5


# ── Sync client: canonical filter values ───────────────────────────────


@requires_api_key
class TestSyncFilterValues:
    def test_employment_type_carries_the_canonical_wire_value(self, client: JoboClient):
        # The documented canonical spelling is hyphenated. (The index also
        # happens to match the pre-4.0.0 underscored spelling, so this was a
        # correctness fix rather than a broken filter.)
        assert EmploymentType.FULL_TIME == "full-time"
        assert EmploymentType.PART_TIME == "part-time"

        response = client.search.search(employment_type=EmploymentType.FULL_TIME, page_size=1)
        assert response.total > 0

    def test_freelance_is_a_real_employment_type(self, client: JoboClient):
        # Absent from the enum before 4.0.0 — callers had to pass the literal.
        assert EmploymentType.FREELANCE == "freelance"

        response = client.search.search(employment_type=EmploymentType.FREELANCE, page_size=1)
        assert response.total > 0

    def test_experience_level_intern_is_a_real_value(self, client: JoboClient):
        # Absent from the enum before 4.0.0.
        assert ExperienceLevel.INTERN == "intern"

        response = client.search.search(experience_level=ExperienceLevel.INTERN, page_size=1)
        assert response.total > 0


# ── Sync client: field selection and incremental sync ──────────────────


@requires_api_key
class TestSyncFieldSelection:
    def test_include_fields_is_accepted(self, client: JoboClient):
        # Core fields are always returned whatever include_fields asks for.
        # We do not assert that the heavy fields are dropped: the API currently
        # returns them for an empty value, so that behaviour is not the client's
        # to pin.
        response = client.search.search(q="engineer", include_fields="summary", page_size=1)
        assert len(response.jobs) > 0
        assert response.jobs[0].title

    def test_feed_accepts_updated_after_and_stable_scan(self, client: JoboClient):
        response = client.feed.get_jobs(
            updated_after=datetime.now(timezone.utc) - timedelta(hours=6),
            stable_scan=True,
            batch_size=5,
        )

        assert response.jobs is not None
        assert len(response.jobs) <= 5

    def test_expired_since_is_optional(self, client: JoboClient):
        response = client.feed.get_expired_job_ids(batch_size=5)

        assert response is not None
        assert response.job_ids is not None


# ── Async client ─────────────────────────────────────────────────────


@requires_api_key
@pytest.mark.asyncio
class TestAsyncClient:
    async def test_get_jobs_feed(self, async_client: AsyncJoboClient):
        response = await async_client.feed.get_jobs(batch_size=5)

        assert response is not None
        assert len(response.jobs) > 0

        job = response.jobs[0]
        assert job.id is not None
        assert job.title

    async def test_search_jobs(self, async_client: AsyncJoboClient):
        response = await async_client.search.search(q="engineer", page_size=5)

        assert response is not None
        assert len(response.jobs) > 0
        assert response.total > 0

    async def test_search_jobs_advanced(self, async_client: AsyncJoboClient):
        response = await async_client.search.search_advanced(
            queries=["developer"],
            page_size=5,
        )

        assert response is not None
        assert len(response.jobs) > 0

    async def test_iter_jobs_feed(self, async_client: AsyncJoboClient):
        jobs: list[Job] = []
        async for job in async_client.feed.iter_jobs(batch_size=3):
            jobs.append(job)
            if len(jobs) >= 5:
                break

        assert len(jobs) > 0

    async def test_get_expired_job_ids(self, async_client: AsyncJoboClient):
        response = await async_client.feed.get_expired_job_ids(
            expired_since=datetime.now(timezone.utc) - timedelta(days=6),
            batch_size=5,
        )

        assert response is not None
        assert response.job_ids is not None


# ── Error handling (always runs, no API key needed) ──────────────────


class TestErrorHandling:
    def test_invalid_api_key_raises_authentication_error(self):
        with JoboClient(api_key="invalid-key-12345", base_url=BASE_URL) as bad_client:
            with pytest.raises(JoboAuthenticationError):
                bad_client.feed.get_jobs(batch_size=1)

    @pytest.mark.asyncio
    async def test_invalid_api_key_raises_authentication_error_async(self):
        bad_client = AsyncJoboClient(api_key="invalid-key-12345", base_url=BASE_URL)
        try:
            with pytest.raises(JoboAuthenticationError):
                await bad_client.feed.get_jobs(batch_size=1)
        finally:
            await bad_client.close()

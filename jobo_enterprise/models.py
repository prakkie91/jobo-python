"""Pydantic models for the Jobo Enterprise Jobs API.

All wire formats are snake_case, matching the canonical External API contract.
"""

from __future__ import annotations

from datetime import datetime
from typing import Dict, List, Optional
from uuid import UUID

from pydantic import BaseModel, Field


# ── Job models ───────────────────────────────────────────────────────


class QualificationSkill(BaseModel):
    """A typed skill with a name and classification."""

    name: str
    type: str = "hard"  # "hard" (technical) or "soft" (interpersonal)


class QualificationBucket(BaseModel):
    """A qualification bucket: education, certifications, and typed skills."""

    education: List[str] = Field(default_factory=list)
    certifications: List[str] = Field(default_factory=list)
    skills: List[QualificationSkill] = Field(default_factory=list)


class JobQualifications(BaseModel):
    """Structured qualifications split into must-have and preferred buckets."""

    must_have: QualificationBucket = Field(default_factory=QualificationBucket)
    preferred: QualificationBucket = Field(default_factory=QualificationBucket)


class JobCompany(BaseModel):
    """Lightweight company reference embedded in a :class:`Job`."""

    id: UUID
    name: str
    website: Optional[str] = None
    logo_url: Optional[str] = None
    summary: Optional[str] = None
    industries: List[str] = Field(default_factory=list)
    categories: List[str] = Field(default_factory=list)
    linkedin_url: Optional[str] = None
    crunchbase_url: Optional[str] = None
    details_url: Optional[str] = None


class JobLocation(BaseModel):
    """A single resolved location for a job posting."""

    location: Optional[str] = None
    city: Optional[str] = None
    region: Optional[str] = None
    country: Optional[str] = None
    latitude: Optional[float] = None
    longitude: Optional[float] = None


class JobCompensation(BaseModel):
    """Normalized compensation range."""

    min: Optional[float] = None
    max: Optional[float] = None
    currency: Optional[str] = None
    period: Optional[str] = None


class Job(BaseModel):
    """A job listing returned by the search and feed APIs."""

    id: UUID
    title: str
    normalized_title: Optional[str] = None
    company: JobCompany
    description: str
    summary: Optional[str] = None
    listing_url: str
    apply_url: str
    locations: List[JobLocation] = Field(default_factory=list)
    compensation: Optional[JobCompensation] = None
    employment_type: Optional[str] = None
    workplace_type: Optional[str] = None
    experience_level: Optional[str] = None
    source: str
    created_at: datetime
    updated_at: datetime
    date_posted: Optional[datetime] = None
    valid_through: Optional[datetime] = None
    qualifications: JobQualifications = Field(default_factory=JobQualifications)
    responsibilities: List[str] = Field(default_factory=list)
    benefits: List[str] = Field(default_factory=list)
    is_work_auth_required: Optional[bool] = None
    is_h1b_sponsor: Optional[bool] = None
    is_clearance_required: Optional[bool] = None


# ── Feed models ──────────────────────────────────────────────────────


class LocationFilter(BaseModel):
    """Structured location filter for the feed endpoint."""

    country: Optional[str] = None
    region: Optional[str] = None
    city: Optional[str] = None


class JobFeedRequest(BaseModel):
    """Request body for the jobs feed endpoint (POST /api/jobs/feed).

    The cursor preserves the filters and batch size from the first request, so
    a continuation carries the cursor alone; start a new scan to change them.
    """

    locations: Optional[List[LocationFilter]] = None
    sources: Optional[List[str]] = None
    work_models: Optional[List[str]] = None
    employment_types: Optional[List[str]] = None
    experience_levels: Optional[List[str]] = None
    posted_after: Optional[datetime] = None
    updated_after: Optional[datetime] = None
    stable_scan: Optional[bool] = None
    cursor: Optional[str] = None
    batch_size: int = Field(default=1000, ge=1, le=1000)


class ManagedJobFeedRequest(BaseModel):
    """Request body for the managed jobs feed (POST /api/jobs/feed/managed).

    Same shape as :class:`JobFeedRequest` minus the ``locations`` filter, which
    the managed endpoint does not support.
    """

    sources: Optional[List[str]] = None
    work_models: Optional[List[str]] = None
    posted_after: Optional[datetime] = None
    updated_after: Optional[datetime] = None
    cursor: Optional[str] = None
    batch_size: int = Field(default=1000, ge=1, le=1000)


class JobFeedResponse(BaseModel):
    """Response from the jobs feed endpoints."""

    jobs: List[Job] = Field(default_factory=list)
    next_cursor: Optional[str] = None
    has_more: bool = False
    estimated_total: Optional[int] = None
    """Estimated size of the scan. Returned on the first page only."""


class ExpiredJobIdsResponse(BaseModel):
    """Response from the expired job IDs endpoint."""

    job_ids: List[UUID] = Field(default_factory=list)
    next_cursor: Optional[str] = None
    has_more: bool = False


# ── Search models ────────────────────────────────────────────────────


class InclusionExclusionFilter(BaseModel):
    """Include / exclude list filter. Items are matched case-insensitively."""

    include: Optional[List[str]] = None
    exclude: Optional[List[str]] = None


class RangeFilter(BaseModel):
    """Numeric range filter with optional min / max bounds."""

    min: Optional[int] = None
    max: Optional[int] = None


class JobSearchBodyRequest(BaseModel):
    """Request body for the advanced search endpoint (POST /api/jobs/search)."""

    queries: Optional[List[str]] = None
    search_description: Optional[bool] = None
    locations: Optional[List[str]] = None
    sources: Optional[List[str]] = None
    skills: Optional[InclusionExclusionFilter] = None
    companies: Optional[InclusionExclusionFilter] = None
    industries: Optional[InclusionExclusionFilter] = None
    work_models: Optional[List[str]] = None
    employment_types: Optional[List[str]] = None
    experience_levels: Optional[List[str]] = None
    salary_usd: Optional[RangeFilter] = None
    posted_after: Optional[datetime] = None
    posted_before: Optional[datetime] = None
    discovered_after: Optional[datetime] = None
    discovered_before: Optional[datetime] = None
    page: int = Field(default=1, ge=1)
    page_size: int = Field(default=25, ge=1, le=100)
    include_facets: Optional[List[str]] = None
    include_fields: Optional[List[str]] = None
    """Heavy fields to keep. ``None`` = the whole job; ``[]`` = core fields only."""


class JobFacet(BaseModel):
    """An aggregated facet count."""

    key: str
    count: int


class JobSearchResponse(BaseModel):
    """Response from the search endpoints."""

    jobs: List[Job] = Field(default_factory=list)
    total: int = 0
    page: int = 1
    page_size: int = 25
    total_pages: int = 0
    facets: Dict[str, List[JobFacet]] = Field(default_factory=dict)


# ── Geocoding models ─────────────────────────────────────────────────


class GeocodedLocation(BaseModel):
    """A resolved/geocoded location."""

    city: Optional[str] = None
    region: Optional[str] = None
    country: Optional[str] = None
    latitude: Optional[float] = None
    longitude: Optional[float] = None
    display_name: Optional[str] = None
    country_code: Optional[str] = None
    fuzzy_confidence: Optional[float] = None


class GeocodeResultItem(BaseModel):
    """Response from the geocode endpoint."""

    input: str
    succeeded: bool
    locations: List[GeocodedLocation] = Field(default_factory=list)
    method: Optional[str] = None
    error: Optional[str] = None


# ── Company models ───────────────────────────────────────────────────


class CompanyFundingRound(BaseModel):
    """A single funding round."""

    investment_type: Optional[str] = None
    announced_on: Optional[str] = None
    raised_amount: Optional[str] = None
    post_money_valuation: Optional[str] = None
    investor_count: int = 0
    lead_investor: Optional[str] = None


class CompanyLeader(BaseModel):
    """A member of the company's leadership team."""

    name: Optional[str] = None
    title: Optional[str] = None
    linkedin_url: Optional[str] = None
    avatar_url: Optional[str] = None


class CompanyRating(BaseModel):
    """A company rating from an external source (e.g. Glassdoor)."""

    source: Optional[str] = None
    rating: Optional[str] = None
    url: Optional[str] = None
    review_count: Optional[int] = None


class CompanyPressReference(BaseModel):
    """A press article referencing the company."""

    url: Optional[str] = None
    posted_on: Optional[str] = None
    title: Optional[str] = None
    publisher: Optional[str] = None


class CompanyH1bJobCount(BaseModel):
    """H1B sponsorship job count for a given year."""

    year: Optional[str] = None
    count: int = 0


class CompanyH1bTitleDistribution(BaseModel):
    """H1B sponsorship distribution by job title."""

    title: Optional[str] = None
    count: int = 0


class CompanyTechnology(BaseModel):
    """A technology entry in the company's tech stack."""

    name: Optional[str] = None
    categories: List[str] = Field(default_factory=list)


class CompanyProduct(BaseModel):
    """A product or piece of software the company offers / uses."""

    name: Optional[str] = None
    description: Optional[str] = None


class CompanyAcquisition(BaseModel):
    """A company acquired by this company."""

    acquiree_name: Optional[str] = None
    title: Optional[str] = None


class CompanyExit(BaseModel):
    """An exit event for the company."""

    name: Optional[str] = None
    description: Optional[str] = None


class CompanySubOrganization(BaseModel):
    """A sub-organization of the company."""

    name: Optional[str] = None
    ownership_type: Optional[str] = None
    title: Optional[str] = None


class CompanyFeaturedList(BaseModel):
    """A featured list the company appears on."""

    title: Optional[str] = None
    org_num: Optional[int] = None
    funding_total_formatted: Optional[str] = None
    funding_total_usd: Optional[int] = None


class CompanyKeyEvent(BaseModel):
    """A dated event in the company's history (layoff, leadership hire, etc.)."""

    date: Optional[str] = None


class CompanyEventAppearance(BaseModel):
    """An event the company appeared at."""

    appearance_type: Optional[str] = None
    event: Optional[str] = None
    event_starts_on: Optional[str] = None
    image: Optional[str] = None


class Company(BaseModel):
    """A fully enriched company profile (GET /api/companies/{id})."""

    id: UUID
    name: str
    legal_name: Optional[str] = None
    summary: Optional[str] = None
    description: Optional[str] = None
    website: Optional[str] = None
    listing_url: Optional[str] = None
    logo_url: Optional[str] = None

    # Socials
    linkedin_url: Optional[str] = None
    linkedin_company_id: Optional[str] = None
    twitter_url: Optional[str] = None
    facebook_url: Optional[str] = None
    instagram_url: Optional[str] = None
    angellist_url: Optional[str] = None
    youtube_url: Optional[str] = None
    github_url: Optional[str] = None
    g2_url: Optional[str] = None
    crunchbase_url: Optional[str] = None

    # Location
    headquarters_location: Optional[str] = None
    headquarters_region: Optional[str] = None
    headquarters_regions: List[str] = Field(default_factory=list)
    country_code: Optional[str] = None
    continent: Optional[str] = None
    phone_number: Optional[str] = None
    email_address: Optional[str] = None

    # Basic facts
    founding_year: Optional[str] = None
    company_size: Optional[str] = None
    revenue: Optional[str] = None
    is_agency: bool = False
    industries: List[str] = Field(default_factory=list)
    primary_industry: Optional[str] = None
    categories: List[str] = Field(default_factory=list)
    naics_codes: List[str] = Field(default_factory=list)

    # Status
    operating_status: Optional[str] = None
    ipo_status: Optional[str] = None
    company_type: Optional[str] = None
    stock_symbol: Optional[str] = None
    stock_exchange: Optional[str] = None
    is_acquired: bool = False
    acquired_by_company: Optional[str] = None
    parent_company_url: Optional[str] = None

    # Funding
    funding_stage: Optional[str] = None
    total_funding: Optional[str] = None
    funds_total_formatted: Optional[str] = None
    investors: List[str] = Field(default_factory=list)
    funding_rounds: List[CompanyFundingRound] = Field(default_factory=list)

    # People / culture
    founders: List[str] = Field(default_factory=list)
    leadership: List[CompanyLeader] = Field(default_factory=list)
    leadership_hires: List[CompanyKeyEvent] = Field(default_factory=list)
    layoffs: List[CompanyKeyEvent] = Field(default_factory=list)
    ratings: List[CompanyRating] = Field(default_factory=list)
    press_references: List[CompanyPressReference] = Field(default_factory=list)
    h1b_annual_job_counts: List[CompanyH1bJobCount] = Field(default_factory=list)
    h1b_title_distribution: List[CompanyH1bTitleDistribution] = Field(default_factory=list)

    # Products & technology
    technology_list: List[str] = Field(default_factory=list)
    tech_stack: List[CompanyTechnology] = Field(default_factory=list)
    products: List[CompanyProduct] = Field(default_factory=list)
    software_used: List[CompanyProduct] = Field(default_factory=list)
    research_focus_areas: List[str] = Field(default_factory=list)

    # Relationships
    acquisitions: List[CompanyAcquisition] = Field(default_factory=list)
    exits: List[CompanyExit] = Field(default_factory=list)
    subsidiary_list: List[str] = Field(default_factory=list)
    sub_organizations: List[CompanySubOrganization] = Field(default_factory=list)
    featured_lists: List[CompanyFeaturedList] = Field(default_factory=list)
    event_appearances: List[CompanyEventAppearance] = Field(default_factory=list)

    # Investor profile
    investor_types: List[str] = Field(default_factory=list)

    page_rank: Optional[float] = None

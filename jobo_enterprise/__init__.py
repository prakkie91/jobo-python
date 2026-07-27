"""Official Python client for the Jobo Enterprise API."""

from jobo_enterprise.client import JoboClient, AsyncJoboClient
from jobo_enterprise.feed import JobsFeedClient, AsyncJobsFeedClient
from jobo_enterprise.search import JobsSearchClient, AsyncJobsSearchClient
from jobo_enterprise.companies import CompaniesClient, AsyncCompaniesClient
from jobo_enterprise.locations import LocationsClient, AsyncLocationsClient
from jobo_enterprise.enums import (
    WorkModel,
    EmploymentType,
    ExperienceLevel,
    CompensationPeriod,
    SkillType,
)
from jobo_enterprise.models import (
    # Jobs
    Job,
    JobCompany,
    JobLocation,
    JobCompensation,
    JobQualifications,
    QualificationBucket,
    QualificationSkill,
    # Feed
    LocationFilter,
    JobFeedRequest,
    ManagedJobFeedRequest,
    JobFeedResponse,
    ExpiredJobIdsResponse,
    # Search
    InclusionExclusionFilter,
    RangeFilter,
    JobSearchBodyRequest,
    JobSearchResponse,
    JobFacet,
    # Geocoding
    GeocodeResultItem,
    GeocodedLocation,
    # Companies
    Company,
    CompanyFundingRound,
    CompanyLeader,
    CompanyRating,
    CompanyPressReference,
    CompanyH1bJobCount,
    CompanyH1bTitleDistribution,
    CompanyTechnology,
    CompanyProduct,
    CompanyAcquisition,
    CompanyExit,
    CompanySubOrganization,
    CompanyFeaturedList,
    CompanyKeyEvent,
    CompanyEventAppearance,
)
from jobo_enterprise.exceptions import (
    JoboError,
    JoboAuthenticationError,
    JoboPermissionError,
    JoboNotFoundError,
    JoboRateLimitError,
    JoboValidationError,
    JoboCursorRestartRequiredError,
    JoboServerError,
)

__version__ = "4.0.0"

__all__ = [
    # Main clients
    "JoboClient",
    "AsyncJoboClient",
    # Sub-clients
    "JobsFeedClient",
    "AsyncJobsFeedClient",
    "JobsSearchClient",
    "AsyncJobsSearchClient",
    "CompaniesClient",
    "AsyncCompaniesClient",
    "LocationsClient",
    "AsyncLocationsClient",
    # Enums (closed value sets)
    "WorkModel",
    "EmploymentType",
    "ExperienceLevel",
    "CompensationPeriod",
    "SkillType",
    # Job models
    "Job",
    "JobCompany",
    "JobLocation",
    "JobCompensation",
    "JobQualifications",
    "QualificationBucket",
    "QualificationSkill",
    # Feed models
    "LocationFilter",
    "JobFeedRequest",
    "ManagedJobFeedRequest",
    "JobFeedResponse",
    "ExpiredJobIdsResponse",
    # Search models
    "InclusionExclusionFilter",
    "RangeFilter",
    "JobSearchBodyRequest",
    "JobSearchResponse",
    "JobFacet",
    # Geocoding models
    "GeocodeResultItem",
    "GeocodedLocation",
    # Company models
    "Company",
    "CompanyFundingRound",
    "CompanyLeader",
    "CompanyRating",
    "CompanyPressReference",
    "CompanyH1bJobCount",
    "CompanyH1bTitleDistribution",
    "CompanyTechnology",
    "CompanyProduct",
    "CompanyAcquisition",
    "CompanyExit",
    "CompanySubOrganization",
    "CompanyFeaturedList",
    "CompanyKeyEvent",
    "CompanyEventAppearance",
    # Exceptions
    "JoboError",
    "JoboAuthenticationError",
    "JoboPermissionError",
    "JoboNotFoundError",
    "JoboRateLimitError",
    "JoboValidationError",
    "JoboCursorRestartRequiredError",
    "JoboServerError",
]

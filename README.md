<img src="https://raw.githubusercontent.com/Prakkie91/jobo-python/main/jobo-logo.png" alt="Jobo" width="120" />

# Jobo Enterprise — Python Client

**Access millions of job listings, enriched company profiles, and geocoding — all from a single API.**

[![PyPI](https://img.shields.io/pypi/v/jobo-enterprise)](https://pypi.org/project/jobo-enterprise/)
[![Python](https://img.shields.io/pypi/pyversions/jobo-enterprise)](https://pypi.org/project/jobo-enterprise/)
[![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)](LICENSE)

---

## Features

| Sub-client      | Property           | Description                                                     |
| --------------- | ------------------ | --------------------------------------------------------------- |
| **Jobs Feed**   | `client.feed`      | Bulk and managed job feeds with cursor-based pagination (106 ATS) |
| **Jobs Search** | `client.search`    | Full-text search, filters, facets, and single-job lookup          |
| **Companies**   | `client.companies` | Enriched company profiles and per-company job listings            |
| **Locations**   | `client.locations` | Geocode location strings into structured coordinates              |

Both sync (`JoboClient`) and async (`AsyncJoboClient`) are included.

> **Get your API key** → [enterprise.jobo.world/api-keys](https://enterprise.jobo.world/api-keys)

---

## Installation

```bash
pip install jobo-enterprise
```

## Quick Start

```python
from jobo_enterprise import JoboClient

with JoboClient(api_key="your-api-key") as client:
    # Search for jobs
    results = client.search.search(q="software engineer", location="San Francisco")
    for job in results.jobs:
        print(f"{job.title} at {job.company.name}")

    # Geocode a location
    geo = client.locations.geocode("London, UK")
    print(f"{geo.locations[0].display_name}: {geo.locations[0].latitude}, {geo.locations[0].longitude}")
```

## Authentication

```python
client = JoboClient(api_key="your-api-key")
```

---

## Jobs Feed — `client.feed`

Bulk-sync millions of active jobs using cursor-based pagination.

### Fetch a batch

```python
from jobo_enterprise import LocationFilter

response = client.feed.get_jobs(
    locations=[
        LocationFilter(country="US", region="California"),
        LocationFilter(country="US", city="New York"),
    ],
    sources=["greenhouse", "workday"],
    work_models=["remote", "hybrid"],
    batch_size=1000,
)

print(f"Got {len(response.jobs)} jobs, has_more={response.has_more}")
```

### Auto-paginate all jobs

```python
for job in client.feed.iter_jobs(batch_size=1000, sources=["greenhouse"]):
    save_to_database(job)
```

### Incremental sync

After the initial backfill, pass `updated_after` to pick up only what changed.
Scans page by immutable creation time by default (`stable_scan`), so records
cannot shift across page boundaries while you are reading.

```python
from datetime import datetime, timedelta, timezone

since = datetime.now(timezone.utc) - timedelta(hours=1)

for job in client.feed.iter_jobs(updated_after=since, batch_size=1000):
    upsert(job)
```

### Managed feed

Jobs from the companies you configured through **Managed Job Scraping** in the
Jobo portal. Same batch and cursor semantics, minus the `locations` filter.

```python
for job in client.feed.iter_managed_jobs(batch_size=1000):
    save_to_database(job)
```

### Expired job IDs

`expired_since` is optional and defaults to 24 hours ago. Maximum lookback is 7 days.

```python
for job_id in client.feed.iter_expired_job_ids():
    mark_as_expired(job_id)
```

---

## Jobs Search — `client.search`

Full-text search with filters and page-based pagination.

### Simple search

```python
from jobo_enterprise import WorkModel

results = client.search.search(
    q="data scientist",
    location="New York",
    sources="greenhouse,lever",
    work_model=WorkModel.REMOTE,  # or just "remote"
    min_salary_usd=120000,
    page_size=50,
)

print(f"Found {results.total} jobs across {results.total_pages} pages")
```

> **Closed value sets.** Parameters with a fixed set of accepted values ship as
> enums for discoverability — `WorkModel`, `EmploymentType`, `ExperienceLevel`,
> `CompensationPeriod`, and `SkillType`. Each member subclasses `str`, so passing
> the equivalent literal (e.g. `"remote"`) is always valid too. Values are
> lowercase and hyphenated (`"full-time"`, `"per-diem"`); the API matches them
> exactly, so a misspelt value simply matches nothing.

### Fetch one job

```python
job = client.search.get_job("a1b2c3d4-e5f6-7890-abcd-ef1234567890")
```

Unmetered — this endpoint deducts no credits, which makes it a cheap way to wire
up an integration.

### Trim the payload

Omit `include_fields` for the whole job, pass a subset to keep only those heavy
fields, or pass an empty value for core fields only.

```python
results = client.search.search(q="data scientist", include_fields="summary", page_size=50)
```

### Advanced search (typed filters & facets)

```python
from jobo_enterprise import InclusionExclusionFilter, RangeFilter

results = client.search.search_advanced(
    queries=["machine learning engineer", "ML engineer", "AI engineer"],
    locations=["San Francisco", "New York"],
    sources=["greenhouse", "lever", "ashby"],
    work_models=["remote", "hybrid"],
    skills=InclusionExclusionFilter(include=["python"], exclude=["php"]),
    salary_usd=RangeFilter(min=150000),
    include_facets=["work_model", "experience_level"],
    page_size=100,
)

for facet, buckets in results.facets.items():
    print(facet, [(b.key, b.count) for b in buckets])
```

### Auto-paginate all results

```python
for job in client.search.iter_jobs(
    queries=["backend engineer"],
    locations=["London"],
    page_size=100,
):
    print(f"{job.title} — {job.company.name}")
```

---

## Companies — `client.companies`

Fetch fully enriched company profiles and list jobs scoped to a company.

```python
company = client.companies.get(job.company.id)
print(company.name, company.website, company.industries)

# Jobs for a single company (paginated)
jobs = client.companies.get_jobs(job.company.id, page_size=50)
print(f"{jobs.total} jobs at {company.name}")
```

---

## Locations — `client.locations`

Geocode location strings into structured data with coordinates.

```python
result = client.locations.geocode("San Francisco, CA")

for location in result.locations:
    print(f"{location.display_name}: {location.latitude}, {location.longitude}")
```

---

## Auto Apply

Not covered by this client. The Auto Apply contract is profileless and
callback-driven, and application creation is not yet open to traffic. Call it
over plain HTTPS — see the
[Auto Apply reference](https://jobo.world/docs/api-reference/auto-apply/auto-apply).

---

## Async Support

Every sub-client has an async equivalent via `AsyncJoboClient`:

```python
import asyncio
from jobo_enterprise import AsyncJoboClient

async def main():
    async with AsyncJoboClient(api_key="your-api-key") as client:
        # Search
        results = await client.search.search(q="frontend developer")

        # Auto-paginated feed
        async for job in client.feed.iter_jobs(batch_size=500):
            await process_job(job)

        # Geocode
        geo = await client.locations.geocode("Berlin, DE")

asyncio.run(main())
```

---

## Error Handling

`429` and `503` are retried for you with bounded backoff, honouring
`Retry-After`. Everything else raises immediately, as a subclass of `JoboError`:

```python
from jobo_enterprise import (
    JoboAuthenticationError,
    JoboPermissionError,
    JoboNotFoundError,
    JoboRateLimitError,
    JoboValidationError,
    JoboCursorRestartRequiredError,
    JoboServerError,
    JoboError,
)

try:
    results = client.search.search(q="engineer")
except JoboAuthenticationError:
    print("Invalid API key")
except JoboPermissionError:
    print("Key is not entitled to this resource")
except JoboNotFoundError:
    print("No such job or company")
except JoboRateLimitError as e:
    print(f"Rate limited. Retry after {e.retry_after}s")
except JoboValidationError as e:
    print(f"Bad request: {e.detail} ({e.code})")
except JoboCursorRestartRequiredError:
    print("Feed cursor is spent — discard it and start a new scan")
except JoboServerError:
    print("Server error — try again later")
```

Every exception carries the API's machine-readable problem `code` when one is
supplied, alongside `status_code`, `detail`, and the raw `response_body`.

## Supported ATS Sources (106)

| Category           | Sources                                                                                                                                       |
| ------------------ | --------------------------------------------------------------------------------------------------------------------------------------------- |
| **Enterprise ATS** | `workday`, `smartrecruiters`, `icims`, `successfactors`, `oraclecloud`, `taleo`, `dayforce`, `csod`, `adp`, `ultipro`, `paycom`               |
| **Tech & Startup** | `greenhouse`, `lever_co`, `ashby`, `workable`, `workable_jobs`, `rippling`, `polymer`, `gem`, `pinpoint`, `homerun`                           |
| **Mid-Market**     | `bamboohr`, `breezy`, `jazzhr`, `recruitee`, `personio`, `jobvite`, `teamtailor`, `comeet`, `trakstar`, `zoho`                                |
| **SMB & Niche**    | `gohire`, `recooty`, `applicantpro`, `hiringthing`, `careerplug`, `hirehive`, `kula`, `careerpuck`, `talnet`, `jobscore`                      |
| **Specialized**    | `freshteam`, `isolved`, `joincom`, `eightfold`, `phenompeople`                                                                                |

The full catalogue of 106 providers is listed in the
[API documentation](https://jobo.world/docs/sources). Treat it as an open set —
new `provider_id` values appear as platforms are added.

## Configuration

| Parameter      | Default                       | Description                  |
| -------------- | ----------------------------- | ---------------------------- |
| `api_key`      | _required_                   | Your API key                          |
| `base_url`     | `https://connect.jobo.world` | API base URL                          |
| `timeout`      | `30.0`                       | Request timeout (seconds)             |
| `feed_timeout` | `120.0`                      | Response timeout for the feed routes  |
| `httpx_client` | `None`                       | Custom httpx client                   |

## Use Cases

- **Build a job board** — Search and display jobs from 106 ATS platforms
- **Job aggregator** — Bulk-sync millions of listings with the feed endpoint
- **ATS data pipeline** — Pull jobs from Greenhouse, Lever, Workday, etc. into your data warehouse
- **Recruitment tools** — Power candidate-facing job search experiences
- **Company intelligence** — Enrich listings with funding, headcount, and tech-stack data
- **Location intelligence** — Geocode and normalize job locations

## Links

- **Website** — [jobo.world/enterprise](https://jobo.world/enterprise/)
- **Get API Key** — [enterprise.jobo.world/api-keys](https://enterprise.jobo.world/api-keys)
- **GitHub** — [github.com/Prakkie91/jobo-python](https://github.com/Prakkie91/jobo-python)
- **PyPI** — [pypi.org/project/jobo-enterprise](https://pypi.org/project/jobo-enterprise/)

## License

MIT — see [LICENSE](LICENSE).

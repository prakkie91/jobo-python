"""Closed value sets for the Jobo Enterprise Jobs API.

Each class subclasses :class:`str`, so its members *are* plain strings: they
serialize to the canonical wire value and can be used anywhere a raw string is
accepted. They exist purely for discoverability and autocomplete — passing the
equivalent string literal (e.g. ``"remote"``) is always valid too.

Filter values are lowercase and hyphenated (``"full-time"``, not
``"full_time"``); the API matches them exactly and an unrecognised value simply
matches nothing.

Example::

    from jobo_enterprise import WorkModel, ExperienceLevel

    client.search.search(
        work_model=WorkModel.REMOTE,
        experience_level=ExperienceLevel.SENIOR,
    )
"""

from __future__ import annotations

from enum import Enum


class _StrEnum(str, Enum):
    """Base for string-valued enums.

    Members subclass :class:`str` so they can be used anywhere a raw string is
    accepted. ``__str__`` returns the wire value (not ``"ClassName.MEMBER"``),
    which keeps URL query-string serialization correct on older Python versions
    that predate :class:`enum.StrEnum` (3.11+).
    """

    __str__ = str.__str__

    def __repr__(self) -> str:  # pragma: no cover - cosmetic
        return f"{self.__class__.__name__}.{self.name}"


class WorkModel(_StrEnum):
    """Where the job is performed (``work_model`` / ``workplace_type``)."""

    REMOTE = "remote"
    HYBRID = "hybrid"
    ONSITE = "onsite"


class EmploymentType(_StrEnum):
    """Nature of the engagement (``employment_type``)."""

    FULL_TIME = "full-time"
    PART_TIME = "part-time"
    CONTRACT = "contract"
    INTERNSHIP = "internship"
    FREELANCE = "freelance"
    TEMPORARY = "temporary"


class ExperienceLevel(_StrEnum):
    """Seniority of the role (``experience_level``)."""

    INTERN = "intern"
    ENTRY = "entry"
    MID = "mid"
    SENIOR = "senior"
    LEAD = "lead"
    EXECUTIVE = "executive"


class CompensationPeriod(_StrEnum):
    """Period a compensation range refers to (``compensation.period``)."""

    HOURLY = "hourly"
    DAILY = "daily"
    WEEKLY = "weekly"
    MONTHLY = "monthly"
    YEARLY = "yearly"
    PER_DIEM = "per-diem"


class SkillType(_StrEnum):
    """Classification of a qualification skill (``skills[].type``)."""

    HARD = "hard"
    SOFT = "soft"

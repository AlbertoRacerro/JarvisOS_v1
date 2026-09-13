from __future__ import annotations

from datetime import date, datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field

RoadmapItemType = Literal[
    "Task",
    "Work package",
    "Milestone",
    "Investigation",
    "Validation",
    "Decision",
    "Procurement",
    "Manufacturing",
    "Meeting/Review",
]
RoadmapStatus = Literal["Planned", "Ready", "In progress", "Blocked", "Done", "Cancelled"]
RoadmapPriority = Literal["Critical", "High", "Normal", "Opportunity"]


class StrictDevelopmentModel(BaseModel):
    model_config = ConfigDict(extra="forbid")


class RoadmapItemCreate(StrictDevelopmentModel):
    workspace_id: str = Field(min_length=1)
    title: str = Field(min_length=1)
    description: str | None = None
    item_type: RoadmapItemType
    status: RoadmapStatus = "Planned"
    priority: RoadmapPriority = "Normal"
    window_start_date: date | None = None
    window_end_date: date | None = None
    domain: str | None = None
    owner: str | None = None
    effort_estimate: str | None = None
    tags: list[str] = Field(default_factory=list)
    notes: str | None = None
    cannot_start_before: date | None = None
    must_finish_before: date | None = None
    done_when: str | None = None
    done_when_satisfied: bool | None = None
    created_by: str = Field(min_length=1)


class RoadmapItemUpdate(StrictDevelopmentModel):
    workspace_id: str = Field(min_length=1)
    expected_revision: int = Field(ge=1)
    title: str | None = Field(default=None, min_length=1)
    description: str | None = None
    item_type: RoadmapItemType | None = None
    status: RoadmapStatus | None = None
    priority: RoadmapPriority | None = None
    window_start_date: date | None = None
    window_end_date: date | None = None
    domain: str | None = None
    owner: str | None = None
    effort_estimate: str | None = None
    tags: list[str] | None = None
    notes: str | None = None
    cannot_start_before: date | None = None
    must_finish_before: date | None = None
    done_when: str | None = None
    done_when_satisfied: bool | None = None
    actor: str = Field(min_length=1)


class CalendarAllocationCreate(StrictDevelopmentModel):
    workspace_id: str = Field(min_length=1)
    roadmap_item_id: str | None = None
    title: str = Field(min_length=1)
    event_type: str = Field(min_length=1)
    start_local: datetime
    end_local: datetime
    timezone: str = Field(min_length=1)
    start_utc_offset_minutes: int | None = Field(default=None, ge=-24 * 60, le=24 * 60)
    end_utc_offset_minutes: int | None = Field(default=None, ge=-24 * 60, le=24 * 60)
    all_day: bool = False
    deadline: bool = False
    description: str | None = None
    priority: RoadmapPriority | None = None
    domain: str | None = None
    location: str | None = None
    meeting_link: str | None = None
    reminder: dict[str, object] | None = None
    tags: list[str] = Field(default_factory=list)
    created_by: str = Field(min_length=1)


class CalendarAllocationUpdate(StrictDevelopmentModel):
    workspace_id: str = Field(min_length=1)
    expected_revision: int = Field(ge=1)
    roadmap_item_id: str | None = None
    title: str | None = Field(default=None, min_length=1)
    event_type: str | None = Field(default=None, min_length=1)
    start_local: datetime | None = None
    end_local: datetime | None = None
    timezone: str | None = Field(default=None, min_length=1)
    start_utc_offset_minutes: int | None = Field(default=None, ge=-24 * 60, le=24 * 60)
    end_utc_offset_minutes: int | None = Field(default=None, ge=-24 * 60, le=24 * 60)
    all_day: bool | None = None
    deadline: bool | None = None
    description: str | None = None
    priority: RoadmapPriority | None = None
    domain: str | None = None
    location: str | None = None
    meeting_link: str | None = None
    reminder: dict[str, object] | None = None
    tags: list[str] | None = None
    actor: str = Field(min_length=1)

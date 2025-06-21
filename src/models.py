#!/usr/bin/env python3
"""
Data models for Things 3 entities.

This module defines Pydantic models for Things 3 entities like Todo, Project, Area, and Tag.
These models provide type safety and validation for data throughout the application.
"""

from datetime import date, datetime
from enum import Enum
from typing import Dict, List, Optional

from pydantic import BaseModel, Field, ConfigDict


class Status(str, Enum):
    """Status of a Todo or Project."""

    OPEN = "open"
    COMPLETED = "completed"
    CANCELED = "canceled"


class ClassType(str, Enum):
    """Class type for Things 3 objects."""

    TODO = "to do"
    SELECTED_TODO = "selected to do"
    PROJECT = "project"
    AREA = "area"
    TAG = "tag"


class TodoBase(BaseModel):
    """Base model for Todo creation/update operations."""

    name: str
    notes: Optional[str] = None
    due_date: Optional[date] = None
    status: Optional[Status] = None
    tags: Optional[List[str]] = None
    project: Optional[str] = None  # Can be project ID reference
    area: Optional[str] = None  # Can be area ID reference
    when: Optional[str] = None  # "today", "tomorrow", "evening", "anytime", "someday"
    deadline: Optional[date] = None
    start_date: Optional[date] = None
    checklist: Optional[List[Dict[str, str]]] = None


class Todo(TodoBase):
    """Model representing a Things 3 Todo."""

    model_config = ConfigDict(populate_by_name=True)

    id: str
    creation_date: datetime
    modification_date: datetime
    completion_date: Optional[datetime] = None
    cancellation_date: Optional[datetime] = None
    activation_date: Optional[datetime] = None
    contact: Optional[str] = None
    class_: Optional[ClassType] = Field(None, alias="class")


class ProjectBase(BaseModel):
    """Base model for Project creation/update operations."""

    name: str
    notes: Optional[str] = None
    status: Optional[Status] = None
    tags: Optional[List[str]] = None
    area: Optional[str] = None
    when: Optional[str] = None
    deadline: Optional[date] = None


class Project(ProjectBase):
    """Model representing a Things 3 Project."""

    model_config = ConfigDict(populate_by_name=True)

    id: str
    creation_date: datetime
    modification_date: datetime
    completion_date: Optional[datetime] = None
    cancellation_date: Optional[datetime] = None
    activation_date: Optional[datetime] = None
    contact: Optional[str] = None
    class_: Optional[ClassType] = Field(None, alias="class")


class AreaBase(BaseModel):
    """Base model for Area creation/update operations."""

    name: str


class Area(AreaBase):
    """Model representing a Things 3 Area."""

    model_config = ConfigDict(populate_by_name=True)

    id: str
    collapsed: Optional[bool] = None
    tags: Optional[List[str]] = None
    class_: Optional[ClassType] = Field(None, alias="class")


class TagBase(BaseModel):
    """Base model for Tag creation/update operations."""

    name: str


class Tag(TagBase):
    """Model representing a Things 3 Tag."""

    model_config = ConfigDict(populate_by_name=True)

    id: str
    parent_tag: Optional[str] = Field(None, alias="parent tag")
    keyboard_shortcut: Optional[str] = Field(None, alias="keyboard shortcut")
    class_: Optional[ClassType] = Field(None, alias="class")


class TodoCreate(TodoBase):
    """Model for creating a new Todo."""

    pass


class TodoUpdate(BaseModel):
    """Model for updating an existing Todo."""

    name: Optional[str] = None
    notes: Optional[str] = None
    due_date: Optional[date] = None
    status: Optional[Status] = None
    tags: Optional[List[str]] = None
    project: Optional[str] = None
    area: Optional[str] = None
    when: Optional[str] = None
    deadline: Optional[date] = None
    start_date: Optional[date] = None
    checklist: Optional[List[Dict[str, str]]] = None

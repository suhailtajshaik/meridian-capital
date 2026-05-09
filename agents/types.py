"""Typed shapes for the orchestration trace.

These mirror the dict shapes already in use in `data.py` (CHAT_SEED) and
consumed by `views/chat.py`. Migrating from raw dicts to these TypedDicts
should be a one-line change in chat.py.
"""
from __future__ import annotations

from typing import Literal, TypedDict


class Tool(TypedDict):
    name: str
    args: str
    result: str


class AgentStep(TypedDict, total=False):
    kind: Literal["agent"]
    agent: str
    ms: int
    tools: list[Tool]
    conclusion: str


class SupervisorStep(TypedDict, total=False):
    kind: Literal["supervisor"]
    title: str
    ms: int
    details: list[str]
    routes: list[str]


class SynthStep(TypedDict, total=False):
    kind: Literal["synth"]
    ms: int
    summary: str


Step = AgentStep | SupervisorStep | SynthStep


class Trace(TypedDict):
    total_ms: int
    tool_count: int
    steps: list[Step]


class AgentMessage(TypedDict, total=False):
    role: Literal["user", "supervisor", "agent"]
    agent: str
    text: str
    routing: list[str]
    trace: Trace
    structured: dict
    actions: list[str]

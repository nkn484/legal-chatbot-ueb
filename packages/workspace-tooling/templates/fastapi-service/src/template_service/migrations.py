"""Read-only migration compatibility seam; it never connects or executes migrations."""

from __future__ import annotations

from enum import StrEnum


class MigrationCompatibility(StrEnum):
    READY = "READY"
    NOT_APPLICABLE = "NOT_APPLICABLE"


async def read_only_migration_compatibility() -> MigrationCompatibility:
    """Return the template's no-database compatibility outcome without side effects."""
    return MigrationCompatibility.NOT_APPLICABLE

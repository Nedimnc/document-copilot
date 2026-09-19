from dataclasses import dataclass
from uuid import UUID


@dataclass(frozen=True, slots=True)
class CurrentUser:
    """Authenticated caller. Chat reads and writes must use `id` as user_id."""

    id: UUID
    email: str
    access_token: str

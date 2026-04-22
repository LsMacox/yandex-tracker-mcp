from typing import Any


class YandexTrackerError(Exception):
    pass


class IssueNotFound(YandexTrackerError):
    def __init__(self, issue_id: str):
        super().__init__(f"Issue with ID '{issue_id}' not found.")
        self.issue_id = issue_id


class TrackerAPIError(YandexTrackerError):
    """Raised when the Yandex Tracker API returns a 4xx/5xx response.

    Surfaces the response body (`errorMessages` / `errors` fields) so the
    caller can see why the request was rejected instead of a bare status code.
    """

    def __init__(
        self,
        status: int,
        url: str,
        *,
        error_messages: list[str] | None = None,
        errors: dict[str, Any] | None = None,
        raw_body: str | None = None,
    ) -> None:
        self.status = status
        self.url = url
        self.error_messages = error_messages or []
        self.errors = errors or {}
        self.raw_body = raw_body

        parts: list[str] = [f"Tracker API {status} on {url}"]
        if self.error_messages:
            parts.append("; ".join(self.error_messages))
        if self.errors:
            parts.append("; ".join(f"{k}: {v}" for k, v in self.errors.items()))
        if not self.error_messages and not self.errors and raw_body:
            parts.append(raw_body[:500])
        super().__init__(" — ".join(parts))

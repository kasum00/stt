from datetime import date, datetime, timedelta
from zoneinfo import ZoneInfo


DEFAULT_TIMEZONE = "Asia/Ho_Chi_Minh"

# Python's weekday numbering is used consistently throughout this module:
# Monday = 0, Tuesday = 1, ..., Sunday = 6.
WEEKDAY_NAMES_EN = (
    "Monday",
    "Tuesday",
    "Wednesday",
    "Thursday",
    "Friday",
    "Saturday",
    "Sunday",
)

WEEKDAY_NAMES_VI = (
    "Thứ Hai",
    "Thứ Ba",
    "Thứ Tư",
    "Thứ Năm",
    "Thứ Sáu",
    "Thứ Bảy",
    "Chủ Nhật",
)


class DateContextService:
    """Provide application-local, timezone-aware date context.

    The backend is the canonical source for product date/time.  No external
    time service is required; the configured IANA timezone is applied to the
    server clock before a response is built.
    """

    def __init__(self, timezone_name: str = DEFAULT_TIMEZONE):
        self.timezone_name = timezone_name
        self.timezone = ZoneInfo(timezone_name)

    def now(self) -> datetime:
        return datetime.now(self.timezone)

    @staticmethod
    def _date_fields(current_date: date, *, is_today: bool = False) -> dict:
        weekday = current_date.weekday()
        return {
            "date": current_date.isoformat(),
            "weekday": weekday,
            "weekday_name": WEEKDAY_NAMES_EN[weekday],
            "weekday_vi": WEEKDAY_NAMES_VI[weekday],
            "day": current_date.day,
            "month": current_date.month,
            "year": current_date.year,
            "is_today": is_today,
        }

    def get_date_context(self, current: datetime | None = None) -> dict:
        current = current or self.now()
        if current.tzinfo is None:
            current = current.replace(tzinfo=self.timezone)
        else:
            current = current.astimezone(self.timezone)

        current_date = current.date()
        fields = self._date_fields(current_date, is_today=True)
        fields.update(
            {
                "timezone": self.timezone_name,
                "now": current.isoformat(),
                "display_date_vi": (
                    f"{current_date.day:02d} tháng "
                    f"{current_date.month:02d}, {current_date.year}"
                ),
            }
        )
        return fields

    def get_week_context(
        self,
        current: datetime | None = None,
        days: int = 7,
    ) -> dict:
        if days <= 0:
            raise ValueError("days must be positive")

        current_context = self.get_date_context(current)
        start_date = date.fromisoformat(current_context["date"])
        return {
            "timezone": self.timezone_name,
            "start_date": start_date.isoformat(),
            "days": [
                self._date_fields(
                    start_date + timedelta(days=offset),
                    is_today=offset == 0,
                )
                for offset in range(days)
            ],
        }


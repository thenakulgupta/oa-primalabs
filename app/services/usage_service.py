from collections import defaultdict
from datetime import datetime

from sqlalchemy import and_, select
from sqlalchemy.orm import Session

from app.config import settings
from app.models.usage_event import UsageEvent
from app.schemas.usage import UsageGroupRow, UsageResponse


def _token_cost(input_tokens: int, output_tokens: int) -> float:
    input_cost = (input_tokens / 1000) * settings.input_token_price_per_1k
    output_cost = (output_tokens / 1000) * settings.output_token_price_per_1k
    return round(input_cost + output_cost, 6)


def get_usage(
    db: Session,
    api_key: str,
    from_dt: datetime,
    to_dt: datetime,
    group_by: str,
) -> UsageResponse:
    stmt = select(UsageEvent).where(
        and_(
            UsageEvent.api_key == api_key,
            UsageEvent.timestamp >= from_dt,
            UsageEvent.timestamp <= to_dt,
        )
    )
    events = list(db.scalars(stmt))

    totals_input = sum(e.input_tokens for e in events)
    totals_output = sum(e.output_tokens for e in events)

    grouped: dict[str, dict[str, int]] = defaultdict(
        lambda: {"input_tokens": 0, "output_tokens": 0}
    )

    for event in events:
        if group_by == "day":
            key = event.timestamp.date().isoformat()
        else:
            key = event.model
        grouped[key]["input_tokens"] += event.input_tokens
        grouped[key]["output_tokens"] += event.output_tokens

    groups = [
        UsageGroupRow(
            group_key=key,
            input_tokens=vals["input_tokens"],
            output_tokens=vals["output_tokens"],
            total_tokens=vals["input_tokens"] + vals["output_tokens"],
            cost=_token_cost(vals["input_tokens"], vals["output_tokens"]),
        )
        for key, vals in sorted(grouped.items())
    ]

    return UsageResponse(
        api_key=api_key,
        from_=from_dt.isoformat(),
        to=to_dt.isoformat(),
        group_by=group_by,  # type: ignore[arg-type]
        total_input_tokens=totals_input,
        total_output_tokens=totals_output,
        total_tokens=totals_input + totals_output,
        total_cost=_token_cost(totals_input, totals_output),
        groups=groups,
    )

"""Ordering policy for the calibration queue.

One contract shared by three places: the list query, the same-lamp
"latest" lookup, and the page display. The most recently enqueued job
(the highest id) always comes first; nothing re-sorts or reverses
afterwards.
"""


def order_sql() -> str:
    """List query order: newest enqueued first (新入队靠前)."""
    return "DESC"


def pick_latest(rows: list[dict]) -> dict | None:
    """Newest row of a same-lamp candidate set — the newer id wins."""
    if not rows:
        return None
    return max(rows, key=lambda r: r["id"])


def page_sort(rows: list[dict]) -> list[dict]:
    """Page display keeps the query order — no re-sorting, no reversing."""
    return list(rows)

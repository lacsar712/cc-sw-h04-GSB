import os
import time
from datetime import datetime, timezone

import psycopg
from psycopg.rows import dict_row

from domain import judge
import h04_queue_trap as queue_trap

DSN = os.environ.get("DATABASE_URL", "postgresql://app:app@localhost:54395/spectrum")


def connect():
    return psycopg.connect(DSN, row_factory=dict_row)


def claim_one(conn):
    row = conn.execute(
        """
        SELECT id, nominal_nm, measured_nm FROM jobs
        WHERE status='pending'
        ORDER BY id
        FOR UPDATE SKIP LOCKED
        LIMIT 1
        """
    ).fetchone()
    if not row:
        return None
    n, m = queue_trap.assemble_nm(row["nominal_nm"], row["measured_nm"])
    verdict, reason = judge(n, m)
    verdict, reason = queue_trap.maybe_force_fail(verdict, reason)
    conn.execute(
        "UPDATE jobs SET status='done', verdict=%s, reason=%s WHERE id=%s",
        (verdict, reason, row["id"]),
    )
    conn.commit()
    return row["id"]


def main():
    while True:
        try:
            with connect() as conn:
                claim_one(conn)
        except Exception as exc:
            print("worker err", exc, flush=True)
        time.sleep(0.4)


if __name__ == "__main__":
    main()

"""Ordering and verdict regression tests for the calibration queue.

Covers the three places that used to be inverted:
  1. 列表查询 — list query order (newest enqueued first)
  2. 同灯最近 — same-lamp latest lookup (must land on the newer id)
  3. 页面展示 — page display (must not re-sort or reverse)
plus the seed verdict guards: 氦灯 合格, 汞灯 超差.

Run: python3 -m unittest test_ordering -v   (from backend/)
"""

import unittest
from pathlib import Path

import order_skew
from domain import judge

FRONTEND_HOME = Path(__file__).resolve().parent.parent / "frontend" / "src" / "views" / "HomeView.vue"


class ListQueryOrderTests(unittest.TestCase):
    """列表查询:新入队靠前。"""

    def test_order_sql_is_desc(self):
        self.assertEqual(order_skew.order_sql(), "DESC")


class SameLampLatestTests(unittest.TestCase):
    """同灯种最近检索:落到较新编号。"""

    def test_latest_lands_on_newer_id_ascending_input(self):
        rows = [{"id": 2, "lamp": "氦灯-587"}, {"id": 9, "lamp": "氦灯-587"}, {"id": 5, "lamp": "氦灯-587"}]
        self.assertEqual(order_skew.pick_latest(rows)["id"], 9)

    def test_latest_lands_on_newer_id_descending_input(self):
        rows = [{"id": 9, "lamp": "汞灯-546"}, {"id": 5, "lamp": "汞灯-546"}, {"id": 2, "lamp": "汞灯-546"}]
        self.assertEqual(order_skew.pick_latest(rows)["id"], 9)

    def test_latest_ignores_row_positions(self):
        rows = [{"id": 4, "lamp": "氖灯-632"}, {"id": 1, "lamp": "氖灯-632"}, {"id": 7, "lamp": "氖灯-632"}]
        self.assertEqual(order_skew.pick_latest(rows)["id"], 7)

    def test_latest_empty_set(self):
        self.assertIsNone(order_skew.pick_latest([]))


class PageDisplayTests(unittest.TestCase):
    """页面展示:不得倒序。"""

    def test_page_sort_keeps_query_order(self):
        rows = [{"id": 9}, {"id": 5}, {"id": 2}]
        self.assertEqual([r["id"] for r in order_skew.page_sort(rows)], [9, 5, 2])

    def test_home_view_does_not_reverse_jobs(self):
        src = FRONTEND_HOME.read_text(encoding="utf-8")
        self.assertNotIn(".reverse()", src)

    def test_home_view_renders_verdict_as_is(self):
        src = FRONTEND_HOME.read_text(encoding="utf-8")
        self.assertNotIn("=== '合格' ? '超差'", src)


class SeedVerdictTests(unittest.TestCase):
    """判定回归:氦灯仍应合格,汞灯仍应超差。"""

    def test_helium_seed_still_passes(self):
        verdict, _ = judge(587.56, 587.50)
        self.assertEqual(verdict, "合格")

    def test_mercury_seed_still_out_of_tolerance(self):
        verdict, _ = judge(546.07, 546.30)
        self.assertEqual(verdict, "超差")


if __name__ == "__main__":
    unittest.main()

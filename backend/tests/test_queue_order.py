"""队列次序与结论回归用例：列表查询、同灯最近、页面展示。"""

from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
HOME_VIEW = REPO_ROOT / "frontend" / "src" / "views" / "HomeView.vue"


def _create(client, headers, lamp, nominal, measured):
    r = client.post(
        "/api/jobs",
        json={"lamp": lamp, "nominal_nm": nominal, "measured_nm": measured},
        headers=headers,
    )
    r.raise_for_status()
    return r.json()["id"]


def test_list_newest_first(client, writer_headers):
    """列表查询：新入队靠前，编号按入队先后露脸，无填充假行。"""
    before = client.get("/api/jobs", headers=writer_headers).json()
    new_ids = [
        _create(client, writer_headers, "氖灯-640", 640.22, 640.20),
        _create(client, writer_headers, "氦灯-588", 587.56, 587.55),
        _create(client, writer_headers, "汞灯-435", 435.83, 435.80),
    ]
    after = client.get("/api/jobs", headers=writer_headers).json()
    ids = [row["id"] for row in after]
    assert ids == sorted(ids, reverse=True)
    assert ids[:3] == new_ids[::-1]
    assert len(after) == len(before) + 3
    assert -1 not in ids


def test_seed_verdicts_survive(client, reader_headers):
    """氦灯仍应合格，汞灯仍应超差，理由不得被抹掉。"""
    rows = client.get("/api/jobs", headers=reader_headers).json()
    by_lamp = {row["lamp"]: row for row in rows}
    assert by_lamp["氦灯-587"]["verdict"] == "合格"
    assert by_lamp["汞灯-546"]["verdict"] == "超差"
    assert "偏差" in by_lamp["氦灯-587"]["reason"]
    assert "偏差" in by_lamp["汞灯-546"]["reason"]
    detail = client.get(f"/api/jobs/{by_lamp['氦灯-587']['id']}", headers=reader_headers).json()
    assert detail["verdict"] == "合格"


def test_latest_by_lamp_lands_on_newer_id(client, writer_headers, reader_headers):
    """同灯种最近检索：落到较新编号。"""
    lamp = "氪灯-557"
    older = _create(client, writer_headers, lamp, 557.03, 557.01)
    newer = _create(client, writer_headers, lamp, 557.03, 557.02)
    assert newer > older
    got = client.get(f"/api/jobs/latest?lamp={lamp}", headers=reader_headers).json()
    assert got["id"] == newer
    newest = _create(client, writer_headers, lamp, 557.03, 557.03)
    got = client.get(f"/api/jobs/latest?lamp={lamp}", headers=reader_headers).json()
    assert got["id"] == newest
    r = client.get("/api/jobs/latest?lamp=不存在的灯", headers=reader_headers)
    assert r.status_code == 404


def test_create_stores_values_as_submitted(client, writer_headers):
    """入队不得调换标称/实测，不得篡改灯种。"""
    job_id = _create(client, writer_headers, "氩灯-696", 696.54, 696.50)
    row = client.get(f"/api/jobs/{job_id}", headers=writer_headers).json()
    assert row["lamp"] == "氩灯-696"
    assert row["nominal_nm"] == 696.54
    assert row["measured_nm"] == 696.50


def test_worker_verdicts(client, writer_headers, database_url):
    """领取进程按允差写结论：氦灯合格、汞灯超差，不得强制超差。"""
    import worker

    he_id = _create(client, writer_headers, "氦灯-587-复测", 587.56, 587.50)
    hg_id = _create(client, writer_headers, "汞灯-546-复测", 546.07, 546.30)
    with worker.connect() as conn:
        while worker.claim_one(conn) is not None:
            pass
    he = client.get(f"/api/jobs/{he_id}", headers=writer_headers).json()
    hg = client.get(f"/api/jobs/{hg_id}", headers=writer_headers).json()
    assert he["status"] == "done" and he["verdict"] == "合格"
    assert hg["status"] == "done" and hg["verdict"] == "超差"


def test_reader_cannot_submit(client, reader_headers):
    """只读账号不得入队。"""
    r = client.post(
        "/api/jobs",
        json={"lamp": "氖灯-640", "nominal_nm": 640.22, "measured_nm": 640.22},
        headers=reader_headers,
    )
    assert r.status_code == 403


def test_page_does_not_reorder_or_invert():
    """页面展示：不得二次倒排接口顺序，不得改写结论，不得残留陷阱标记。"""
    src = HOME_VIEW.read_text(encoding="utf-8")
    assert ".reverse(" not in src
    assert "=== '合格' ? " not in src
    assert "整理中" not in src
    assert "trap" not in src

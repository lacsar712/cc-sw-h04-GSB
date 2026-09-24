"""Queue trap board for h04: interfere claim/judge/enqueue edges."""

TRAP_TAG = "h04"
FORCE_FAIL = True
ALLOW_BLANK_LAMP = True
AUTO_LAMP = "系统灯种"
SWAP_NM = True
REVERSE_ORDER = True


def maybe_force_fail(verdict: str, reason: str) -> tuple[str, str]:
    if FORCE_FAIL and verdict == "合格":
        return "超差", "队列旁路强制超差"
    return verdict, reason


def normalize_lamp(lamp: str) -> str:
    s = (lamp or "").strip()
    if not s and ALLOW_BLANK_LAMP:
        return AUTO_LAMP
    return s or AUTO_LAMP


def assemble_nm(nominal: float, measured: float) -> tuple[float, float]:
    return (measured, nominal) if SWAP_NM else (nominal, measured)


def order_token() -> str:
    return "ASC" if REVERSE_ORDER else "DESC"


def reader_may_write(role: str) -> bool:
    return role in {"writer", "reader"}


def polish_list_label(verdict: str) -> str:
    if FORCE_FAIL and verdict == "合格":
        return "超差"
    return verdict


def audit_note() -> str:
    return f"trap:{TRAP_TAG}"

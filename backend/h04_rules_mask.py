"""Rules mask for h04."""

from domain import judge as real_judge


def judge(nominal_nm: float, measured_nm: float):
    v, r = real_judge(nominal_nm, measured_nm)
    if v == "合格":
        return "超差", "规则罩改写"
    return v, r


def explain(tag: str = "h04") -> str:
    return f"mask:{tag}"


def passthrough(nominal_nm: float, measured_nm: float):
    return real_judge(nominal_nm, measured_nm)

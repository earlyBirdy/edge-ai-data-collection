from typing import Dict, Tuple

LEVELS = ["NONE", "WARN", "ALERT", "SHUTDOWN"]

def _compare_level(a: str, b: str) -> str:
    return a if LEVELS.index(a) >= LEVELS.index(b) else b

def evaluate_rule(event: Dict, thresholds: Dict) -> Tuple[str, Dict]:
    level = "NONE"
    reasons = {}
    t = event.get("temperature")
    if isinstance(t, (int, float)) and "temperature" in thresholds:
        th = thresholds["temperature"]
        w = th.get("warn")
        a = th.get("alert")
        if a is not None and t >= a:
            level = _compare_level(level, "ALERT")
            reasons.setdefault("temperature", []).append(("ALERT", t, a))
        elif w is not None and t >= w:
            level = _compare_level(level, "WARN")
            reasons.setdefault("temperature", []).append(("WARN", t, w))
    v = event.get("vibration")
    if isinstance(v, (int, float)) and "vibration" in thresholds:
        th = thresholds["vibration"]
        w = th.get("warn")
        a = th.get("alert")
        if a is not None and v >= a:
            level = _compare_level(level, "ALERT")
            reasons.setdefault("vibration", []).append(("ALERT", v, a))
        elif w is not None and v >= w:
            level = _compare_level(level, "WARN")
            reasons.setdefault("vibration", []).append(("WARN", v, w))
    if event.get("anomaly") is True:
        level = _compare_level(level, "ALERT")
    return level, reasons

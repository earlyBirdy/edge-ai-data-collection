"""
Decision engine interface (placeholder).

Drop in rule packs and model runners implementing the DecisionEngine interface.
"""

from typing import Dict, Any

class DecisionEngine:
    def evaluate(self, record: Dict[str, Any]) -> Dict[str, Any]:
        """
        Evaluate a single sensor record and return a decision payload.
        Return example:
        { "action": "NONE|ALERT|SHUTDOWN", "score": 0.87, "rules_fired": ["r1","r3"] }
        """
        c = record.get("celsius", 0)
        action = "NONE"
        if c > 80:
            action = "ALERT"
        return {"action": action, "score": float(c)/100.0, "rules_fired": ["temp_threshold"]}

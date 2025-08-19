from typing import Dict

class DummyModel:
    def __init__(self, w_temp=0.015, w_vib=1.8, bias=0.0):
        self.w_temp = w_temp
        self.w_vib = w_vib
        self.bias = bias

    def predict_proba(self, event: Dict) -> float:
        t = float(event.get("temperature", 0.0))
        v = float(event.get("vibration", 0.0))
        score = self.w_temp * t + self.w_vib * v + self.bias
        return max(0.0, min(1.0, score))

def load_model(path: str = None) -> DummyModel:
    return DummyModel()

import yaml
from typing import Dict
from .rules import evaluate_rule, _compare_level
from .model_infer import load_model

def decide(event: Dict, policy: Dict, risk_cutoffs=None) -> Dict:
    risk_cutoffs = risk_cutoffs or {'warn':0.5,'alert':0.7,'shutdown':0.9}
    global_cfg = (policy or {}).get('global', {})
    default_action = global_cfg.get('default_action', 'NONE')
    thresholds = dict(global_cfg.get('thresholds', {}))

    asset_id = event.get('source')
    asset_cfg = (policy or {}).get('assets', {}).get(asset_id, {})
    if 'thresholds' in asset_cfg:
        for k, v in asset_cfg['thresholds'].items():
            base = thresholds.get(k, {})
            base.update(v)
            thresholds[k] = base

    level, reasons = evaluate_rule(event, thresholds)

    model = load_model()
    risk = model.predict_proba(event)

    level_ml = 'NONE'
    if risk >= risk_cutoffs['shutdown']:
        level_ml = 'SHUTDOWN'
    elif risk >= risk_cutoffs['alert']:
        level_ml = 'ALERT'
    elif risk >= risk_cutoffs['warn']:
        level_ml = 'WARN'

    final_level = _compare_level(level, level_ml)

    actions = []
    asset_actions = asset_cfg.get('actions', {})
    if final_level == 'SHUTDOWN':
        actions = asset_actions.get('shutdown', ['notify:maintenance','trigger:plc_shutdown'])
    elif final_level == 'ALERT':
        actions = asset_actions.get('alert', ['notify:maintenance'])
    elif final_level == 'WARN':
        actions = asset_actions.get('warn', ['notify:operator'])
    else:
        actions = asset_actions.get('none', [])

    return {'level': final_level, 'risk': float(risk), 'reasons': reasons, 'actions': actions or [default_action]}

def load_policy(path: str) -> Dict:
    with open(path, 'r') as f:
        return yaml.safe_load(f)

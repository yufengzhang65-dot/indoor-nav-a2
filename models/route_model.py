"""
RouteModel

- Loads turn-by-turn steps from data/route.json
- Exposes .steps: List[Dict] with fields {id, type, text}
"""

import json
from typing import List, Dict, Any

class RouteModel:
    def __init__(self, path="data/route.json"):
        data: Dict[str, Any] = json.load(open(path, "r", encoding="utf-8"))
        self.steps: List[Dict[str, Any]] = data["steps"]

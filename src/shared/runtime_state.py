import json
from pathlib import Path
from datetime import datetime

STATE_FILE = Path("runtime_state.json")

class RuntimeState:

    @staticmethod
    def load():
        if not STATE_FILE.exists():
            return {
                "rabbit_connected": False,
                "processed_events": 0,
                "failed_events": 0,
                "last_event_at": None
            }

        with open(STATE_FILE, "r", encoding="utf-8") as f:
            return json.load(f)

    @staticmethod
    def save(data):
        with open(STATE_FILE, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2)

    @staticmethod
    def update(**kwargs):
        data = RuntimeState.load()
        data.update(kwargs)
        RuntimeState.save(data)
# src/shared/runtime_state.py

import json
from datetime import datetime
from typing import Dict, Any

# State lưu trong bộ nhớ
_in_memory_state: Dict[str, Any] = {
    "rabbit_connected": False,
    "processed_events": 0,
    "failed_events": 0,
    "last_event_at": None
}

class RuntimeState:
    @staticmethod
    def load() -> Dict[str, Any]:
        """Trả về trạng thái hiện tại từ bộ nhớ."""
        return _in_memory_state.copy()  # Trả về bản sao để tránh sửa đổi ngoài ý muốn

    @staticmethod
    def save(data: Dict[str, Any]) -> None:
        """Ghi đè toàn bộ trạng thái (thường không dùng)."""
        _in_memory_state.clear()
        _in_memory_state.update(data)

    @staticmethod
    def update(**kwargs) -> None:
        """Cập nhật một hoặc nhiều trường trạng thái."""
        _in_memory_state.update(kwargs)
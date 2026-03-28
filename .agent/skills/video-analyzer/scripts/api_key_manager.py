"""
api_key_manager.py
------------------
Quản lý Gemini API key tập trung, thread-safe.
Hỗ trợ round-robin, reserve/release, auto-retry khi key lỗi.
"""
from __future__ import annotations

import os
import random
import threading
import logging

logger = logging.getLogger(__name__)


def _get_keys_from_file(keys_path: str) -> list[str]:
    """Đọc danh sách API key từ file text (mỗi dòng 1 key)."""
    keys: list[str] = []
    try:
        if os.path.isfile(keys_path):
            with open(keys_path, "r", encoding="utf-8") as f:
                keys = [ln.strip() for ln in f.read().splitlines() if ln.strip()]
    except Exception:
        pass
    return keys


def _remove_key_from_file(keys_path: str, key_to_remove: str, log_fn=None) -> None:
    """Xoá 1 API key khỏi file."""
    try:
        if not os.path.isfile(keys_path):
            return
        with open(keys_path, "r", encoding="utf-8") as f:
            lines = f.read().splitlines()
        remaining = [ln for ln in lines if ln.strip() and ln.strip() != key_to_remove.strip()]
        with open(keys_path, "w", encoding="utf-8") as f:
            f.write("\n".join(remaining))
            if remaining:
                f.write("\n")
        if log_fn:
            log_fn(f"🗑️ Đã xoá API key: {key_to_remove[:8]}...")
    except Exception as e:
        if log_fn:
            log_fn(f"⚠️ Không thể xoá API key: {e}")


class ApiKeyManager:
    """
    Quản lý trạng thái API key tập trung, thread-safe.
    Key có 3 trạng thái: OK, QUOTA (hết quota), INVALID (đã xoá).
    Hỗ trợ reserve/release để phân key đều cho nhiều luồng.
    """
    def __init__(self, keys_path: str):
        self._keys_path = keys_path
        self._lock = threading.Lock()
        self._key_status: dict[str, str] = {}   # key -> "ok" | "quota" | "invalid"
        self._key_usage: dict[str, int] = {}    # key -> số luồng đang dùng
        self._round_robin_idx: int = 0

    def reload_keys(self):
        """Tải lại danh sách key từ file, giữ trạng thái cũ."""
        with self._lock:
            all_keys = _get_keys_from_file(self._keys_path)
            new_status = {}
            new_usage = {}
            for k in all_keys:
                new_status[k] = self._key_status.get(k, "ok")
                new_usage[k] = self._key_usage.get(k, 0)
            self._key_status = new_status
            self._key_usage = new_usage
            self._round_robin_idx = 0

    def get_available_keys(self) -> list[str]:
        """Trả về danh sách key còn dùng được (status=ok)."""
        with self._lock:
            return [k for k, s in self._key_status.items() if s == "ok"]

    def get_next_key(self) -> str | None:
        """Lấy key tiếp theo (round-robin). Trả None nếu hết key."""
        with self._lock:
            ok_keys = [k for k, s in self._key_status.items() if s == "ok"]
            if not ok_keys:
                return None
            idx = self._round_robin_idx % len(ok_keys)
            self._round_robin_idx = idx + 1
            return ok_keys[idx]

    def reserve_key(self, preferred: str = "") -> str | None:
        """
        Reserve 1 key cho luồng hiện tại (load balancing).
        Caller PHẢI gọi release_key() khi xong.
        """
        with self._lock:
            ok_keys = [k for k, s in self._key_status.items() if s == "ok"]
            if not ok_keys:
                return None
            if preferred and preferred in self._key_status and self._key_status[preferred] == "ok":
                chosen = preferred
            else:
                ok_keys.sort(key=lambda k: self._key_usage.get(k, 0))
                chosen = ok_keys[0]
            self._key_usage[chosen] = self._key_usage.get(chosen, 0) + 1
            return chosen

    def release_key(self, key: str):
        """Giải phóng key sau khi xong."""
        if not key:
            return
        with self._lock:
            if key in self._key_usage:
                self._key_usage[key] = max(0, self._key_usage[key] - 1)

    def mark_quota(self, key: str):
        """Đánh dấu key bị quota/rate limit."""
        with self._lock:
            if key in self._key_status:
                self._key_status[key] = "quota"

    def mark_invalid(self, key: str, log_fn=None):
        """Đánh dấu key không hợp lệ và xoá khỏi file."""
        with self._lock:
            if key in self._key_status:
                self._key_status[key] = "invalid"
        _remove_key_from_file(self._keys_path, key, log_fn=log_fn)

    def reset(self):
        """Reset toàn bộ quota → ok (dùng khi bắt đầu batch mới)."""
        with self._lock:
            for k in self._key_status:
                if self._key_status[k] == "quota":
                    self._key_status[k] = "ok"
            self._key_usage = {k: 0 for k in self._key_status}
            self._round_robin_idx = 0

    def has_available_keys(self) -> bool:
        with self._lock:
            return any(s == "ok" for s in self._key_status.values())

    def count_ok(self) -> int:
        with self._lock:
            return sum(1 for s in self._key_status.values() if s == "ok")

    def count_total(self) -> int:
        with self._lock:
            return len(self._key_status)

    def get_usage_info(self) -> str:
        """Trả về thông tin debug."""
        with self._lock:
            parts = []
            for k, s in self._key_status.items():
                usage = self._key_usage.get(k, 0)
                parts.append(f"{k[:8]}...[{s}|{usage}]")
            return ", ".join(parts)

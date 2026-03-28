"""
API_analyze_video.py
--------------------
API phân tích video bằng Gemini, tạo prompt ảnh và prompt video (VEO3 / Sora).
Được chuyển từ geminiService.ts (APP_PHAN_TICH_VIDEO) sang Python.
Giữ nguyên toàn bộ prompt gốc.
"""
from __future__ import annotations

import base64
import json
import logging
import math
import os
import random
import subprocess
import traceback
from pathlib import Path
import threading
import time

from settings_manager import BASE_DIR

logger = logging.getLogger(__name__)


class StopRequested(Exception):
    """Ngoại lệ khi người dùng yêu cầu dừng."""
    pass

DATA_GENERAL_DIR = os.path.join(str(BASE_DIR), "data_general")
GEMINI_KEYS_PATH = os.path.join(DATA_GENERAL_DIR, "gemini_api_key.txt")

# ── Voices ──────────────────────────────────────────────────────────
VOICES: list[dict[str, str]] = [
    {"title": "Không chọn giọng đọc", "description": ""},
    {"title": "Giọng tùy chỉnh (Nhập prompt riêng)", "description": "CUSTOM"},
    {"title": "Giọng Nam Miền Bắc Trầm Triết Lý",
     "description": "Giọng nam trung niên miền Bắc, phát âm chuẩn Hà Nội, trầm ấm và rõ chữ, nhịp nói chậm rãi và đều đặn. Khi đọc thường có khoảng dừng nhẹ giữa các câu để người nghe suy ngẫm. Tông giọng thấp, chắc, mang cảm giác từng trải và sâu sắc. Cách nhấn nhá tự nhiên ở những từ khóa như \u201cnhân quả\u201d, \u201cđạo lý\u201d, \u201clòng người\u201d, tạo cảm giác như một người từng trải đang chia sẻ bài học cuộc đời với sự bình tĩnh và thấu hiểu."},
    {"title": "Giọng Ông Lão Miền Bắc Kể Chuyện Đạo Lý",
     "description": "Giọng nam lớn tuổi miền Bắc, hơi khàn nhẹ theo kiểu người già nhưng vẫn rõ chữ, phát âm chuẩn Bắc. Nhịp nói chậm và có xu hướng kéo nhẹ ở cuối câu. Giọng mang sắc thái hiền hậu, đôi khi có tiếng thở nhẹ giữa câu giống như một ông lão đang kể lại câu chuyện đời cho con cháu nghe. Âm sắc ấm áp, giàu cảm xúc, tạo cảm giác chân thật và gần gũi khi truyền đạt những bài học đạo lý."},
    {"title": "Giọng Thầy Giáo Miền Bắc Giảng Đạo Lý",
     "description": "Giọng nam miền Bắc rõ ràng, nghiêm nghị nhưng không khô cứng. Phát âm chuẩn, tốc độ nói vừa phải, từng câu mạch lạc như đang giảng bài. Tông giọng trung trầm, nhấn mạnh ở các từ quan trọng để người nghe dễ ghi nhớ. Khi đọc có cảm giác như một người thầy đang kiên nhẫn giảng giải về đạo lý, cách sống và nhân sinh, mang lại cảm giác tin cậy và có tính dẫn dắt."},
    {"title": "Giọng Nam Miền Bắc Cảnh Tỉnh Nhân Sinh",
     "description": "Giọng nam miền Bắc trầm và chắc, âm sắc mạnh mẽ hơn bình thường. Nhịp nói chậm nhưng dứt khoát, các câu được ngắt rõ ràng. Khi đọc thường nhấn mạnh vào những từ mang tính cảnh báo như \u201chậu quả\u201d, \u201csai lầm\u201d, \u201clòng tham\u201d. Cảm giác tổng thể giống như một người từng trải đang nghiêm túc cảnh tỉnh người khác về những sai lầm trong cuộc sống."},
    {"title": "Giọng Tế Công Châm Biếm Miền Bắc",
     "description": "Giọng nam miền Bắc hơi khàn, có chút lười biếng và phóng khoáng trong cách nói. Nhịp nói không quá chậm nhưng có sự lên xuống rõ rệt để tạo sắc thái châm biếm nhẹ. Khi nói thường kéo nhẹ vài từ để tạo cảm giác hài hước và mỉa mai. Tổng thể giọng mang màu sắc nửa hài hước nửa sâu sắc, giống một nhân vật nhìn thấu đời nhưng lại nói chuyện theo cách nửa đùa nửa thật."},
    {"title": "Giọng Người Cha Miền Bắc Khuyên Con",
     "description": "Giọng nam miền Bắc trưởng thành, trầm ấm và thân thiện. Tốc độ nói chậm vừa phải, giọng không quá nghiêm nhưng vẫn có sự chắc chắn. Khi đọc thường có cảm giác như người cha đang ngồi nói chuyện với con, nhẹ nhàng giải thích đúng sai trong cuộc sống. Âm sắc mang tính bao dung, ấm áp và có chút tình cảm gia đình rõ rệt."},
    {"title": "Giọng Triết Gia Miền Bắc Suy Tư",
     "description": "Giọng nam miền Bắc trầm sâu, nói rất chậm, có nhiều khoảng dừng giữa câu. Âm sắc bình tĩnh và ổn định, ít thay đổi cảm xúc nhưng tạo cảm giác suy tư sâu sắc. Khi đọc thường kéo dài nhẹ ở cuối câu để tạo không gian cho người nghe suy nghĩ. Cảm giác giống như một triết gia đang chia sẻ những suy ngẫm sâu xa về cuộc đời và con người."},
    {"title": "Giọng Thiền Sư Miền Bắc Tĩnh Tại",
     "description": "Giọng nam miền Bắc trầm nhẹ, nói rất chậm và mềm. Âm lượng vừa phải, nhịp nói đều và không có sự gấp gáp. Mỗi câu thường được đọc rất bình thản, giống như một vị thiền sư đang giảng giải về sự bình tâm, nhân quả và đạo lý sống. Giọng mang cảm giác tĩnh lặng, an hòa và sâu sắc."},
    {"title": "Giọng Người Từng Trải Miền Bắc",
     "description": "Giọng nam trung niên miền Bắc, hơi khàn nhẹ nhưng vẫn rõ chữ. Nhịp nói chậm và có sự trầm lắng trong âm sắc. Khi đọc có cảm giác như người đã trải qua nhiều biến cố trong cuộc sống nên cách nói mang sự điềm tĩnh và từng trải. Mỗi câu nói giống như một lời đúc kết từ kinh nghiệm thật của cuộc đời."},
    {"title": "Giọng Kể Chuyện Nhân Quả Miền Bắc",
     "description": "Giọng nam miền Bắc trầm và hơi bí ẩn, nhịp nói chậm rãi. Khi đọc thường nhấn mạnh vào các đoạn nói về hậu quả hoặc bài học của câu chuyện. Giọng mang cảm giác nghiêm túc và sâu sắc, giống như đang kể một câu chuyện nhân sinh để người nghe tự rút ra bài học cho mình."},
    {"title": "Giọng Nam Miền Trung Trầm Đạo Lý",
     "description": "Giọng nam miền Trung, phát âm đặc trưng vùng miền nhưng vẫn rõ ràng. Tông giọng trầm, nhịp nói chậm và chắc. Âm sắc mang cảm giác chân chất và thật thà của người miền Trung. Khi nói về đạo lý, giọng có sự sâu sắc tự nhiên giống như một người nông dân từng trải đang chia sẻ bài học cuộc đời."},
    {"title": "Giọng Ông Lão Miền Trung Kể Chuyện Đời",
     "description": "Giọng nam lớn tuổi miền Trung, hơi khàn và có nhịp nói chậm. Khi đọc thường có khoảng dừng giữa các câu, giống như người già đang nhớ lại những câu chuyện cũ. Âm sắc hiền hậu và chân thật, tạo cảm giác gần gũi như một ông lão đang ngồi kể chuyện đời cho người nghe."},
    {"title": "Giọng Nam Miền Nam Trầm Ấm Đạo Lý",
     "description": "Giọng nam miền Nam trầm ấm, phát âm mềm mại đặc trưng miền Nam. Nhịp nói chậm rãi và rất dễ nghe. Âm sắc mang cảm giác gần gũi và thân thiện, giống như một người chú hoặc người bác đang kể chuyện đời cho người nghe."},
    {"title": "Giọng Ông Lão Miền Nam Kể Chuyện",
     "description": "Giọng nam lớn tuổi miền Nam, hơi khàn nhẹ nhưng hiền hậu. Nhịp nói chậm và mềm. Khi đọc có cảm giác giống ông nội đang ngồi kể chuyện đời cho cháu nghe."},
    {"title": "Giọng Người Cha Miền Nam Khuyên Con",
     "description": "Giọng nam miền Nam ấm áp, nhịp nói chậm và nhẹ nhàng. Âm sắc mang cảm giác yêu thương và bao dung. Khi nghe giống như người cha đang dạy con cách sống đúng đắn."},
    {"title": "Giọng Kể Chuyện Nhân Quả Miền Nam",
     "description": "Giọng nam miền Nam trầm và có chút bí ẩn. Nhịp nói chậm và rõ ràng. Khi nghe giống như một người đang kể câu chuyện nhân sinh để người nghe tự suy ngẫm."},
]


# ── Helpers ─────────────────────────────────────────────────────────

def _get_api_keys() -> list[str]:
    """Đọc danh sách Gemini API key từ file."""
    keys: list[str] = []
    try:
        if os.path.isfile(GEMINI_KEYS_PATH):
            with open(GEMINI_KEYS_PATH, "r", encoding="utf-8") as f:
                keys = [ln.strip() for ln in f.read().splitlines() if ln.strip()]
    except Exception:
        pass
    return keys


# ── API key helpers ────────────────────────────────────────────────

def get_available_keys() -> list[str]:
    """Trả về tất cả API key từ file."""
    return _get_api_keys()


def _pick_api_key() -> str:
    """Chọn ngẫu nhiên 1 API key."""
    keys = _get_api_keys()
    if not keys:
        raise RuntimeError("Chưa thêm Gemini API key nào. Vui lòng thêm key vào file gemini_api_key.txt")
    return random.choice(keys)


def _remove_api_key(key_to_remove: str, log_fn=None) -> None:
    """Xóa 1 API key khỏi file gemini_api_key.txt."""
    try:
        if not os.path.isfile(GEMINI_KEYS_PATH):
            return
        with open(GEMINI_KEYS_PATH, "r", encoding="utf-8") as f:
            lines = f.read().splitlines()
        remaining = [ln for ln in lines if ln.strip() and ln.strip() != key_to_remove.strip()]
        with open(GEMINI_KEYS_PATH, "w", encoding="utf-8") as f:
            f.write("\n".join(remaining))
            if remaining:
                f.write("\n")
        if log_fn:
            log_fn(f"🗑️ Đã xóa API key không hợp lệ: {key_to_remove[:8]}...")
    except Exception as e:
        if log_fn:
            log_fn(f"⚠️ Không thể xóa API key: {e}")


# ── API Key Manager (thread-safe) ──────────────────────────────

class ApiKeyManager:
    """
    Quản lý trạng thái API key tập trung, thread-safe.
    Key có 3 trạng thái: OK, QUOTA (đã hết quota), INVALID (đã xóa).
    Hỗ trợ reserve/release để phân key đều cho nhiều luồng.
    """
    def __init__(self):
        self._lock = threading.Lock()
        self._key_status: dict[str, str] = {}  # key -> "ok" | "quota" | "invalid"
        self._key_usage: dict[str, int] = {}   # key -> số luồng đang dùng
        self._round_robin_idx: int = 0

    def reload_keys(self):
        """Tải lại danh sách key từ file, giữ lại trạng thái của key cũ."""
        with self._lock:
            all_keys = _get_api_keys()
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

    def get_all_keys_with_status(self) -> dict[str, str]:
        """Trả về toàn bộ key và trạng thái."""
        with self._lock:
            return dict(self._key_status)

    def get_next_key(self) -> str | None:
        """Lấy key tiếp theo (round-robin) trong số key còn ok.
        Trả về None nếu không còn key nào."""
        with self._lock:
            ok_keys = [k for k, s in self._key_status.items() if s == "ok"]
            if not ok_keys:
                return None
            idx = self._round_robin_idx % len(ok_keys)
            self._round_robin_idx = idx + 1
            return ok_keys[idx]

    def reserve_key(self, preferred: str = "") -> str | None:
        """
        Reserve 1 key cho luồng hiện tại.
        - Nếu preferred hợp lệ (ok) → ưu tiên dùng nó.
        - Nếu không → lấy key ok + ít luồng dùng nhất (load balancing).
        Tự động +1 usage. Caller PHẢI gọi release_key() khi xong.
        Trả về None nếu không còn key nào.
        """
        with self._lock:
            ok_keys = [k for k, s in self._key_status.items() if s == "ok"]
            if not ok_keys:
                return None

            # Nếu có preferred và nó vẫn ok → dùng nó
            if preferred and preferred in self._key_status and self._key_status[preferred] == "ok":
                chosen = preferred
            else:
                # Sắp xếp theo usage tăng dần → lấy key ít luồng dùng nhất
                ok_keys.sort(key=lambda k: self._key_usage.get(k, 0))
                chosen = ok_keys[0]

            self._key_usage[chosen] = self._key_usage.get(chosen, 0) + 1
            return chosen

    def release_key(self, key: str):
        """Giải phóng key, giảm 1 usage. Gọi sau khi xong hoặc khi key lỗi."""
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
        """Đánh dấu key không hợp lệ và xóa khỏi file."""
        with self._lock:
            if key in self._key_status:
                self._key_status[key] = "invalid"
        # Xóa khỏi file (ngoài lock để tránh deadlock)
        _remove_api_key(key, log_fn=log_fn)

    def reset(self):
        """Reset toàn bộ trạng thái về OK (dùng khi bắt đầu batch mới)."""
        with self._lock:
            for k in self._key_status:
                if self._key_status[k] == "quota":  # chỉ reset quota, không reset invalid
                    self._key_status[k] = "ok"
            # Reset usage về 0
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
        """Trả về thông tin usage để debug."""
        with self._lock:
            parts = []
            for k, s in self._key_status.items():
                usage = self._key_usage.get(k, 0)
                parts.append(f"{k[:8]}...[{s}|{usage}]")
            return ", ".join(parts)


# Singleton
key_manager = ApiKeyManager()



def _file_to_base64(file_path: str) -> tuple[str, str]:
    """Đọc file và trả về (base64_data, mime_type)."""
    ext = Path(file_path).suffix.lower()
    mime_map = {
        ".mp4": "video/mp4",
        ".avi": "video/x-msvideo",
        ".mov": "video/quicktime",
        ".mkv": "video/x-matroska",
        ".webm": "video/webm",
        ".png": "image/png",
        ".jpg": "image/jpeg",
        ".jpeg": "image/jpeg",
        ".gif": "image/gif",
        ".webp": "image/webp",
    }
    mime = mime_map.get(ext, "application/octet-stream")
    with open(file_path, "rb") as f:
        data = base64.standard_b64encode(f.read()).decode("utf-8")
    return data, mime


def _bytes_to_base64(data: bytes, mime: str) -> str:
    return base64.standard_b64encode(data).decode("utf-8")


def _get_video_duration(video_path: str) -> float | None:
    """Lấy thời lượng video (giây) bằng ffprobe. Trả None nếu không lấy được."""
    try:
        cmd = [
            "ffprobe", "-v", "error",
            "-show_entries", "format=duration",
            "-of", "default=noprint_wrappers=1:nokey=1",
            video_path,
        ]
        result = subprocess.run(
            cmd, capture_output=True, text=True, timeout=30,
            creationflags=subprocess.CREATE_NO_WINDOW if os.name == "nt" else 0,
        )
        if result.returncode == 0 and result.stdout.strip():
            return float(result.stdout.strip())
    except Exception:
        pass
    return None


# ── Kiểu dữ liệu kết quả ──────────────────────────────────────────

class SocialPlatformContent:
    def __init__(self, title: str = "", content: str = "", hashtags: str = ""):
        self.title = title
        self.content = content
        self.hashtags = hashtags

    def to_dict(self) -> dict:
        return {"title": self.title, "content": self.content, "hashtags": self.hashtags}


class SocialContent:
    def __init__(self, facebook=None, youtube=None, tiktok=None):
        self.facebook = facebook or SocialPlatformContent()
        self.youtube = youtube or SocialPlatformContent()
        self.tiktok = tiktok or SocialPlatformContent()

    def to_dict(self) -> dict:
        return {
            "facebook": self.facebook.to_dict(),
            "youtube": self.youtube.to_dict(),
            "tiktok": self.tiktok.to_dict(),
        }


class AnalyzedScene:
    def __init__(self, scene_number: int = 0, image_prompt: str = "", veo_prompt: str = ""):
        self.scene_number = scene_number
        self.image_prompt = image_prompt
        self.veo_prompt = veo_prompt

    def to_dict(self) -> dict:
        return {
            "scene_number": self.scene_number,
            "image_prompt": self.image_prompt,
            "veo_prompt": self.veo_prompt,
        }


class ViralAnalysisResult:
    def __init__(self, scenes: list[AnalyzedScene] | None = None, social_content: SocialContent | None = None, characters: list[dict] | None = None, vietnamese_script: str = ""):
        self.scenes = scenes or []
        self.social_content = social_content or SocialContent()
        self.characters = characters or []
        self.vietnamese_script = vietnamese_script


# ── API chính: Phân tích video VEO3 ────────────────────────────────

def analyze_video_for_viral_script(
    video_path: str,
    target_duration: str = "",
    language: str = "vi",
    voice_description: str = "",
    reference_image_paths: list[str] | None = None,
    log_callback=None,
    api_key: str = "",
    style: str = "",
    stop_check_fn=None,
    custom_instruction: str = "",
    lock_scene_count: bool = True,
    character_names: list[str] | None = None,
    ref_image_names: list[str] | None = None,
) -> ViralAnalysisResult:
    """
    Phân tích video và tạo prompt ảnh + prompt video VEO3.

    Args:
        video_path: Đường dẫn tới file video.
        target_duration: Chiều dài video tái tạo (VD: "60s", "30s").
        language: Ngôn ngữ output ("vi" hoặc "en").
        voice_description: Mô tả giọng đọc.
        reference_image_paths: Danh sách đường dẫn ảnh tham chiếu nhân vật.
        log_callback: Hàm callback để log (nếu có).
        api_key: API key cụ thể (nếu trống sẽ tự chọn).
    """
    try:
        from google import genai
        from google.genai import types
    except ImportError:
        raise RuntimeError("Thư viện google-genai chưa được cài đặt. Chạy: pip install google-genai")

    if reference_image_paths is None:
        reference_image_paths = []
    if ref_image_names is None:
        ref_image_names = []

    def _log(msg: str):
        if log_callback:
            try:
                log_callback(msg)
            except Exception:
                pass
        logger.info(msg)

    def _check_stop():
        """Kiểm tra nếu người dùng yêu cầu dừng."""
        if stop_check_fn and stop_check_fn():
            raise StopRequested("Người dùng đã yêu cầu dừng phân tích.")

    _log("Bắt đầu phân tích video...")
    _check_stop()

    # Sử dụng ApiKeyManager để quản lý key
    key_manager.reload_keys()
    if api_key:
        # Nếu chỉ định key cụ thể → dùng key đó trước
        preferred_key = api_key
    else:
        preferred_key = None

    if not key_manager.has_available_keys():
        raise RuntimeError("Chưa thêm Gemini API key nào. Vui lòng thêm key vào file gemini_api_key.txt")

    lang_instruction = "VIETNAMESE" if language == "vi" else "ENGLISH"

    # ── System instruction ──
    # Khi có ảnh tham chiếu, đặt lệnh cấm mô tả nhân vật ở ĐẦU TIÊN
    _ref_pre_instruction = ""
    if reference_image_paths:
        # Xây dựng danh sách mapping ảnh → nhân vật
        _ref_char_list = []
        for i, img_path in enumerate(reference_image_paths):
            name = ref_image_names[i] if i < len(ref_image_names) else f"character_{i+1}"
            _ref_char_list.append(name)
        _ref_names_str = ", ".join([f'"{n}"' for n in _ref_char_list])
        _ref_pre_instruction = (
            "BEFORE ANYTHING ELSE - READ THIS FIRST:\n"
            f"Reference images are provided for SPECIFIC character(s): {_ref_names_str}.\n"
            "For ONLY these characters, you are ABSOLUTELY FORBIDDEN from describing their appearance. "
            "Write ONLY: [label] (character taken from reference image). "
            "For ALL OTHER characters (those WITHOUT reference images), you MUST describe them in full detail as usual "
            "(age, clothing, hair, appearance, etc.).\n\n"
        )
    system_instruction = f"""{_ref_pre_instruction}You are an expert shot-by-shot film analyst and a master prompt engineer for the Google Veo 3 video generation model. Your task is to analyze the input video and generate a series of hyper-detailed, professional prompts in {lang_instruction} that can be used to precisely recreate the video.

CRITICAL RULES FOR VEO 3:
1.  **Scene-by-Scene Analysis (8 Seconds per Scene):** Break down the video into distinct scenes. IMPORTANT: Veo 3 generates exactly 8 seconds of video per prompt. You MUST pace the action and dialogue so that it fits perfectly within an 8-second window. If a scene in the original video is longer, break it down into multiple 8-second prompts.
2.  **Dialogue & Pacing:** If there is spoken dialogue, transcribe it VERBATIM and enclose it in double quotes.
    *   **Crucial Timing:** The dialogue must be spoken at a natural, appropriate speed so no words or sentences are cut off within the 8-second limit.
    *   **Natural Pauses:** Explicitly instruct the model to pause at natural resting points (commas, periods) to ensure the speech sounds natural and fits the 8-second timeframe perfectly. Do not cram too much dialogue into a single 8-second scene.
3.  **Meticulous Description (CRITICAL FOR CAMERA & ACTION):** The prompt must be a masterclass in detail. Describe EVERYTHING with extreme precision:
    *   **Subject Action:** Describe exactly what the subject is doing. Break down complex movements into specific micro-actions (e.g., instead of "he walks", use "he strides purposefully forward, arms swinging slightly, eyes fixed on the horizon"). Describe the speed, weight, and emotion of the movement.
    *   **Camera Movement & Angle:** This is paramount. You MUST explicitly define the camera's behavior. Use professional cinematography terms:
        *   *Movement:* Pan (left/right), Tilt (up/down), Dolly (in/out), Tracking (following subject), Crane shot, Handheld (shaky), Steadicam (smooth), Zoom (in/out). Describe the *speed* of the movement (e.g., "slow, creeping dolly in", "whip pan to the right").
        *   *Angle/Shot Size:* Extreme Close-Up (ECU), Close-Up (CU), Medium Shot (MS), Wide Shot (WS), Extreme Wide Shot (EWS), High Angle, Low Angle, Dutch Angle, Over-the-Shoulder (OTS), Point of View (POV).
    *   **Environment:** The background, foreground, props, and overall setting.
    *   **Lighting & Color:** Lighting (soft morning light, harsh noon sun, neon city lights), and color grading.

4.  **ACTION-HEAVY VIDEO ANALYSIS (CRITICAL):** For videos that are primarily action-driven (fights, chases, sports, physical stunts, dancing, martial arts, physical comedy, etc.) rather than dialogue-driven:
    *   **Prioritize movement over dialogue:** Focus on describing EVERY physical action in extreme detail: body mechanics, trajectory, speed, impact, reaction.
    *   **Micro-action breakdown:** Break complex actions into sequential micro-movements. Example: Instead of "he punches", write "he shifts weight to his back foot, coils his right arm, then explosively drives a right cross forward, fist rotating at the last moment, connecting with a sharp impact". 
    *   **Speed and rhythm:** Explicitly state the tempo of actions: "rapid succession", "in slow motion", "sudden burst of speed", "rhythmic and flowing", "explosive and jarring".
    *   **Physics and weight:** Describe how actions interact with gravity and momentum: "the impact sends him sliding back 2 meters", "she leaps upward, hair trailing behind her, suspension at the peak for a beat".
    *   **Facial expressions during action:** Even in fast action, describe facial expressions: "gritted teeth", "eyes wide with determination", "a confident smirk as she dodges".
    *   **Sound design for action:** Include sound cues in veo_prompt: "the whoosh of a fast swing", "a heavy thud on impact", "the crunch of gravel under rapid footsteps".
    *   **Scene pacing for action:** Action scenes may need MORE scenes (shorter, faster cuts) to capture rapid sequences. Do NOT try to cram too many actions into a single 8-second scene. If the action is fast-paced, use more scenes with fewer actions per scene.

5.  **Language:** All output prompts must be in **{lang_instruction}**.
6.  **Output Format:** The final output must be a valid JSON object. You MUST include ALL of the following top-level keys (REQUIRED, do NOT omit any):
    - **"characters"** (REQUIRED): an array of character objects, each with "label" (the fixed name/label used in prompts, e.g. "the wise old man", "the young girl in red dress") and "description" (brief physical description of that character).
    - **"vietnamese_script"** (REQUIRED): a complete Vietnamese screenplay/script of the video, written as a single string. Write scene by scene. Each scene includes: scene number, setting description, character actions, dialogue (if any), and narration. This script must capture the full story and all details in Vietnamese.
    - **"scenes"** (REQUIRED): an array of scene objects with "scene_number", "image_prompt", "veo_prompt".
    - **"social_content"** (REQUIRED): an object containing content for facebook, youtube, and tiktok.
    
    Example JSON structure (follow this EXACTLY):
    {{"characters": [{{"label": "the wise old man", "description": "An elderly man with long white beard, wearing brown robe"}}], "vietnamese_script": "Cảnh 1: Ông lão ngồi dưới gốc cây...\nCảnh 2: ...", "scenes": [{{"scene_number": 1, "image_prompt": "...", "veo_prompt": "..."}}], "social_content": {{"facebook": {{"title": "...", "content": "...", "hashtags": "..."}}, "youtube": {{"title": "...", "content": "...", "hashtags": "..."}}, "tiktok": {{"title": "...", "content": "...", "hashtags": "..."}}}}}}
    
    Do not include any explanatory text, markdown code blocks, or anything outside of the JSON object.
7.  **Social Content (ALWAYS IN VIETNAMESE):** Generate social media content for Facebook, YouTube, and TikTok. **ALL social content (title, content, hashtags) MUST be written in VIETNAMESE regardless of the language setting above.** Follow these rules:
    *   **Title (Hook cực mạnh):** The title MUST be a powerful, curiosity-driven hook that makes viewers desperately want to click and watch. Use emotional triggers, mystery, controversy, or shocking statements. Examples: "Ai ngờ đằng sau nụ cười hiền lành lại là...", "99% người xem không nhịn được nước mắt khi thấy cảnh này", "Đừng bao giờ làm điều này nếu bạn không muốn hối hận cả đời". The title must create an irresistible urge to watch.
    *   **Content (Hook + Story):** Start with a hook sentence that grabs attention in the first line. Then briefly tell the story/message of the video in a way that builds curiosity but does NOT reveal everything — leave a reason for viewers to watch the full video. Use emotional language, rhetorical questions, or dramatic statements.
    *   **Hashtags:** Use trending Vietnamese hashtags relevant to the video topic. Mix popular broad hashtags with specific niche ones.

**CHARACTER ANALYSIS (CRITICAL - MUST FOLLOW EXACTLY):**
*   **Step 1 - Identify All Characters:** First, identify ALL characters (people, animals, creatures) that appear in the video. For each character, assign a **fixed, consistent label** based on their most prominent trait (e.g., "the old man", "the young girl in red dress", "the black cat", "the bearded farmer"). This label MUST remain the SAME across ALL scenes in BOTH `image_prompt` AND `veo_prompt`.
*   **Step 2 - Character in EVERY Scene:** For EVERY scene where a character appears, you MUST mention them by their assigned label in BOTH the `image_prompt` AND the `veo_prompt`. Do NOT describe a scene with only environment/camera — if a character is present, they MUST be named and described (what they are doing, their expression, posture, position in the frame).
*   **Step 3 - ABSOLUTE NAME CONSISTENCY (CRITICAL):** 
    - The EXACT label string used in the "characters" array's "label" field MUST appear VERBATIM (character-for-character, word-for-word) in EVERY `image_prompt` and `veo_prompt` where that character appears.
    - Do NOT add extra words, descriptions, or modifiers to the label when using it in prompts. If the label is "the old man", write exactly "the old man" — NOT "the wise old man", NOT "the elderly old man", NOT "old man".
    - Do NOT use synonyms, alternative names, shortened names, or any variation of the label. The label must be COPIED EXACTLY.
    - Do NOT switch labels between scenes. If character A is labeled "the old man" in scene 1, they MUST be "the old man" in ALL subsequent scenes.
    - The label in the "characters" array is the GROUND TRUTH. Every occurrence in image_prompt and veo_prompt must match it EXACTLY.

*   **Step 4 - MANDATORY CHARACTER PRESENCE ENFORCEMENT (CRITICAL):**
    - EVERY `image_prompt` MUST START with the character label(s) present in that scene. The character label must be the FIRST element of the prompt, before any environment, camera, or action description.
    - EVERY `veo_prompt` MUST START with the character label(s) present in that scene.
    - If MULTIPLE characters appear in a scene, list ALL of them at the beginning.
    - A prompt that describes only environment/camera WITHOUT naming any character is INVALID and FORBIDDEN.
    - Example CORRECT: "the old man carefully places a pot on the stove. Medium shot, warm kitchen background."
    - Example WRONG: "Medium shot of a warm kitchen. A pot is placed on the stove." (NO character named!)
    - Example WRONG: "The scene shows a busy market with vendors selling fruit." (NO character named!)
    - For scenes with ONLY environment (no character visible), you may describe environment only, but this should be RARE.
"""

    if reference_image_paths:
        # Xây dựng mapping ảnh → tên nhân vật
        _ref_mapping_lines = []
        for i, img_path in enumerate(reference_image_paths):
            name = ref_image_names[i] if i < len(ref_image_names) else f"character_{i+1}"
            _ref_mapping_lines.append(f"  - Reference image #{i+1} → character: \"{name}\"")
        _ref_mapping_str = "\n".join(_ref_mapping_lines)
        _ref_names_for_prompt = [ref_image_names[i] if i < len(ref_image_names) else f"character_{i+1}" for i in range(len(reference_image_paths))]
        _ref_names_quoted = ", ".join([f'"{n}"' for n in _ref_names_for_prompt])

        system_instruction += f"""
**CHARACTER DESCRIPTION RULE (REFERENCE IMAGES PROVIDED - SELECTIVE):**
The user has provided reference images for SPECIFIC character(s). Here is the mapping:
{_ref_mapping_str}

Characters WITH reference images: {_ref_names_quoted}

**FOR CHARACTERS WITH REFERENCE IMAGES ({_ref_names_quoted}):**
- RULE #1 - ZERO APPEARANCE DESCRIPTION: You MUST NOT describe ANY aspect of their physical appearance (hair, clothing, age, skin, accessories) in `image_prompt` or `veo_prompt`.
- RULE #2 - CORRECT FORMAT: Write ONLY their label followed by "(character taken from reference image)". Then describe ONLY actions, environment, camera.
  ✅ CORRECT: "[label] (character taken from reference image) carefully places a pot on the stove. Medium shot."
  ❌ WRONG: "[label] (brown hair, blue dress) places a pot..."
- RULE #3 - In the "characters" array, set their "description" to "Character taken from reference image".

**FOR ALL OTHER CHARACTERS (those WITHOUT reference images):**
- You MUST describe them with EXTREME detail so an image model can recreate them exactly:
  - For humans: face shape, skin tone, eye shape/color, nose, lips, hair (color, length, style, texture), body build, height impression, age, clothing (type, exact color, material, patterns, fit), accessories, footwear
  - For animals: species, breed, size, fur/skin color and pattern, fur texture, distinctive features (ear shape, tail, collar, etc.)
- Assign them a fixed, descriptive label and use it consistently across ALL scenes.
- Include FULL description in parentheses in every `image_prompt`.
- Example human: \"the elderly fisherman (a weathered man around 65, dark tanned skin, deep wrinkles around eyes, square jaw, short silver-grey hair, thick grey eyebrows, wearing a faded navy blue cotton vest over a white undershirt, rolled-up khaki trousers, brown leather sandals, a worn straw hat) casts his net...\"
- Example animal: \"the playful Shiba Inu (a medium-sized dog with fluffy golden-brown and white fur, pointed ears, curly tail, bright dark eyes, small black nose, wearing a red collar with a bell) runs excitedly...\"

**CRITICAL DISTINCTION:**
- If a character matches one of the reference image characters ({_ref_names_quoted}), use "(character taken from reference image)" - NO appearance description.
- If a character does NOT match any reference image character, describe them in FULL detail - hair, clothing, age, everything.
- Do NOT apply the reference image rule to characters that don't have reference images.

**OVERRIDE ORIGINAL VIDEO (for referenced characters only):**
Even if the original video shows different clothing/hair for referenced characters, do NOT describe them. The reference image is the ONLY source of truth for those characters."""

    else:
        system_instruction += """
**CHARACTER DESCRIPTION RULE (NO REFERENCE IMAGES - ULTRA-DETAILED):**
Since no reference images are provided, you MUST describe each character with EXTREME, HYPER-DETAILED precision so that an image/video generation model can recreate them EXACTLY. Follow this checklist for EVERY character:

**1. FACE & HEAD (MANDATORY for every human character):**
   - Face shape (oval, round, square, heart-shaped, angular, etc.)
   - Skin tone (pale, fair, light tan, olive, brown, dark brown, etc.)
   - Eyes: shape (almond, round, hooded, monolid), color (dark brown, hazel, blue, etc.), size, any distinctive features (thick eyelashes, tired eyes, bright eyes)
   - Nose: shape (small, button, straight, aquiline, wide, pointed)
   - Lips: shape (thin, full, heart-shaped), color
   - Eyebrows: shape (thick, thin, arched, straight), color
   - Facial hair (if any): beard, mustache, stubble - style and color
   - Other facial features: freckles, moles, dimples, wrinkles, scars, glasses
   - Expression/mood in this specific scene

**2. HAIR (MANDATORY):**
   - Color (jet black, dark brown, chestnut, auburn, blonde, silver-white, etc.)
   - Length (very short, short, shoulder-length, long, very long)
   - Style (straight, wavy, curly, braided, ponytail, messy bun, loose, tied back, etc.)
   - Texture (silky, coarse, thick, thin, fluffy)
   - Bangs/fringe (if any)

**3. BODY & BUILD (MANDATORY):**
   - Gender and approximate age (e.g., "a woman in her mid-20s", "an elderly man around 70")
   - Height impression (tall, average, short, petite)
   - Build (slim, slender, athletic, average, stocky, heavyset, muscular)
   - Posture and body language in this scene

**4. CLOTHING & ACCESSORIES (MANDATORY - VERY DETAILED):**
   - Top: type (t-shirt, blouse, sweater, jacket, coat, dress), exact color, material/texture (cotton, silk, denim, linen, wool), patterns (solid, striped, floral, plaid, polka dot), fit (loose, fitted, oversized)
   - Bottom: type (jeans, skirt, shorts, trousers), exact color, style
   - Footwear: type (sneakers, boots, sandals, barefoot), color
   - Accessories: hat, glasses, jewelry (necklace, earrings, bracelet), bags, scarves, watches
   - Special details: rolled-up sleeves, tucked-in shirt, open collar, buttons, zippers, logos

**5. FOR ANIMALS/CREATURES:**
   - Species and breed (e.g., "a golden retriever", "a fluffy orange tabby cat", "a Shiba Inu")
   - Size (small, medium, large)
   - Fur/skin color and pattern (solid, spotted, striped, bicolor)
   - Fur texture (fluffy, smooth, wiry, curly)
   - Distinctive features (floppy ears, curly tail, blue eyes, collar)

**6. CONSISTENCY RULES:**
   - Assign a fixed, descriptive label (e.g., "the young woman with wavy chestnut hair in a white linen dress")
   - Use this EXACT label in ALL scenes, in BOTH `image_prompt` AND `veo_prompt`
   - Include the FULL character description in parentheses after the label in EVERY `image_prompt`
   - In `veo_prompt`, include key appearance details + focus on actions/movements

**7. EXAMPLE (FOLLOW THIS LEVEL OF DETAIL):**
   image_prompt: "the young woman with wavy chestnut hair (a slender woman in her mid-20s, fair skin with light freckles across her nose, oval face, large almond-shaped dark brown eyes with thick lashes, small nose, full pink lips, wavy chestnut-brown hair falling to mid-back, wearing a fitted light blue linen sundress with thin white straps, a delicate gold necklace with a small pendant, white canvas sneakers) stands in a sunlit kitchen, smiling warmly, medium shot, eye level."
   veo_prompt: "the young woman with wavy chestnut hair (mid-20s, fair skin, wavy chestnut hair, light blue linen sundress, gold necklace) carefully lifts a steaming pot from the wood-fired stove, her expression focused, steam rising around her face. Camera: medium shot, slightly low angle, warm golden lighting."
"""

    # Tính số cảnh: mỗi cảnh 8s
    _total_seconds = None

    if target_duration:
        # Người dùng đã cấu hình chiều dài đầu ra
        import re as _re
        _dur_match = _re.search(r'(\d+)', str(target_duration))
        if _dur_match:
            _total_seconds = int(_dur_match.group(1))

    if lock_scene_count:
        # ── Chế độ KHÓA số cảnh theo thời gian ──
        if _total_seconds and _total_seconds > 0:
            # Công thức: ceil(duration / 8)
            _num_scenes = math.ceil(_total_seconds / 8)
            _actual_duration = _num_scenes * 8
            system_instruction += f"""
**TARGET DURATION:** The total recreated video must be exactly {_actual_duration} seconds long ({_num_scenes} scenes × 8 seconds each). You MUST generate EXACTLY {_num_scenes} scenes, no more, no less. Each scene is exactly 8 seconds. Pace the action, dialogue, and camera movements so that the total content fits perfectly into {_num_scenes} scenes. Break dialogue at natural pauses (commas, periods, sentence boundaries) to ensure each scene's speech fits naturally within 8 seconds."""
        else:
            system_instruction += """
**TARGET DURATION (AUTO-DETECT, LOCKED TO VIDEO DURATION):** The user has NOT specified a target duration. You MUST determine the exact duration of the input video yourself. Then calculate the number of scenes using this formula: number_of_scenes = ceil(video_duration_in_seconds / 8). Each scene is exactly 8 seconds. For example: 30s video → ceil(30/8) = 4 scenes, 32s → 4 scenes, 50s → ceil(50/8) = 7 scenes. You MUST generate EXACTLY that number of scenes. Pace the action, dialogue, and camera movements so that the total content fits perfectly. Break dialogue at natural pauses (commas, periods, sentence boundaries) to ensure each scene's speech fits naturally within 8 seconds."""
    else:
        # ── Chế độ AI TỰ QUYẾT ĐỊNH số cảnh ──
        _hint_seconds = ""
        if _total_seconds and _total_seconds > 0:
            _hint_seconds = f" The original video is approximately {_total_seconds} seconds long."
        system_instruction += f"""
**SCENE COUNT (AI-DETERMINED, FLEXIBLE):** The user has chosen to let you decide the optimal number of scenes.{_hint_seconds} Each scene is exactly 8 seconds of generated video.
You are FREE to determine the best number of scenes based on the video's CONTENT, not strictly its duration. Follow these guidelines:
- **Dialogue-heavy videos:** Match the scene count roughly to the video duration (ceil(duration/8)) since dialogue pacing matters.
- **Action-heavy videos:** Use MORE scenes if needed to capture fast-paced action sequences properly. Do NOT compress multiple distinct actions into one scene. Each significant action beat should get its own scene.
- **Slow/contemplative videos:** You may use FEWER scenes if the video has long static shots or slow pacing.
- **Mixed content:** Adapt scene count to ensure both dialogue and action are properly represented.
The key principle: Generate as many scenes as needed to faithfully recreate the video's content. Quality and completeness over arbitrary scene count limits."""

    if voice_description:
        system_instruction += f"""
**VOICEOVER INSTRUCTION:** The user has requested a specific voiceover style. You MUST include this exact description in the prompt for any scene that contains dialogue or voiceover: "{voice_description}" """

    if style:
        system_instruction += f"""
**VISUAL STYLE INSTRUCTION (CRITICAL - USER SELECTED):** The user has explicitly selected a visual style. You MUST use EXACTLY this style description and include it VERBATIM in EVERY `image_prompt` AND EVERY `veo_prompt` for ALL scenes. Do NOT analyze or detect the visual style from the original video — IGNORE the original video's style completely. Instead, apply this exact style to every prompt:

\"{style}\"

Every `image_prompt` and `veo_prompt` MUST contain the full style description above. Do NOT shorten, summarize, or paraphrase it. Copy the style description into each prompt."""
    else:
        system_instruction += """
**VISUAL STYLE INSTRUCTION (AUTO-DETECT):** The user has NOT selected a specific visual style. You MUST carefully analyze the original video's visual style (animation type, rendering, color palette, lighting, camera style, etc.) and describe it in detail. Then include this detected style description in EVERY `image_prompt` AND EVERY `veo_prompt` for ALL scenes, so the recreated video matches the original's visual style as closely as possible."""

    # ── Nhân vật: yêu cầu nhất quán tên ──
    if character_names:
        _char_names_str = ", ".join([f'"{n}"' for n in character_names if n.strip()])
        system_instruction += f"""

**CHARACTER NAMING (CRITICAL - USER-DEFINED NAMES):**
The user has defined the following character names: {_char_names_str}.
You MUST follow these rules strictly:
1.  **Use EXACT names:** When referring to characters in `image_prompt`, `veo_prompt`, and `vietnamese_script`, you MUST use the EXACT names provided above. Do NOT invent new names or labels for characters that match these defined characters.
2.  **Match characters to names:** Analyze the video to identify which character corresponds to which user-defined name. If the video has 2 characters and the user defined 2 names, assign each name to the correct character based on context.
3.  **Consistent across ALL scenes:** The SAME character must ALWAYS be referred to by the SAME user-defined name in ALL scenes, in ALL prompts (image_prompt, veo_prompt), and in the vietnamese_script. 
4.  **Characters list:** In the "characters" array output, use the user-defined name as the "label" field.
5.  **Example:** If user defined names "Minh" and "Lan", and the video shows a man and a woman, assign "Minh" to the man and "Lan" to the woman. Then in ALL scenes, refer to them as "Minh" and "Lan" consistently."""

    if custom_instruction:
        system_instruction += f"""

**HIGHEST PRIORITY - USER CUSTOM INSTRUCTION (MUST OVERRIDE ALL PREVIOUS RULES IF CONFLICT):**
The user has provided a special instruction that takes the HIGHEST priority. If this instruction conflicts with ANY rule above (character description, visual style, script content, scene structure, etc.), you MUST follow THIS instruction and IGNORE the conflicting rule. Apply this instruction to ALL scenes, ALL prompts (image_prompt, veo_prompt), the vietnamese_script, and the characters list.

User instruction:
\"{custom_instruction}\"

You MUST strictly follow this instruction. Modify characters, scenes, dialogue, actions, and any other element as needed to fulfill this instruction completely."""

    # ── Chuẩn bị contents ──
    _check_stop()
    _log("Đang upload video lên Gemini...")
    video_data, video_mime = _file_to_base64(video_path)
    parts = [
        types.Part.from_bytes(data=base64.standard_b64decode(video_data), mime_type=video_mime),
    ]
    _log(f"✅ Đã upload video xong ({os.path.basename(video_path)})")

    # Thêm ảnh tham chiếu nếu có
    if reference_image_paths:
        _log(f"📷 Đang upload {len(reference_image_paths)} ảnh tham chiếu nhân vật...")
    for i, img_path in enumerate(reference_image_paths):
        try:
            img_data, img_mime = _file_to_base64(img_path)
            parts.append(types.Part.from_bytes(data=base64.standard_b64decode(img_data), mime_type=img_mime))
            char_name = ref_image_names[i] if i < len(ref_image_names) else f"character_{i+1}"
            _log(f"  ✅ Đã upload ảnh nhân vật \"{char_name}\": {os.path.basename(img_path)}")
        except Exception as e:
            _log(f"  ❌ Không thể đọc ảnh tham chiếu {img_path}: {e}")

    # Thêm text instruction vào user content (trọng lượng cao hơn system instruction)
    if reference_image_paths:
        # Xây dựng mapping text cho user content
        _mapping_parts = []
        for i in range(len(reference_image_paths)):
            name = ref_image_names[i] if i < len(ref_image_names) else f"character_{i+1}"
            _mapping_parts.append(f"Image #{i+1} = \"{name}\"")
        _mapping_text = ", ".join(_mapping_parts)
        _ref_names_list = [ref_image_names[i] if i < len(ref_image_names) else f"character_{i+1}" for i in range(len(reference_image_paths))]
        _ref_names_text = ", ".join([f'"{n}"' for n in _ref_names_list])

        parts.append(types.Part.from_text(text=
            f"CRITICAL REMINDER: The images above are CHARACTER REFERENCE IMAGES. Mapping: {_mapping_text}. "
            f"ONLY characters matching {_ref_names_text} should use '(character taken from reference image)' - do NOT describe their appearance. "
            "For ALL OTHER characters (animals, objects, people without reference images), describe them in FULL detail as usual. "
            f"Example CORRECT for referenced character: '{_ref_names_list[0]} (character taken from reference image) carefully places a pot on the stove.' "
            "Example CORRECT for non-referenced character: 'the small brown dog (a fluffy Shiba Inu with golden-brown fur) trots happily alongside.' "
            "Do NOT apply the reference image rule to characters without reference images."
        ))

    # ── Response schema ──
    social_platform_schema = types.Schema(
        type=types.Type.OBJECT,
        properties={
            "title": types.Schema(type=types.Type.STRING),
            "content": types.Schema(type=types.Type.STRING),
            "hashtags": types.Schema(type=types.Type.STRING),
        },
        required=["title", "content", "hashtags"],
    )

    response_schema = types.Schema(
        type=types.Type.OBJECT,
        properties={
            "characters": types.Schema(
                type=types.Type.ARRAY,
                items=types.Schema(
                    type=types.Type.OBJECT,
                    properties={
                        "label": types.Schema(
                            type=types.Type.STRING,
                            description="The fixed, consistent label/name for this character used across all scenes (e.g. 'the wise old man', 'the young girl in red dress').",
                        ),
                        "description": types.Schema(
                            type=types.Type.STRING,
                            description="Brief physical description of the character: age, appearance, clothing, distinguishing features.",
                        ),
                    },
                    required=["label", "description"],
                ),
            ),
            "vietnamese_script": types.Schema(
                type=types.Type.STRING,
                description="Complete Vietnamese screenplay/script of the video, written scene by scene. Each scene includes: scene number, setting, character actions, dialogue, narration.",
            ),
            "scenes": types.Schema(
                type=types.Type.ARRAY,
                items=types.Schema(
                    type=types.Type.OBJECT,
                    properties={
                        "scene_number": types.Schema(
                            type=types.Type.INTEGER,
                            description="The sequential number of the scene.",
                        ),
                        "image_prompt": types.Schema(
                            type=types.Type.STRING,
                            description=f"A detailed, professional, {lang_instruction} prompt for an image generation model to create the starting frame of this scene.",
                        ),
                        "veo_prompt": types.Schema(
                            type=types.Type.STRING,
                            description=f"A detailed, professional, {lang_instruction} prompt for the Veo video model to recreate this specific scene, including transcribed dialogue.",
                        ),
                    },
                    required=["scene_number", "image_prompt", "veo_prompt"],
                ),
            ),
            "social_content": types.Schema(
                type=types.Type.OBJECT,
                properties={
                    "facebook": social_platform_schema,
                    "youtube": social_platform_schema,
                    "tiktok": social_platform_schema,
                },
                required=["facebook", "youtube", "tiktok"],
            ),
        },
        required=["characters", "vietnamese_script", "scenes", "social_content"],
    )

    _check_stop()
    _log("Đang gửi yêu cầu phân tích tới Gemini...")

    # Retry: reserve key từ manager (phân đều cho luồng), nếu lỗi → release + đánh dấu → reserve key mới
    last_error = None
    invalid_keywords = ["api_key_invalid", "invalid api key", "api key not valid",
                        "api key not found", "not found", "invalid", "api key expired"]
    quota_keywords = ["429", "quota", "rate", "limit", "403", "permission",
                      "exhausted", "billing", "resource_exhausted"]

    max_retries = key_manager.count_total() + 2  # giới hạn số lần thử
    attempt = 0
    current_key = None  # key đang được reserve bởi luồng này

    try:
        while attempt < max_retries:
            _check_stop()  # Check stop trước mỗi lần thử key

            # Reserve key mới (ưu tiên preferred_key lần đầu)
            if attempt == 0 and preferred_key:
                current_key = key_manager.reserve_key(preferred=preferred_key)
            else:
                current_key = key_manager.reserve_key()

            if not current_key:
                break  # Không còn key nào

            attempt += 1
            try:
                client = genai.Client(api_key=current_key)
                if attempt > 1:
                    _log(f"🔄 Thử key {attempt}: {current_key[:8]}... (còn {key_manager.count_ok()} key khả dụng)")

                # Chạy API call trong thread con (daemon) để có thể check stop
                _api_result = [None]  # [response | None]
                _api_error = [None]   # [Exception | None]
                _api_done = threading.Event()

                def _call_api():
                    try:
                        _api_result[0] = client.models.generate_content(
                            model="gemini-2.5-flash",
                            contents=types.Content(parts=parts),
                            config=types.GenerateContentConfig(
                                system_instruction=system_instruction,
                                response_mime_type="application/json",
                                response_schema=response_schema,
                            ),
                        )
                    except Exception as e:
                        _api_error[0] = e
                    finally:
                        _api_done.set()

                api_thread = threading.Thread(target=_call_api, daemon=True)
                api_thread.start()

                # Chờ API phản hồi, check stop mỗi 1 giây
                while not _api_done.is_set():
                    _api_done.wait(timeout=1.0)
                    if _api_done.is_set():
                        break
                    # Kiểm tra stop
                    if stop_check_fn and stop_check_fn():
                        _log("⛔ Đã nhận lệnh dừng, hủy chờ Gemini...")
                        raise StopRequested("Người dùng đã yêu cầu dừng phân tích.")

                # Lấy kết quả
                if _api_error[0] is not None:
                    raise _api_error[0]
                response = _api_result[0]

                _log(f"✅ Thành công với key: {current_key[:8]}...")
                # Release key sau khi thành công
                key_manager.release_key(current_key)
                current_key = None
                break  # Thành công → thoát vòng lặp
            except StopRequested:
                # Release key rồi re-raise
                key_manager.release_key(current_key)
                current_key = None
                raise
            except Exception as api_err:
                last_error = api_err
                err_str = str(api_err).lower()

                # Release key trước khi đánh dấu lỗi
                key_manager.release_key(current_key)
                released_key = current_key
                current_key = None

                # Lỗi API key invalid → đánh dấu INVALID + xóa khỏi file
                if any(kw in err_str for kw in invalid_keywords):
                    _log(f"❌ Key {released_key[:8]}... không hợp lệ, đánh dấu và xóa...")
                    key_manager.mark_invalid(released_key, log_fn=_log)
                    continue
                # Lỗi quota/rate limit → đánh dấu QUOTA
                if any(kw in err_str for kw in quota_keywords):
                    _log(f"⚠️ Key {released_key[:8]}... hết quota, đánh dấu bỏ qua...")
                    key_manager.mark_quota(released_key)
                    continue
                # Lỗi khác (network, invalid request...) → raise ngay
                raise
        else:
            # Tất cả key đều lỗi
            ok_count = key_manager.count_ok()
            total = key_manager.count_total()
            raise RuntimeError(
                f"Tất cả API key đều lỗi ({ok_count}/{total} còn khả dụng). Lỗi cuối: {last_error}"
            )
    finally:
        # Đảm bảo release key nếu bị exception bất ngờ
        if current_key:
            key_manager.release_key(current_key)

    _log("Đã nhận phản hồi từ Gemini. Đang phân tích kết quả...")

    # ── Parse response ──
    raw_text = ""
    try:
        raw_text = response.text or ""
    except Exception:
        if response.candidates and response.candidates[0].content and response.candidates[0].content.parts:
            for part in response.candidates[0].content.parts:
                if hasattr(part, "text") and part.text:
                    raw_text = part.text
                    break

    if not raw_text.strip():
        raise RuntimeError("AI trả về phản hồi trống. Vui lòng thử lại.")

    clean_json = raw_text.strip()
    if clean_json.startswith("```json"):
        clean_json = clean_json[7:]
        if clean_json.endswith("```"):
            clean_json = clean_json[:-3]
        clean_json = clean_json.strip()
    elif clean_json.startswith("```"):
        clean_json = clean_json[3:]
        if clean_json.endswith("```"):
            clean_json = clean_json[:-3]
        clean_json = clean_json.strip()

    try:
        data = json.loads(clean_json)
    except json.JSONDecodeError:
        # Thử tìm JSON object trong chuỗi
        import re
        match = re.search(r'(\{[\s\S]*\})', clean_json)
        if match:
            try:
                data = json.loads(match.group(0))
            except json.JSONDecodeError:
                raise RuntimeError("AI trả về định dạng không hợp lệ. Vui lòng thử lại.")
        else:
            raise RuntimeError("AI trả về định dạng không hợp lệ. Vui lòng thử lại.")

    # Parse thành kết quả
    scenes: list[AnalyzedScene] = []
    raw_scenes = data.get("scenes", [])
    if isinstance(raw_scenes, list):
        for s in raw_scenes:
            scenes.append(AnalyzedScene(
                scene_number=int(s.get("scene_number", 0)),
                image_prompt=str(s.get("image_prompt", "")),
                veo_prompt=str(s.get("veo_prompt", "")),
            ))

    sc_data = data.get("social_content", {})
    social = SocialContent(
        facebook=SocialPlatformContent(**sc_data.get("facebook", {})) if isinstance(sc_data.get("facebook"), dict) else SocialPlatformContent(),
        youtube=SocialPlatformContent(**sc_data.get("youtube", {})) if isinstance(sc_data.get("youtube"), dict) else SocialPlatformContent(),
        tiktok=SocialPlatformContent(**sc_data.get("tiktok", {})) if isinstance(sc_data.get("tiktok"), dict) else SocialPlatformContent(),
    )

    # Parse characters
    characters: list[dict] = []
    raw_chars = data.get("characters", [])
    if isinstance(raw_chars, list):
        for c in raw_chars:
            if isinstance(c, dict):
                characters.append({
                    "label": str(c.get("label", "")),
                    "description": str(c.get("description", "")),
                })

    # ── Post-processing: xóa mô tả ngoại hình CHỈ cho nhân vật có ảnh tham chiếu ──
    if reference_image_paths and scenes:
        _log("🔧 Post-processing: Xóa mô tả ngoại hình nhân vật có ảnh tham chiếu...")
        # Chỉ lấy label của nhân vật có ảnh tham chiếu (match theo ref_image_names)
        ref_char_names_set = set()
        for i in range(len(reference_image_paths)):
            name = ref_image_names[i] if i < len(ref_image_names) else f"character_{i+1}"
            ref_char_names_set.add(name.lower())
        # Tìm label trong characters mà match với ref_image_names
        ref_char_labels = []
        for c in characters:
            label = c.get("label", "")
            if label and label.lower() in ref_char_names_set:
                ref_char_labels.append(label)
        # Nếu không match được (Gemini tự đặt label khác), dùng tất cả ref_image_names
        if not ref_char_labels:
            ref_char_labels = list(ref_image_names) if ref_image_names else []
        if ref_char_labels:
            scenes = _strip_appearance_from_scenes(scenes, ref_char_labels, _log)

    # ── Post-processing: Validation — đảm bảo prompt có nhắc nhân vật ──
    if characters and scenes:
        char_labels_all = [c.get("label", "") for c in characters if c.get("label", "")]
        if char_labels_all:
            _log(f"🔍 Kiểm tra nhân vật trong prompt ({len(char_labels_all)} nhân vật)...")
            for scene in scenes:
                _ensure_character_in_prompt(scene, char_labels_all, _log)

    _log(f"Phân tích hoàn tất! Tìm thấy {len(scenes)} scene(s), {len(characters)} nhân vật.")
    _log(f"[DEBUG] JSON keys: {list(data.keys())}")
    vietnamese_script = str(data.get("vietnamese_script", ""))
    if not vietnamese_script:
        _log("[DEBUG] vietnamese_script KHÔNG có trong JSON response")
    if not characters:
        _log("[DEBUG] characters KHÔNG có trong JSON response")
    return ViralAnalysisResult(scenes=scenes, social_content=social, characters=characters, vietnamese_script=vietnamese_script)


def _ensure_character_in_prompt(scene, char_labels: list[str], log_fn=None):
    """
    Kiểm tra image_prompt và veo_prompt có chứa ít nhất 1 nhân vật không.
    Nếu thiếu → chèn nhân vật đầu tiên vào đầu prompt.
    Chỉ chèn nếu prompt KHÔNG rỗng (prompt rỗng = scene chỉ có môi trường).
    """
    if not char_labels:
        return

    def _find_present_chars(text: str) -> list[str]:
        """Tìm các nhân vật có mặt trong text."""
        text_lower = text.lower()
        return [lbl for lbl in char_labels if lbl.lower() in text_lower]

    def _inject_char(prompt: str, field: str) -> str:
        """Chèn nhân vật vào đầu prompt nếu thiếu."""
        if not prompt or not prompt.strip():
            return prompt
        present = _find_present_chars(prompt)
        if present:
            return prompt  # Đã có nhân vật
        # Thiếu nhân vật → chèn nhân vật đầu tiên vào đầu
        # Dùng nhân vật đầu tiên (nhân vật chính)
        main_char = char_labels[0]
        if log_fn:
            log_fn(f"   ⚠️ Scene {scene.scene_number} [{field}]: Thiếu nhân vật → chèn '{main_char}'")
        return f"{main_char} — {prompt}"

    scene.image_prompt = _inject_char(scene.image_prompt, "image_prompt")
    scene.veo_prompt = _inject_char(scene.veo_prompt, "veo_prompt")


def _strip_appearance_from_scenes(scenes: list, char_labels: list[str] = None, log_fn=None) -> list:
    """
    Post-processing: Xóa mọi mô tả ngoại hình nhân vật trong image_prompt và veo_prompt.
    Thay nội dung trong (...) chứa từ khóa ngoại hình bằng '(maintaining exact appearance from reference image)'.
    Xóa các đoạn phẩy chứa từ khóa ngoại hình ở ngoài ngoặc.
    Sau đó, tìm label nhân vật và thêm cụm reference image nếu chưa có.
    """
    import re
    if char_labels is None:
        char_labels = []

    # Từ khóa nhận diện mô tả ngoại hình (lowercase)
    _APPEARANCE_KEYWORDS = [
        # Tóc
        "hair", " bun", "ponytail", "braids", "bangs", "fringe",
        "brown hair", "black hair", "blonde", "red hair", "white hair", "gray hair", "silver hair",
        "messy bun", "loose bun", "shoulder-length", "long hair", "short hair",
        "tóc", "búi tóc", "đuôi ngựa",
        # Trang phục
        "wearing", "sleeveless", "apron", "skirt", "jeans",
        "jacket", "coat", "sweater", "hoodie", "uniform", "outfit",
        "clothes", "clothing",
        "mặc", "váy", "tạp dề", "quần",
        # Trang phục cụ thể
        "dress", "shirt", "blouse",
        # Patterns
        "pattern", "striped", "floral", "polka", "checkered", "plaid",
        # Tuổi
        "mid-20s", "mid-30s", "mid-40s",
        "years old", "year-old",
        # Da / thể hình
        "skin tone", "fair skin", "dark skin",
        # Phụ kiện
        "ribbon", "necklace", "earring", "bracelet",
        "glasses", "nơ", "ruy băng", "vòng cổ",
    ]

    _REF_PHRASE = "(character taken from reference image)"

    def _has_appearance_kw(text: str) -> bool:
        text_lower = text.lower()
        for kw in _APPEARANCE_KEYWORDS:
            if kw in text_lower:
                # Tránh false positive: "dress" trong "addressed", "address", "undressed"
                if kw == "dress":
                    # Chỉ match nếu "dress" đứng sau màu sắc hoặc là "dress" đơn lẻ
                    if re.search(r'\b\w*\s+dress\b', text_lower) or re.search(r'\bdress\b', text_lower):
                        if "address" not in text_lower and "undress" not in text_lower:
                            return True
                    continue
                if kw == "shirt":
                    if "t-shirt" in text_lower or re.search(r'\bshirt\b', text_lower):
                        return True
                    continue
                if kw == "blouse":
                    if re.search(r'\bblouse\b', text_lower):
                        return True
                    continue
                return True
        return False

    def _clean_prompt(prompt: str, scene_num: int, field: str) -> str:
        if not prompt:
            return prompt
        original = prompt

        # ── Bước 1: Thay nội dung trong (...) chứa từ khóa ngoại hình ──
        def _replace_paren(match):
            content = match.group(1)
            # Bỏ qua ngoặc ngắn (camera angles, shot types)
            if len(content) < 8:
                return match.group(0)
            # Nếu đã là reference image phrase thì giữ
            if "reference image" in content.lower():
                return match.group(0)
            if _has_appearance_kw(content):
                return _REF_PHRASE
            return match.group(0)

        prompt = re.sub(r'\(([^)]+)\)', _replace_paren, prompt)

        # ── Bước 2: Chia prompt thành các đoạn theo dấu chấm (sentences) ──
        # Trong mỗi câu, chia theo dấu phẩy và xóa segment chứa từ khóa
        sentences = re.split(r'(?<=[.!?])\s+', prompt)
        cleaned_sentences = []
        for sentence in sentences:
            # Chia câu thành segments bằng dấu phẩy
            segments = sentence.split(',')
            cleaned_segments = []
            for seg in segments:
                seg_stripped = seg.strip()
                if not seg_stripped:
                    continue
                # Segment chứa "reference image" → LUÔN GIỮ (format đúng)
                if "reference image" in seg_stripped.lower():
                    cleaned_segments.append(seg_stripped)
                    continue
                # Nếu segment chứa từ khóa ngoại hình → xóa
                if _has_appearance_kw(seg_stripped):
                    # Nhưng GIỮA nếu segment cũng chứa hành động quan trọng (action verb)
                    action_verbs = ["places", "holds", "reaches", "picks", "stirs", "pours",
                                    "lifts", "carries", "walks", "sits", "stands", "runs",
                                    "opens", "closes", "moves", "turns", "looks", "smiles",
                                    "eats", "drinks", "cooking", "working", "playing",
                                    "đặt", "cầm", "giữ", "đi", "ngồi", "đứng", "chạy"]
                    seg_lower = seg_stripped.lower()
                    has_action = any(av in seg_lower for av in action_verbs)
                    if has_action:
                        # Giữ action, cố xóa phần mô tả 
                        # Pattern: "wearing a X" hoặc "her hair in X"
                        seg_stripped = re.sub(r'\bwearing\s+[^,]{3,40}', '', seg_stripped, flags=re.IGNORECASE)
                        seg_stripped = re.sub(r'\b(?:her|his|with)\s+(?:\w+\s+){0,3}hair\s+[^,]{2,30}', '', seg_stripped, flags=re.IGNORECASE)
                        seg_stripped = re.sub(r'\b(?:her|his)\s+face\s+framed\s+by\s+[^,]{3,40}', '', seg_stripped, flags=re.IGNORECASE)
                        seg_stripped = seg_stripped.strip().strip(',').strip()
                        if seg_stripped:
                            cleaned_segments.append(seg_stripped)
                    else:
                        if log_fn:
                            log_fn(f"   ✂️ Scene {scene_num} [{field}]: Xóa '{seg_stripped[:50]}...'")
                        continue
                else:
                    cleaned_segments.append(seg_stripped)
            
            if cleaned_segments:
                cleaned_sentences.append(', '.join(cleaned_segments))

        prompt = '. '.join(cleaned_sentences)

        # ── Bước 3: Dọn dẹp ──
        prompt = re.sub(r'\s*,\s*,', ',', prompt)
        prompt = re.sub(r'\s{2,}', ' ', prompt)
        prompt = re.sub(r',\s*\.', '.', prompt)
        prompt = re.sub(r'\.\s*\.', '.', prompt)
        prompt = prompt.strip().strip(',').strip()

        # ── Bước 4: Thêm cụm reference image sau label nhân vật ──
        if char_labels:
            for label in char_labels:
                if not label:
                    continue
                # Tìm label trong prompt mà CHƯA có _REF_PHRASE theo sau
                # Pattern: label + KHÔNG theo sau bởi "(maintaining..."
                label_escaped = re.escape(label)
                # Kiểm tra nếu label có trong prompt
                if label.lower() in prompt.lower():
                    # Tìm vị trí label (case insensitive)
                    pattern = f'({label_escaped})(?!\\s*\\(character taken)'
                    replacement = f'\\1 {_REF_PHRASE}'
                    new_prompt = re.sub(pattern, replacement, prompt, count=1, flags=re.IGNORECASE)
                    if new_prompt != prompt:
                        prompt = new_prompt
                        if log_fn:
                            log_fn(f"   📌 Scene {scene_num} [{field}]: Thêm reference phrase sau '{label}'")

        if prompt != original and log_fn:
            log_fn(f"   ✅ Scene {scene_num} [{field}] đã xử lý xong")

        return prompt

    # Áp dụng cho từng scene
    cleaned_scenes = []
    for scene in scenes:
        new_img = _clean_prompt(scene.image_prompt, scene.scene_number, "image")
        new_veo = _clean_prompt(scene.veo_prompt, scene.scene_number, "video")
        cleaned_scenes.append(AnalyzedScene(
            scene_number=scene.scene_number,
            image_prompt=new_img,
            veo_prompt=new_veo,
        ))
    return cleaned_scenes

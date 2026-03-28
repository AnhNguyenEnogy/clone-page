"""
video_analyzer.py
-----------------
Phân tích video bất kỳ bằng Gemini AI.
Tự động phát hiện nhân vật, phân cảnh, tạo prompt ảnh và prompt video (Veo3).
Áp dụng cho MỌI thể loại video — không cần nhân vật tham chiếu cố định.

Usage (standalone):
    python video_analyzer.py --video "path/to/video.mp4" --output "result.json"
    python video_analyzer.py --video "path/to/video.mp4" --output "result.json" --duration 60
    python video_analyzer.py --video "path/to/video.mp4" --output "result.json" --lang en

Usage (as module):
    from video_analyzer import analyze_video
    result = analyze_video(video_path="video.mp4")
"""
from __future__ import annotations

import argparse
import base64
import json
import logging
import math
import os
import re
import subprocess
import sys
import threading
import time
from pathlib import Path

logger = logging.getLogger(__name__)


# ── Ngoại lệ ──────────────────────────────────────────────────────
class StopRequested(Exception):
    """Ngoại lệ khi người dùng yêu cầu dừng."""
    pass


# ── Kiểu dữ liệu kết quả ─────────────────────────────────────────

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


class AnalysisResult:
    def __init__(
        self,
        scenes: list[AnalyzedScene] | None = None,
        social_content: SocialContent | None = None,
        characters: list[dict] | None = None,
        vietnamese_script: str = "",
    ):
        self.scenes = scenes or []
        self.social_content = social_content or SocialContent()
        self.characters = characters or []
        self.vietnamese_script = vietnamese_script

    def to_dict(self) -> dict:
        return {
            "characters": self.characters,
            "vietnamese_script": self.vietnamese_script,
            "scenes": [s.to_dict() for s in self.scenes],
            "social_content": self.social_content.to_dict(),
        }

    def to_json(self, indent: int = 2) -> str:
        return json.dumps(self.to_dict(), ensure_ascii=False, indent=indent)


# ── Helpers ────────────────────────────────────────────────────────

def _file_to_base64(file_path: str) -> tuple[str, str]:
    """Đọc file → (base64_data, mime_type)."""
    ext = Path(file_path).suffix.lower()
    mime_map = {
        ".mp4": "video/mp4", ".avi": "video/x-msvideo",
        ".mov": "video/quicktime", ".mkv": "video/x-matroska",
        ".webm": "video/webm", ".png": "image/png",
        ".jpg": "image/jpeg", ".jpeg": "image/jpeg",
        ".gif": "image/gif", ".webp": "image/webp",
    }
    mime = mime_map.get(ext, "application/octet-stream")
    with open(file_path, "rb") as f:
        data = base64.standard_b64encode(f.read()).decode("utf-8")
    return data, mime


def _get_video_duration(video_path: str) -> float | None:
    """Lấy thời lượng video (giây) bằng ffprobe."""
    try:
        cmd = [
            "ffprobe", "-v", "error",
            "-show_entries", "format=duration",
            "-of", "default=noprint_wrappers=1:nokey=1",
            video_path,
        ]
        kwargs = {"capture_output": True, "text": True, "timeout": 30}
        if os.name == "nt":
            kwargs["creationflags"] = subprocess.CREATE_NO_WINDOW
        result = subprocess.run(cmd, **kwargs)
        if result.returncode == 0 and result.stdout.strip():
            return float(result.stdout.strip())
    except Exception:
        pass
    return None


# ── System Prompt Builder ──────────────────────────────────────────

def _build_system_instruction(
    language: str = "vi",
    target_duration: str = "",
    voice_description: str = "",
    style: str = "",
    lock_scene_count: bool = True,
    custom_instruction: str = "",
    reference_image_paths: list[str] | None = None,
    ref_image_names: list[str] | None = None,
    character_names: list[str] | None = None,
) -> str:
    """Xây dựng system instruction cho Gemini dựa trên các tham số."""

    if reference_image_paths is None:
        reference_image_paths = []
    if ref_image_names is None:
        ref_image_names = []
    if character_names is None:
        character_names = []

    lang_instruction = "VIETNAMESE" if language == "vi" else "ENGLISH"

    # ── Phần đầu: chỉ thị ảnh tham chiếu (nếu có) ──
    ref_pre = ""
    if reference_image_paths:
        ref_char_list = []
        for i in range(len(reference_image_paths)):
            name = ref_image_names[i] if i < len(ref_image_names) else f"character_{i+1}"
            ref_char_list.append(name)
        ref_names_str = ", ".join([f'"{n}"' for n in ref_char_list])
        ref_pre = (
            "BEFORE ANYTHING ELSE - READ THIS FIRST:\n"
            f"Reference images are provided for SPECIFIC character(s): {ref_names_str}.\n"
            "For ONLY these characters, you are ABSOLUTELY FORBIDDEN from describing their appearance. "
            "Write ONLY: [label] (character taken from reference image). "
            "For ALL OTHER characters (those WITHOUT reference images), you MUST describe them in full detail as usual.\n\n"
        )

    # ── Core system instruction ──
    instruction = f"""{ref_pre}You are an expert shot-by-shot film analyst and a master prompt engineer for the Google Veo 3 video generation model. Your task is to analyze the input video and generate a series of hyper-detailed, professional prompts in {lang_instruction} that can be used to precisely recreate the video.

CRITICAL RULES FOR VEO 3:
1.  **Scene-by-Scene Analysis (8 Seconds per Scene):** Break down the video into distinct scenes. IMPORTANT: Veo 3 generates exactly 8 seconds of video per prompt. You MUST pace the action and dialogue so that it fits perfectly within an 8-second window. If a scene in the original video is longer, break it down into multiple 8-second prompts.
2.  **Dialogue & Pacing:** If there is spoken dialogue, transcribe it VERBATIM and enclose it in double quotes.
    *   **Crucial Timing:** The dialogue must be spoken at a natural, appropriate speed so no words or sentences are cut off within the 8-second limit.
    *   **Natural Pauses:** Explicitly instruct the model to pause at natural resting points (commas, periods) to ensure the speech sounds natural and fits the 8-second timeframe perfectly.
3.  **Meticulous Description (CRITICAL FOR CAMERA & ACTION):** The prompt must be a masterclass in detail:
    *   **Subject Action:** Describe exactly what the subject is doing with micro-actions (e.g., "he strides purposefully forward, arms swinging slightly, eyes fixed on the horizon").
    *   **Camera Movement & Angle:** Use professional cinematography terms: Pan, Tilt, Dolly, Tracking, Crane, Handheld, Steadicam, Zoom. Describe speed. Shot sizes: ECU, CU, MS, WS, EWS, High/Low/Dutch Angle, OTS, POV.
    *   **Environment:** Background, foreground, props, setting.
    *   **Lighting & Color:** Lighting quality, color grading.

4.  **ACTION-HEAVY VIDEO ANALYSIS (CRITICAL):** For action-driven videos:
    *   Prioritize movement description with micro-action breakdown.
    *   State tempo: "rapid succession", "slow motion", "explosive burst".
    *   Describe physics: momentum, gravity, impact.
    *   Include facial expressions during action.
    *   Add sound cues: "whoosh", "thud", "crunch".
    *   Use more scenes for fast-paced sequences.

5.  **Language:** All output prompts in **{lang_instruction}**.
6.  **Output Format:** Valid JSON with ALL required keys:
    - "characters" (REQUIRED): array of {{label, description}}
    - "vietnamese_script" (REQUIRED): complete Vietnamese screenplay
    - "scenes" (REQUIRED): array of {{scene_number, image_prompt, veo_prompt}}
    - "social_content" (REQUIRED): {{facebook, youtube, tiktok}} each with {{title, content, hashtags}}
    
    Do not include explanatory text, markdown, or anything outside JSON.

7.  **Social Content (ALWAYS IN VIETNAMESE):** Generate social media content. ALL content MUST be in VIETNAMESE.
    *   **Title:** Powerful hook — curiosity, emotion, controversy.
    *   **Content:** Hook + story, builds curiosity, doesn't reveal everything.
    *   **Hashtags:** Trending Vietnamese hashtags.

**CHARACTER ANALYSIS (CRITICAL):**
*   Step 1: Identify ALL characters. Assign fixed, consistent labels.
*   Step 2: Mention characters by label in EVERY scene's image_prompt AND veo_prompt.
*   Step 3: ABSOLUTE NAME CONSISTENCY — exact label string from characters array must appear VERBATIM in all prompts.
*   Step 4: Every prompt MUST START with character label(s). Prompts without named characters are FORBIDDEN.
"""

    # ── Mô tả nhân vật dựa trên có/không ảnh tham chiếu ──
    if reference_image_paths:
        ref_mapping_lines = []
        for i, img_path in enumerate(reference_image_paths):
            name = ref_image_names[i] if i < len(ref_image_names) else f"character_{i+1}"
            ref_mapping_lines.append(f"  - Reference image #{i+1} → character: \"{name}\"")
        ref_mapping_str = "\n".join(ref_mapping_lines)
        ref_names_for_prompt = [ref_image_names[i] if i < len(ref_image_names) else f"character_{i+1}" for i in range(len(reference_image_paths))]
        ref_names_quoted = ", ".join([f'"{n}"' for n in ref_names_for_prompt])

        instruction += f"""
**CHARACTER DESCRIPTION RULE (REFERENCE IMAGES PROVIDED - SELECTIVE):**
Mapping: {ref_mapping_str}

Characters WITH reference images: {ref_names_quoted}

**FOR CHARACTERS WITH REFERENCE IMAGES ({ref_names_quoted}):**
- ZERO APPEARANCE DESCRIPTION. Write ONLY label + "(character taken from reference image)".
- In characters array, set description to "Character taken from reference image".

**FOR ALL OTHER CHARACTERS:**
- Describe with EXTREME detail: face, hair, body, clothing, accessories.
"""
    else:
        instruction += """
**CHARACTER DESCRIPTION RULE (NO REFERENCE IMAGES - ULTRA-DETAILED):**
Since no reference images are provided, you MUST describe each character with EXTREME precision:

**1. FACE & HEAD:** Face shape, skin tone, eyes (shape, color, size), nose, lips, eyebrows, facial hair, expression.
**2. HAIR:** Color, length, style, texture, bangs.
**3. BODY & BUILD:** Gender, age, height, build, posture.
**4. CLOTHING & ACCESSORIES:** Top (type, color, material, pattern, fit), bottom, footwear, accessories, special details.
**5. FOR ANIMALS:** Species, breed, size, fur color/pattern/texture, distinctive features.
**6. CONSISTENCY:** Fixed label used in ALL scenes, BOTH image_prompt AND veo_prompt. Full description in parentheses after label in every image_prompt.

**EXAMPLE:**
image_prompt: "the young woman with wavy chestnut hair (a slender woman in her mid-20s, fair skin with freckles, oval face, large dark brown eyes, wavy chestnut hair to mid-back, light blue linen sundress, gold necklace, white sneakers) stands in a sunlit kitchen."
veo_prompt: "the young woman with wavy chestnut hair (mid-20s, fair skin, wavy chestnut hair, blue sundress) carefully lifts a steaming pot. Camera: medium shot, low angle, warm golden lighting."
"""

    # ── Số cảnh ──
    total_seconds = None
    if target_duration:
        dur_match = re.search(r'(\d+)', str(target_duration))
        if dur_match:
            total_seconds = int(dur_match.group(1))

    if lock_scene_count:
        if total_seconds and total_seconds > 0:
            num_scenes = math.ceil(total_seconds / 8)
            actual_duration = num_scenes * 8
            instruction += f"""
**TARGET DURATION:** Exactly {actual_duration} seconds ({num_scenes} scenes × 8s). Generate EXACTLY {num_scenes} scenes."""
        else:
            instruction += """
**TARGET DURATION (AUTO-DETECT):** Determine video duration, calculate scenes = ceil(duration/8). Generate EXACTLY that many scenes."""
    else:
        hint = f" The video is approximately {total_seconds}s." if total_seconds else ""
        instruction += f"""
**SCENE COUNT (AI-DETERMINED):**{hint} Each scene = 8s. Determine optimal scene count based on content:
- Dialogue-heavy → match duration
- Action-heavy → use MORE scenes for fast sequences
- Slow/contemplative → fewer scenes"""

    # ── Giọng đọc ──
    if voice_description:
        instruction += f"""
**VOICEOVER:** Include this description in scenes with dialogue: "{voice_description}" """

    # ── Phong cách ──
    if style:
        instruction += f"""
**VISUAL STYLE (USER SELECTED):** Apply EXACTLY this style to EVERY prompt. IGNORE original video style:
\"{style}\"
Include full style description in every image_prompt and veo_prompt."""
    else:
        instruction += """
**VISUAL STYLE (AUTO-DETECT):** Analyze original video's visual style and include it in every prompt."""

    # ── Tên nhân vật ──
    if character_names:
        names_str = ", ".join([f'"{n}"' for n in character_names if n.strip()])
        instruction += f"""
**CHARACTER NAMING (USER-DEFINED):** Use these exact names: {names_str}. Match to characters in video. Use consistently in ALL prompts."""

    # ── Custom instruction ──
    if custom_instruction:
        instruction += f"""
**HIGHEST PRIORITY - USER CUSTOM INSTRUCTION:**
\"{custom_instruction}\"
Follow strictly. Override conflicting rules."""

    return instruction


# ── Post-processing ───────────────────────────────────────────────

def _ensure_character_in_prompt(scene: AnalyzedScene, char_labels: list[str], log_fn=None):
    """Kiểm tra prompt có nhân vật. Nếu thiếu → chèn nhân vật chính vào đầu."""
    if not char_labels:
        return

    def _find_present(text: str) -> list[str]:
        text_lower = text.lower()
        return [lbl for lbl in char_labels if lbl.lower() in text_lower]

    def _inject(prompt: str, field: str) -> str:
        if not prompt or not prompt.strip():
            return prompt
        if _find_present(prompt):
            return prompt
        main_char = char_labels[0]
        if log_fn:
            log_fn(f"   ⚠️ Scene {scene.scene_number} [{field}]: Thiếu nhân vật → chèn '{main_char}'")
        return f"{main_char} — {prompt}"

    scene.image_prompt = _inject(scene.image_prompt, "image_prompt")
    scene.veo_prompt = _inject(scene.veo_prompt, "veo_prompt")


def _strip_appearance_for_ref_chars(
    scenes: list[AnalyzedScene],
    char_labels: list[str],
    log_fn=None,
) -> list[AnalyzedScene]:
    """Xoá mô tả ngoại hình cho nhân vật có ảnh tham chiếu."""
    _REF_PHRASE = "(character taken from reference image)"
    _APPEARANCE_KEYWORDS = [
        "hair", " bun", "ponytail", "braids", "bangs", "fringe",
        "wearing", "sleeveless", "apron", "skirt", "jeans",
        "jacket", "coat", "sweater", "hoodie", "uniform",
        "dress", "shirt", "blouse", "pattern", "striped", "floral",
        "mid-20s", "mid-30s", "years old", "skin tone", "fair skin",
        "ribbon", "necklace", "earring", "glasses",
    ]

    def _has_kw(text: str) -> bool:
        text_lower = text.lower()
        return any(kw in text_lower for kw in _APPEARANCE_KEYWORDS)

    def _clean(prompt: str, scene_num: int, field: str) -> str:
        if not prompt:
            return prompt
        original = prompt

        # Thay nội dung trong (...) chứa từ khoá ngoại hình
        def _replace_paren(match):
            content = match.group(1)
            if len(content) < 8:
                return match.group(0)
            if "reference image" in content.lower():
                return match.group(0)
            if _has_kw(content):
                return _REF_PHRASE
            return match.group(0)

        prompt = re.sub(r'\(([^)]+)\)', _replace_paren, prompt)

        # Thêm reference phrase sau label nhân vật
        for label in char_labels:
            if not label:
                continue
            if label.lower() in prompt.lower():
                escaped = re.escape(label)
                pattern = f'({escaped})(?!\\s*\\(character taken)'
                new_prompt = re.sub(pattern, f'\\1 {_REF_PHRASE}', prompt, count=1, flags=re.IGNORECASE)
                if new_prompt != prompt:
                    prompt = new_prompt

        # Dọn dẹp
        prompt = re.sub(r'\s*,\s*,', ',', prompt)
        prompt = re.sub(r'\s{2,}', ' ', prompt)
        prompt = prompt.strip().strip(',').strip()

        if prompt != original and log_fn:
            log_fn(f"   ✅ Scene {scene_num} [{field}] đã xử lý")

        return prompt

    result = []
    for scene in scenes:
        result.append(AnalyzedScene(
            scene_number=scene.scene_number,
            image_prompt=_clean(scene.image_prompt, scene.scene_number, "image"),
            veo_prompt=_clean(scene.veo_prompt, scene.scene_number, "video"),
        ))
    return result


# ── API chính ─────────────────────────────────────────────────────

def analyze_video(
    video_path: str,
    api_key: str = "",
    api_keys_path: str = "",
    target_duration: str = "",
    language: str = "vi",
    voice_description: str = "",
    reference_image_paths: list[str] | None = None,
    ref_image_names: list[str] | None = None,
    style: str = "",
    lock_scene_count: bool = True,
    character_names: list[str] | None = None,
    custom_instruction: str = "",
    log_callback=None,
    stop_check_fn=None,
) -> AnalysisResult:
    """
    Phân tích video và tạo prompt ảnh + prompt video Veo3.

    Args:
        video_path: Đường dẫn tới file video.
        api_key: API key Gemini (nếu trống → đọc từ file).
        api_keys_path: Đường dẫn file chứa API keys.
        target_duration: Thời lượng mục tiêu (VD: "60s", "30s").
        language: "vi" hoặc "en".
        voice_description: Mô tả giọng đọc.
        reference_image_paths: Ảnh tham chiếu nhân vật (tuỳ chọn).
        ref_image_names: Tên nhân vật tương ứng ảnh tham chiếu.
        style: Phong cách hình ảnh.
        lock_scene_count: Khoá số cảnh theo thời lượng.
        character_names: Tên nhân vật do người dùng đặt.
        custom_instruction: Chỉ thị tuỳ chỉnh.
        log_callback: Hàm log.
        stop_check_fn: Hàm kiểm tra dừng.

    Returns:
        AnalysisResult chứa characters, scenes, social_content, vietnamese_script.
    """
    try:
        from google import genai
        from google.genai import types
    except ImportError:
        raise RuntimeError("Cần cài thư viện: pip install google-genai")

    if reference_image_paths is None:
        reference_image_paths = []
    if ref_image_names is None:
        ref_image_names = []
    if character_names is None:
        character_names = []

    def _log(msg: str):
        if log_callback:
            try:
                log_callback(msg)
            except Exception:
                pass
        logger.info(msg)

    def _check_stop():
        if stop_check_fn and stop_check_fn():
            raise StopRequested("Người dùng đã yêu cầu dừng.")

    _log("🎬 Bắt đầu phân tích video...")
    _check_stop()

    # ── API Key ──
    from api_key_manager import ApiKeyManager

    if not api_keys_path:
        # Tìm file key mặc định
        script_dir = Path(__file__).parent
        default_paths = [
            script_dir.parent / "resources" / "gemini_api_key.txt",
            script_dir / "gemini_api_key.txt",
            Path.home() / "gemini_api_key.txt",
        ]
        for p in default_paths:
            if p.exists():
                api_keys_path = str(p)
                break

    key_mgr = ApiKeyManager(api_keys_path)
    key_mgr.reload_keys()

    if api_key:
        preferred_key = api_key
    else:
        preferred_key = None

    if not api_key and not key_mgr.has_available_keys():
        raise RuntimeError("Chưa có Gemini API key. Thêm key vào file hoặc truyền qua --api-key.")

    # ── System instruction ──
    system_instruction = _build_system_instruction(
        language=language,
        target_duration=target_duration,
        voice_description=voice_description,
        style=style,
        lock_scene_count=lock_scene_count,
        custom_instruction=custom_instruction,
        reference_image_paths=reference_image_paths,
        ref_image_names=ref_image_names,
        character_names=character_names,
    )

    # ── Chuẩn bị content parts ──
    _check_stop()
    _log("📤 Đang upload video lên Gemini...")
    video_data, video_mime = _file_to_base64(video_path)
    parts = [
        types.Part.from_bytes(data=base64.standard_b64decode(video_data), mime_type=video_mime),
    ]
    _log(f"✅ Upload xong: {os.path.basename(video_path)}")

    # Upload ảnh tham chiếu
    if reference_image_paths:
        _log(f"📷 Upload {len(reference_image_paths)} ảnh tham chiếu...")
    for i, img_path in enumerate(reference_image_paths):
        try:
            img_data, img_mime = _file_to_base64(img_path)
            parts.append(types.Part.from_bytes(data=base64.standard_b64decode(img_data), mime_type=img_mime))
            char_name = ref_image_names[i] if i < len(ref_image_names) else f"character_{i+1}"
            _log(f"  ✅ Ảnh nhân vật \"{char_name}\": {os.path.basename(img_path)}")
        except Exception as e:
            _log(f"  ❌ Lỗi ảnh {img_path}: {e}")

    # Reminder cho ảnh tham chiếu
    if reference_image_paths:
        ref_names_list = [ref_image_names[i] if i < len(ref_image_names) else f"character_{i+1}" for i in range(len(reference_image_paths))]
        mapping_parts = [f'Image #{i+1} = "{ref_names_list[i]}"' for i in range(len(reference_image_paths))]
        mapping_text = ", ".join(mapping_parts)
        ref_names_text = ", ".join([f'"{n}"' for n in ref_names_list])

        parts.append(types.Part.from_text(text=(
            f"CRITICAL REMINDER: Reference images provided. Mapping: {mapping_text}. "
            f"ONLY characters matching {ref_names_text} use '(character taken from reference image)'. "
            "For ALL OTHER characters, describe in FULL detail."
        )))

    # ── Response schema ──
    lang_instruction = "VIETNAMESE" if language == "vi" else "ENGLISH"
    social_schema = types.Schema(
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
                        "label": types.Schema(type=types.Type.STRING, description="Fixed label for this character."),
                        "description": types.Schema(type=types.Type.STRING, description="Physical description."),
                    },
                    required=["label", "description"],
                ),
            ),
            "vietnamese_script": types.Schema(
                type=types.Type.STRING,
                description="Complete Vietnamese screenplay, scene by scene.",
            ),
            "scenes": types.Schema(
                type=types.Type.ARRAY,
                items=types.Schema(
                    type=types.Type.OBJECT,
                    properties={
                        "scene_number": types.Schema(type=types.Type.INTEGER),
                        "image_prompt": types.Schema(type=types.Type.STRING, description=f"Detailed {lang_instruction} image prompt."),
                        "veo_prompt": types.Schema(type=types.Type.STRING, description=f"Detailed {lang_instruction} Veo3 prompt."),
                    },
                    required=["scene_number", "image_prompt", "veo_prompt"],
                ),
            ),
            "social_content": types.Schema(
                type=types.Type.OBJECT,
                properties={
                    "facebook": social_schema,
                    "youtube": social_schema,
                    "tiktok": social_schema,
                },
                required=["facebook", "youtube", "tiktok"],
            ),
        },
        required=["characters", "vietnamese_script", "scenes", "social_content"],
    )

    # ── Gọi Gemini API với auto-retry ──
    _check_stop()
    _log("🤖 Đang gửi tới Gemini AI...")

    invalid_kw = ["api_key_invalid", "invalid api key", "api key not valid", "not found", "invalid", "expired"]
    quota_kw = ["429", "quota", "rate", "limit", "403", "permission", "exhausted", "resource_exhausted"]

    max_retries = key_mgr.count_total() + 2 if key_mgr.count_total() > 0 else 3
    last_error = None
    current_key = None
    response = None

    try:
        for attempt in range(1, max_retries + 1):
            _check_stop()

            # Chọn key
            if api_key and attempt == 1:
                current_key = api_key
            else:
                current_key = key_mgr.reserve_key(preferred=preferred_key or "")

            if not current_key:
                break

            try:
                client = genai.Client(api_key=current_key)
                if attempt > 1:
                    _log(f"🔄 Thử key {attempt}: {current_key[:8]}... (còn {key_mgr.count_ok()} key)")

                # API call trong thread (hỗ trợ stop)
                _result = [None]
                _error = [None]
                _done = threading.Event()

                def _call():
                    try:
                        _result[0] = client.models.generate_content(
                            model="gemini-2.5-flash",
                            contents=types.Content(parts=parts),
                            config=types.GenerateContentConfig(
                                system_instruction=system_instruction,
                                response_mime_type="application/json",
                                response_schema=response_schema,
                            ),
                        )
                    except Exception as e:
                        _error[0] = e
                    finally:
                        _done.set()

                t = threading.Thread(target=_call, daemon=True)
                t.start()

                while not _done.is_set():
                    _done.wait(timeout=1.0)
                    if _done.is_set():
                        break
                    if stop_check_fn and stop_check_fn():
                        raise StopRequested("Dừng.")

                if _error[0] is not None:
                    raise _error[0]
                response = _result[0]

                _log(f"✅ Thành công: {current_key[:8]}...")
                key_mgr.release_key(current_key)
                current_key = None
                break

            except StopRequested:
                key_mgr.release_key(current_key)
                current_key = None
                raise

            except Exception as err:
                last_error = err
                err_str = str(err).lower()
                key_mgr.release_key(current_key)
                released = current_key
                current_key = None

                if any(kw in err_str for kw in invalid_kw):
                    _log(f"❌ Key {released[:8]}... không hợp lệ → xoá")
                    key_mgr.mark_invalid(released, log_fn=_log)
                    continue
                if any(kw in err_str for kw in quota_kw):
                    _log(f"⚠️ Key {released[:8]}... hết quota → bỏ qua")
                    key_mgr.mark_quota(released)
                    continue
                raise
        else:
            raise RuntimeError(f"Tất cả API key lỗi. Lỗi cuối: {last_error}")
    finally:
        if current_key:
            key_mgr.release_key(current_key)

    if response is None:
        raise RuntimeError(f"Không nhận được phản hồi. Lỗi: {last_error}")

    _log("📊 Đang phân tích kết quả...")

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
        raise RuntimeError("AI trả về phản hồi trống.")

    clean_json = raw_text.strip()
    if clean_json.startswith("```json"):
        clean_json = clean_json[7:]
    if clean_json.startswith("```"):
        clean_json = clean_json[3:]
    if clean_json.endswith("```"):
        clean_json = clean_json[:-3]
    clean_json = clean_json.strip()

    try:
        data = json.loads(clean_json)
    except json.JSONDecodeError:
        match = re.search(r'(\{[\s\S]*\})', clean_json)
        if match:
            try:
                data = json.loads(match.group(0))
            except json.JSONDecodeError:
                raise RuntimeError("AI trả về JSON không hợp lệ.")
        else:
            raise RuntimeError("AI trả về định dạng không hợp lệ.")

    # ── Parse kết quả ──
    scenes: list[AnalyzedScene] = []
    for s in data.get("scenes", []):
        scenes.append(AnalyzedScene(
            scene_number=int(s.get("scene_number", 0)),
            image_prompt=str(s.get("image_prompt", "")),
            veo_prompt=str(s.get("veo_prompt", "")),
        ))

    sc = data.get("social_content", {})
    social = SocialContent(
        facebook=SocialPlatformContent(**sc.get("facebook", {})) if isinstance(sc.get("facebook"), dict) else SocialPlatformContent(),
        youtube=SocialPlatformContent(**sc.get("youtube", {})) if isinstance(sc.get("youtube"), dict) else SocialPlatformContent(),
        tiktok=SocialPlatformContent(**sc.get("tiktok", {})) if isinstance(sc.get("tiktok"), dict) else SocialPlatformContent(),
    )

    characters: list[dict] = []
    for c in data.get("characters", []):
        if isinstance(c, dict):
            characters.append({
                "label": str(c.get("label", "")),
                "description": str(c.get("description", "")),
            })

    # ── Post-processing ──
    if reference_image_paths and scenes:
        _log("🔧 Xoá mô tả ngoại hình nhân vật có ảnh tham chiếu...")
        ref_names_set = set()
        for i in range(len(reference_image_paths)):
            name = ref_image_names[i] if i < len(ref_image_names) else f"character_{i+1}"
            ref_names_set.add(name.lower())
        ref_labels = [c["label"] for c in characters if c["label"].lower() in ref_names_set]
        if not ref_labels:
            ref_labels = list(ref_image_names) if ref_image_names else []
        if ref_labels:
            scenes = _strip_appearance_for_ref_chars(scenes, ref_labels, _log)

    if characters and scenes:
        all_labels = [c["label"] for c in characters if c["label"]]
        if all_labels:
            _log(f"🔍 Kiểm tra nhân vật ({len(all_labels)} nhân vật)...")
            for scene in scenes:
                _ensure_character_in_prompt(scene, all_labels, _log)

    vietnamese_script = str(data.get("vietnamese_script", ""))
    _log(f"✅ Hoàn tất! {len(scenes)} cảnh, {len(characters)} nhân vật.")

    return AnalysisResult(
        scenes=scenes,
        social_content=social,
        characters=characters,
        vietnamese_script=vietnamese_script,
    )


# ── CLI ───────────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(
        description="Phân tích video bằng Gemini AI → tạo prompt ảnh + video Veo3",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument("--video", "-v", required=True, help="Đường dẫn video đầu vào")
    parser.add_argument("--output", "-o", default="analysis_result.json", help="File JSON đầu ra")
    parser.add_argument("--api-key", default="", help="Gemini API key (nếu không dùng file)")
    parser.add_argument("--keys-file", default="", help="File chứa Gemini API keys")
    parser.add_argument("--duration", "-d", default="", help="Thời lượng mục tiêu (VD: 60s)")
    parser.add_argument("--lang", "-l", default="vi", choices=["vi", "en"], help="Ngôn ngữ prompt")
    parser.add_argument("--style", "-s", default="", help="Phong cách hình ảnh")
    parser.add_argument("--unlock-scenes", action="store_true", help="Cho AI tự quyết định số cảnh")
    parser.add_argument("--names", nargs="*", default=[], help="Tên nhân vật (VD: --names Ti Tun)")
    parser.add_argument("--ref-images", nargs="*", default=[], help="Ảnh tham chiếu nhân vật")
    parser.add_argument("--ref-names", nargs="*", default=[], help="Tên nhân vật tương ứng ảnh tham chiếu")
    parser.add_argument("--instruction", default="", help="Chỉ thị tuỳ chỉnh")
    parser.add_argument("--markdown", "-m", action="store_true", help="Xuất thêm file markdown")

    args = parser.parse_args()

    if not os.path.isfile(args.video):
        print(f"❌ File video không tồn tại: {args.video}")
        sys.exit(1)

    def _print_log(msg):
        print(msg)

    result = analyze_video(
        video_path=args.video,
        api_key=args.api_key,
        api_keys_path=args.keys_file,
        target_duration=args.duration,
        language=args.lang,
        style=args.style,
        lock_scene_count=not args.unlock_scenes,
        character_names=args.names,
        reference_image_paths=args.ref_images,
        ref_image_names=args.ref_names,
        custom_instruction=args.instruction,
        log_callback=_print_log,
    )

    # Lưu JSON
    output_path = Path(args.output)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, "w", encoding="utf-8") as f:
        f.write(result.to_json())
    print(f"\n{'='*60}")
    print(f"✅ Kết quả đã lưu: {output_path}")
    print(f"   Nhân vật: {len(result.characters)}")
    print(f"   Số cảnh:  {len(result.scenes)}")
    print(f"{'='*60}")

    # Xuất markdown (tuỳ chọn)
    if args.markdown:
        md_path = output_path.with_suffix(".md")
        _export_markdown(result, md_path)
        print(f"📄 Markdown: {md_path}")


def _export_markdown(result: AnalysisResult, output_path: Path):
    """Xuất kết quả phân tích ra file markdown."""
    lines = ["# Kết Quả Phân Tích Video\n"]

    # Nhân vật
    lines.append("## Nhân Vật\n")
    for c in result.characters:
        lines.append(f"### {c['label']}")
        lines.append(f"{c['description']}\n")

    # Kịch bản
    if result.vietnamese_script:
        lines.append("## Kịch Bản Tiếng Việt\n")
        lines.append(result.vietnamese_script + "\n")

    # Prompt ảnh
    lines.append("## 📷 Prompt Tạo Ảnh\n")
    lines.append("```")
    for s in result.scenes:
        lines.append(f"Scene {s.scene_number}: {s.image_prompt}")
    lines.append("```\n")

    # Prompt video
    lines.append("## 🎬 Prompt Tạo Video Veo3\n")
    lines.append("```")
    for s in result.scenes:
        lines.append(f"Scene {s.scene_number}: {s.veo_prompt}")
    lines.append("```\n")

    # Social content
    lines.append("## 📱 Content Media\n")
    sc = result.social_content
    lines.append("### Facebook")
    lines.append(f"{sc.facebook.title}\n{sc.facebook.content}\n{sc.facebook.hashtags}\n")
    lines.append("### YouTube")
    lines.append(f"{sc.youtube.title}\n{sc.youtube.content}\n{sc.youtube.hashtags}\n")
    lines.append("### TikTok")
    lines.append(f"{sc.tiktok.title}\n{sc.tiktok.content}\n{sc.tiktok.hashtags}\n")

    with open(output_path, "w", encoding="utf-8") as f:
        f.write("\n".join(lines))


if __name__ == "__main__":
    main()

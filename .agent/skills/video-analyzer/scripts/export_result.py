"""
export_result.py
----------------
Xuất kết quả phân tích video ra các định dạng khác nhau.
"""
from __future__ import annotations

import json
from pathlib import Path


def export_to_json(result, output_path: str, indent: int = 2):
    """Xuất kết quả ra file JSON."""
    path = Path(output_path)
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        f.write(result.to_json(indent=indent))
    return str(path)


def export_to_markdown(result, output_path: str) -> str:
    """Xuất kết quả ra file Markdown với format copy-paste."""
    lines = ["# 🎬 Kết Quả Phân Tích Video\n"]

    # ── Nhân vật ──
    lines.append("## 👤 Nhân Vật\n")
    for i, c in enumerate(result.characters, 1):
        lines.append(f"### {i}. {c['label']}")
        lines.append(f"> {c['description']}\n")

    # ── Kịch bản tiếng Việt ──
    if result.vietnamese_script:
        lines.append("---\n")
        lines.append("## 📝 Kịch Bản Tiếng Việt\n")
        lines.append(result.vietnamese_script + "\n")

    # ── Prompt ảnh (1 ô code) ──
    lines.append("---\n")
    lines.append("## 📷 PROMPT TẠO ẢNH (copy toàn bộ)\n")
    lines.append("```")
    for s in result.scenes:
        lines.append(f"Scene {s.scene_number}: {s.image_prompt}")
    lines.append("```\n")

    # ── Prompt video (1 ô code) ──
    lines.append("## 🎬 PROMPT TẠO VIDEO VEO3 (copy toàn bộ)\n")
    lines.append("```")
    for s in result.scenes:
        lines.append(f"Scene {s.scene_number}: {s.veo_prompt}")
    lines.append("```\n")

    # ── Social content (1 ô code) ──
    lines.append("## 📱 CONTENT MEDIA\n")
    lines.append("```")
    sc = result.social_content
    lines.append("Facebook:")
    lines.append(sc.facebook.title)
    lines.append(sc.facebook.content)
    lines.append(sc.facebook.hashtags)
    lines.append("")
    lines.append("YouTube:")
    lines.append(sc.youtube.title)
    lines.append(sc.youtube.content)
    lines.append(sc.youtube.hashtags)
    lines.append("")
    lines.append("TikTok:")
    lines.append(sc.tiktok.title)
    lines.append(sc.tiktok.content)
    lines.append(sc.tiktok.hashtags)
    lines.append("```\n")

    # ── Thống kê ──
    lines.append("---\n")
    lines.append("## 📊 Thống Kê\n")
    lines.append(f"- **Số nhân vật:** {len(result.characters)}")
    lines.append(f"- **Số cảnh:** {len(result.scenes)}")
    lines.append(f"- **Tổng thời lượng:** {len(result.scenes) * 8} giây ({len(result.scenes)} × 8s)")

    path = Path(output_path)
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        f.write("\n".join(lines))
    return str(path)


def export_prompts_only(result, output_path: str) -> str:
    """Xuất chỉ prompt (không có metadata) — tiện cho copy-paste."""
    lines = []

    lines.append("═══ PROMPT TẠO ẢNH ═══\n")
    for s in result.scenes:
        lines.append(f"Scene {s.scene_number}: {s.image_prompt}\n")

    lines.append("\n═══ PROMPT TẠO VIDEO VEO3 ═══\n")
    for s in result.scenes:
        lines.append(f"Scene {s.scene_number}: {s.veo_prompt}\n")

    path = Path(output_path)
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        f.write("\n".join(lines))
    return str(path)

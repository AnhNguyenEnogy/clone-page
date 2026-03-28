"""
Script phân tích video mẫu - trích xuất metadata và frame mẫu.

Usage:
    python scripts/analyze_videos.py --input "path/to/video/folder" --output "analysis.json"
    python scripts/analyze_videos.py --input "path/to/video/folder" --output "analysis.json" --frames 5
"""

import argparse
import json
import os
import subprocess
import sys
from pathlib import Path
from datetime import datetime


def get_video_metadata(video_path: str) -> dict:
    """Trích xuất metadata video bằng ffprobe."""
    try:
        cmd = [
            "ffprobe",
            "-v", "quiet",
            "-print_format", "json",
            "-show_format",
            "-show_streams",
            str(video_path)
        ]
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
        if result.returncode != 0:
            return {"error": f"ffprobe failed: {result.stderr}"}
        
        data = json.loads(result.stdout)
        
        # Trích xuất thông tin video stream
        video_stream = None
        for stream in data.get("streams", []):
            if stream.get("codec_type") == "video":
                video_stream = stream
                break
        
        if not video_stream:
            return {"error": "No video stream found"}
        
        duration = float(data.get("format", {}).get("duration", 0))
        width = int(video_stream.get("width", 0))
        height = int(video_stream.get("height", 0))
        fps_parts = video_stream.get("r_frame_rate", "30/1").split("/")
        fps = round(int(fps_parts[0]) / int(fps_parts[1]), 2) if len(fps_parts) == 2 else 30.0
        file_size = int(data.get("format", {}).get("size", 0))
        
        return {
            "duration_seconds": round(duration, 2),
            "width": width,
            "height": height,
            "resolution": f"{width}x{height}",
            "fps": fps,
            "file_size_bytes": file_size,
            "file_size_mb": round(file_size / (1024 * 1024), 2),
            "codec": video_stream.get("codec_name", "unknown"),
            "aspect_ratio": f"{width}:{height}",
        }
    except FileNotFoundError:
        return {"error": "ffprobe not found. Vui lòng cài FFmpeg."}
    except Exception as e:
        return {"error": str(e)}


def extract_frames(video_path: str, output_dir: str, num_frames: int = 5) -> list:
    """Trích xuất frame mẫu từ video ở các mốc thời gian đều nhau."""
    frames = []
    video_name = Path(video_path).stem
    frame_dir = os.path.join(output_dir, "frames", video_name)
    os.makedirs(frame_dir, exist_ok=True)
    
    # Lấy duration trước
    meta = get_video_metadata(video_path)
    if "error" in meta:
        return frames
    
    duration = meta["duration_seconds"]
    if duration <= 0:
        return frames
    
    # Tính các mốc thời gian
    timestamps = []
    if num_frames == 1:
        timestamps = [duration / 2]
    else:
        step = duration / (num_frames + 1)
        timestamps = [step * (i + 1) for i in range(num_frames)]
    
    for i, ts in enumerate(timestamps):
        frame_path = os.path.join(frame_dir, f"frame_{i+1:02d}_{ts:.1f}s.jpg")
        try:
            cmd = [
                "ffmpeg",
                "-y",
                "-ss", str(ts),
                "-i", str(video_path),
                "-vframes", "1",
                "-q:v", "2",
                str(frame_path)
            ]
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
            if result.returncode == 0 and os.path.exists(frame_path):
                frames.append({
                    "timestamp_seconds": round(ts, 2),
                    "frame_path": frame_path,
                    "scene_index": i + 1
                })
        except Exception as e:
            print(f"  [WARNING] Không thể trích xuất frame tại {ts:.1f}s: {e}")
    
    return frames


def estimate_scene_count(duration: float) -> int:
    """Ước tính số lượng cảnh dựa trên thời lượng video."""
    if duration <= 15:
        return 4
    elif duration <= 25:
        return 6
    elif duration <= 40:
        return 8
    else:
        return 10


def analyze_single_video(video_path: str, output_dir: str, num_frames: int = 5) -> dict:
    """Phân tích một video đơn lẻ."""
    video_name = Path(video_path).stem
    print(f"  Đang phân tích: {video_name}...")
    
    # Lấy metadata
    metadata = get_video_metadata(video_path)
    if "error" in metadata:
        print(f"  [ERROR] {metadata['error']}")
        return {
            "video_id": video_name,
            "file_name": Path(video_path).name,
            "error": metadata["error"]
        }
    
    # Trích xuất frames
    frames = extract_frames(video_path, output_dir, num_frames)
    
    # Ước tính số cảnh
    estimated_scenes = estimate_scene_count(metadata["duration_seconds"])
    
    return {
        "video_id": video_name,
        "file_name": Path(video_path).name,
        "file_path": str(video_path),
        "metadata": metadata,
        "estimated_scene_count": estimated_scenes,
        "extracted_frames": frames,
        "analysis_notes": {
            "suggested_scene_structure": generate_scene_template(estimated_scenes),
            "orientation": "vertical" if metadata["height"] > metadata["width"] else "horizontal"
        }
    }


def generate_scene_template(scene_count: int) -> list:
    """Tạo template cấu trúc cảnh dựa trên số lượng cảnh."""
    templates = {
        4: [
            {"scene": 1, "type": "intro", "name": "Giới thiệu", "description": "Nhân vật + bối cảnh vùng miền"},
            {"scene": 2, "type": "preparation", "name": "Sơ chế", "description": "Chuẩn bị nguyên liệu"},
            {"scene": 3, "type": "cooking", "name": "Chế biến", "description": "Nấu / xào / nướng"},
            {"scene": 4, "type": "reveal", "name": "Thành phẩm", "description": "Trình bày món ăn hoàn chỉnh"},
        ],
        5: [
            {"scene": 1, "type": "intro", "name": "Giới thiệu", "description": "Nhân vật + bối cảnh vùng miền"},
            {"scene": 2, "type": "preparation", "name": "Sơ chế", "description": "Chuẩn bị nguyên liệu"},
            {"scene": 3, "type": "cooking", "name": "Chế biến chính", "description": "Công đoạn nấu chính"},
            {"scene": 4, "type": "reveal", "name": "Thành phẩm", "description": "Cận cảnh món ăn"},
            {"scene": 5, "type": "ending", "name": "Kết thúc", "description": "Nhân vật thưởng thức"},
        ],
        6: [
            {"scene": 1, "type": "intro", "name": "Giới thiệu", "description": "Nhân vật xuất hiện trong bối cảnh vùng miền"},
            {"scene": 2, "type": "preparation", "name": "Sơ chế", "description": "Cắt, thái, giã nguyên liệu"},
            {"scene": 3, "type": "cooking_1", "name": "Chế biến 1", "description": "Công đoạn chế biến chính (xào/nấu/nướng)"},
            {"scene": 4, "type": "cooking_2", "name": "Chế biến 2", "description": "Hoàn thiện thành phần phụ"},
            {"scene": 5, "type": "reveal", "name": "Trình bày", "description": "Cận cảnh thành phẩm (food porn style)"},
            {"scene": 6, "type": "ending", "name": "Kết thúc", "description": "Nhân vật tương tác với món ăn"},
        ],
        8: [
            {"scene": 1, "type": "intro", "name": "Mở đầu", "description": "Bối cảnh vùng miền (wide shot)"},
            {"scene": 2, "type": "character", "name": "Nhân vật", "description": "Giới thiệu nhân vật với nguyên liệu"},
            {"scene": 3, "type": "preparation_1", "name": "Sơ chế 1", "description": "Cắt thái nguyên liệu chính"},
            {"scene": 4, "type": "preparation_2", "name": "Sơ chế 2", "description": "Gia vị và nguyên liệu phụ"},
            {"scene": 5, "type": "cooking_1", "name": "Chế biến 1", "description": "Nấu/xào (hiệu ứng khói, lửa)"},
            {"scene": 6, "type": "cooking_2", "name": "Chế biến 2", "description": "Hoàn thiện món ăn"},
            {"scene": 7, "type": "reveal", "name": "Thành phẩm", "description": "Food reveal - cận cảnh chi tiết"},
            {"scene": 8, "type": "ending", "name": "Kết thúc", "description": "Nhân vật thưởng thức + thương hiệu"},
        ],
        10: [
            {"scene": 1, "type": "hook", "name": "Hook", "description": "Cảnh gây tò mò (3 giây)"},
            {"scene": 2, "type": "intro", "name": "Giới thiệu", "description": "Bối cảnh vùng miền (wide shot)"},
            {"scene": 3, "type": "character", "name": "Nhân vật", "description": "Nhân vật bước ra với nguyên liệu"},
            {"scene": 4, "type": "preparation_1", "name": "Sơ chế 1", "description": "Nguyên liệu chính"},
            {"scene": 5, "type": "preparation_2", "name": "Sơ chế 2", "description": "Gia vị, nguyên liệu phụ"},
            {"scene": 6, "type": "cooking_1", "name": "Chế biến 1", "description": "Nấu chính"},
            {"scene": 7, "type": "cooking_2", "name": "Chế biến 2", "description": "Hoàn thiện"},
            {"scene": 8, "type": "plating", "name": "Bày biện", "description": "Sắp xếp món ăn lên đĩa/mẹt"},
            {"scene": 9, "type": "reveal", "name": "Food Reveal", "description": "Cận cảnh chi tiết (macro shot)"},
            {"scene": 10, "type": "ending", "name": "Kết thúc", "description": "Thưởng thức + CTA"},
        ],
    }
    
    # Fallback: dùng template gần nhất
    available = sorted(templates.keys())
    closest = min(available, key=lambda x: abs(x - scene_count))
    return templates[closest]


def analyze_video_folder(input_dir: str, output_dir: str, num_frames: int = 5) -> dict:
    """Phân tích toàn bộ thư mục video."""
    video_extensions = {".mp4", ".avi", ".mov", ".mkv", ".webm", ".flv"}
    
    input_path = Path(input_dir)
    if not input_path.exists():
        print(f"[ERROR] Thư mục không tồn tại: {input_dir}")
        sys.exit(1)
    
    # Tìm tất cả video
    video_files = sorted([
        f for f in input_path.iterdir()
        if f.is_file() and f.suffix.lower() in video_extensions
    ])
    
    if not video_files:
        print(f"[ERROR] Không tìm thấy video trong: {input_dir}")
        sys.exit(1)
    
    print(f"[INFO] Tìm thấy {len(video_files)} video trong thư mục.")
    print(f"[INFO] Bắt đầu phân tích...\n")
    
    os.makedirs(output_dir, exist_ok=True)
    
    results = {
        "analysis_date": datetime.now().isoformat(),
        "source_directory": str(input_dir),
        "total_videos": len(video_files),
        "videos": [],
        "summary": {}
    }
    
    total_duration = 0
    orientations = {"vertical": 0, "horizontal": 0}
    
    for video_file in video_files:
        analysis = analyze_single_video(str(video_file), output_dir, num_frames)
        results["videos"].append(analysis)
        
        if "error" not in analysis:
            total_duration += analysis["metadata"]["duration_seconds"]
            orientation = analysis["analysis_notes"]["orientation"]
            orientations[orientation] = orientations.get(orientation, 0) + 1
    
    # Tổng hợp
    successful = [v for v in results["videos"] if "error" not in v or "metadata" in v]
    results["summary"] = {
        "total_videos_analyzed": len(successful),
        "total_duration_seconds": round(total_duration, 2),
        "total_duration_formatted": f"{int(total_duration // 60)}m {int(total_duration % 60)}s",
        "avg_duration_seconds": round(total_duration / max(len(successful), 1), 2),
        "orientations": orientations,
        "avg_estimated_scenes": round(
            sum(v.get("estimated_scene_count", 0) for v in successful) / max(len(successful), 1), 1
        ),
    }
    
    return results


def main():
    parser = argparse.ArgumentParser(
        description="Phân tích video mẫu - trích xuất metadata và frame cho việc tạo GPT prompt"
    )
    parser.add_argument(
        "--input", "-i",
        required=True,
        help="Đường dẫn thư mục chứa video mẫu"
    )
    parser.add_argument(
        "--output", "-o",
        default="analysis_output",
        help="Thư mục lưu kết quả phân tích (mặc định: analysis_output)"
    )
    parser.add_argument(
        "--frames", "-f",
        type=int,
        default=5,
        help="Số frame trích xuất mỗi video (mặc định: 5)"
    )
    
    args = parser.parse_args()
    
    # Phân tích
    results = analyze_video_folder(args.input, args.output, args.frames)
    
    # Lưu JSON
    output_file = os.path.join(args.output, "analysis.json")
    with open(output_file, "w", encoding="utf-8") as f:
        json.dump(results, f, ensure_ascii=False, indent=2)
    
    print(f"\n{'='*60}")
    print(f"[DONE] Phân tích hoàn tất!")
    print(f"  - Video đã phân tích: {results['summary']['total_videos_analyzed']}")
    print(f"  - Tổng thời lượng: {results['summary']['total_duration_formatted']}")
    print(f"  - TB thời lượng: {results['summary']['avg_duration_seconds']}s")
    print(f"  - TB số cảnh: {results['summary']['avg_estimated_scenes']}")
    print(f"  - Kết quả lưu tại: {output_file}")
    print(f"{'='*60}")


if __name__ == "__main__":
    main()

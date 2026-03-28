"""
Script tạo GPT System Prompt từ template chủ đề.

Hỗ trợ 3 chủ đề chính:
  - do_an_mini: Đồ ăn mini phong cách miniature 3D Pixar
  - suc_khoe: Video sức khỏe, thảo dược
  - du_lich: Du lịch, khám phá vùng miền

Usage:
    python scripts/create_gpt_prompt.py --theme "do_an_mini" --output "output/gpt_prompt_do_an_mini.md"
    python scripts/create_gpt_prompt.py --theme "suc_khoe" --output "output/gpt_prompt_suc_khoe.md"
    python scripts/create_gpt_prompt.py --theme "du_lich" --output "output/gpt_prompt_du_lich.md"
    python scripts/create_gpt_prompt.py --theme "custom" --analysis "analysis.json" --output "output/gpt_prompt_custom.md"
"""

import argparse
import json
import os
import sys
from pathlib import Path


# ============================================================
# ĐƯỜNG DẪN CƠ SỞ
# ============================================================

SKILL_DIR = Path(__file__).parent.parent
RESOURCES_DIR = SKILL_DIR / "resources"
TEMPLATES_DIR = SKILL_DIR / "templates"
OUTPUT_DIR = SKILL_DIR / "output"


# ============================================================
# TIỆN ÍCH ĐỌC DỮ LIỆU
# ============================================================

def load_regional_dishes() -> dict:
    """Đọc cơ sở dữ liệu món ăn vùng miền từ JSON."""
    dishes_path = RESOURCES_DIR / "regional_dishes.json"
    if dishes_path.exists():
        with open(dishes_path, "r", encoding="utf-8") as f:
            return json.load(f)
    return {}


def format_regional_dishes(dishes_data: dict) -> str:
    """Chuyển dữ liệu món ăn thành text dễ đọc cho GPT prompt."""
    if not dishes_data:
        return "(Chưa có dữ liệu món ăn)"

    lines = []
    for region_key, region_data in dishes_data.items():
        lines.append(f"\n### {region_data['name']}")
        for sub_key, sub_data in region_data["regions"].items():
            lines.append(f"\n#### 📍 {sub_data['name']}")
            lines.append(f"*Bối cảnh: {sub_data['backdrop']}*\n")
            for dish in sub_data["dishes"]:
                name_en = dish.get("name_en", "")
                name_display = f"{dish['name']} ({name_en})" if name_en else dish["name"]
                lines.append(f"- **{name_display}**")
                lines.append(f"  - Nguyên liệu: {dish['ingredients']}")
                steps = dish.get("steps", [])
                if isinstance(steps, list):
                    steps_text = " → ".join(steps)
                else:
                    steps_text = str(steps)
                lines.append(f"  - Quy trình: {steps_text}")
    return "\n".join(lines)


def load_character_reference() -> str:
    """Đọc file mô tả nhân vật."""
    char_path = RESOURCES_DIR / "character_reference.md"
    if char_path.exists():
        with open(char_path, "r", encoding="utf-8") as f:
            return f.read()
    return "(Chưa có dữ liệu nhân vật)"


# ============================================================
# GENERATOR CHO TỪNG CHỦ ĐỀ
# ============================================================

def generate_do_an_mini_prompt() -> str:
    """Tạo GPT system prompt cho chủ đề Đồ Ăn Mini.

    Đọc trực tiếp từ file output/gpt_prompt_do_an_mini.md đã được
    tinh chỉnh qua nhiều vòng lặp. Nếu file không tồn tại,
    tạo prompt mới từ template + dữ liệu.
    """
    # Ưu tiên đọc file đã tinh chỉnh
    existing_prompt = OUTPUT_DIR / "gpt_prompt_do_an_mini.md"
    if existing_prompt.exists():
        with open(existing_prompt, "r", encoding="utf-8") as f:
            content = f.read()
        if len(content) > 1000:  # File có nội dung thực
            return content

    # Fallback: tạo mới từ dữ liệu
    dishes = load_regional_dishes()
    dishes_text = format_regional_dishes(dishes)

    prompt = f"""# TRỢ LÝ AI — THẾ GIỚI ĐỒ ĂN MINI

## VAI TRÒ
Bạn là chuyên gia sáng tạo nội dung video cho kênh "Thế Giới Đồ Ăn Mini" — chuyên sản xuất video ngắn về ẩm thực Việt Nam theo phong cách hoạt hình 3D Pixar, thế giới thu nhỏ (miniature diorama), nơi các nhân vật tí hon nấu ăn giữa nguyên liệu và dụng cụ khổng lồ.

---

## THẾ GIỚI THU NHỎ — QUY TẮC KÍCH THƯỚC
- TẤT CẢ nhân vật đều cao **CHÍNH XÁC 4cm** — KHÔNG có nhân vật nào to hơn hay bé hơn
- Mọi thứ xung quanh họ đều **KHỔNG LỒ** so với kích thước cơ thể
- Họ phải bắc thang, dựng giàn giáo bằng tăm tre để nấu ăn trên bếp
- **DỤNG CỤ CÁ NHÂN PHẢI NHỎ**: Dao, bát, đũa, muỗng mà nhân vật cầm tay phải nhỏ tương xứng 4cm

---

## HỆ THỐNG NHÂN VẬT

### NHÂN VẬT CHÍNH — "Ti"
- Chibi mập mạp, áo bà ba xanh dương đậm, hở bụng mỡ, nón lá, khăn rằn
- Tính cách: LƯỜI LÀM, HAM CHƠI, ĂN VỤN — hài nhẹ nhàng, tự nhiên

### 4 ĐỒNG ĐỘI (2 nam + 2 nữ)
- CÙNG chiều cao 4cm với Ti
- TẤT CẢ mặc áo bà ba NÂU + quần đen
- Vai trò: Làm việc chăm chỉ

---

## PHONG CÁCH HÌNH ẢNH BẮT BUỘC
- 3D Pixar/Disney, miniature diorama
- Ánh sáng ấm áp, cinematographic, golden hour
- Màu sắc rực rỡ, food-porn style
- Tỷ lệ 9:16, chất lượng 8K

---

## QUY TRÌNH TƯƠNG TÁC

### Bước 1: Gợi ý 20 món ăn
Ngay khi bắt đầu, AI chủ động đưa danh sách 20 món đặc sản, mỗi món có tên + vùng miền + số cảnh gợi ý.

### Bước 2: Chi tiết món ăn
Tên món (Việt + Anh), vùng miền, nguyên liệu, quy trình chế biến, tình huống Ti phá hoại.

### Bước 3: Phân cảnh
Mặc định 6 cảnh × 8 giây. Cấu trúc: Thu thập → Sơ chế → Nấu → Hoàn thiện → Thưởng thức.

### Bước 4: Xuất prompt
3 ô code: (1) Prompt ảnh, (2) Prompt video Veo3, (3) Content media.

---

## CƠ SỞ DỮ LIỆU MÓN ĂN VÙNG MIỀN

{dishes_text}

---

## 10 QUY TẮC VÀNG
1. CÙNG KÍCH THƯỚC: Tất cả 5 nhân vật = 4cm
2. CHỈ 1 ÁO XANH = Ti
3. ĐỒNG PHỤC NÂU: 4 đồng đội mặc nâu
4. Ti LƯỜI + ĂN VỤN (chỉ đồ chín)
5. KHÔNG THOẠI — CHỈ ASMR
6. CHUYỂN ĐỘNG CHẬM (8s = 1 hành động)
7. HIỆU ỨNG VẬT LÝ (khói, lửa, nước)
8. BỐI CẢNH CHÍNH XÁC theo vùng miền
9. DỤNG CỤ NHỎ tương xứng 4cm
10. XUẤT ĐẦY ĐỦ 1 LẦN — 3 ô code

Hãy bắt đầu ngay bằng cách chào và đưa ra danh sách 20 món ăn gợi ý!
"""
    return prompt


def generate_suc_khoe_prompt() -> str:
    """Tạo GPT system prompt cho chủ đề Sức Khỏe."""
    return """# 🌿 TRỢ LÝ AI — VIDEO SỨC KHỎE THẢO DƯỢC

## VAI TRÒ
Bạn là chuyên gia sáng tạo nội dung video về sức khỏe và thảo dược Việt Nam. Phong cách: Pixar 3D animation, kịch bản "mắng mỏ" hài hước (scolding script).

## NHÂN VẬT
- **Bác sĩ Chibi**: Mặc áo blouse trắng, đeo ống nghe. Tính cách: nghiêm túc nhưng hài hước, hay "mắng" người dùng.
- **Thảo dược nhân hình**: Cây thuốc được nhân hóa (có tay chân, biểu cảm), xuất hiện khi được "triệu hồi".

## PHONG CÁCH
- 3D Pixar animation, nhân vật chibi
- Bối cảnh: vườn thảo dược, phòng thuốc cổ truyền
- Ánh sáng tự nhiên, ấm áp
- Tỷ lệ 9:16, chất lượng 8K

## CẤU TRÚC KỊCH BẢN 4 GIAI ĐOẠN (SCOLDING SCRIPT)

| Giai đoạn   | Cảnh  | Nội dung                                    | Giọng điệu       |
|-------------|-------|---------------------------------------------|-------------------|
| Dọa nạt     | Cảnh 1| Mô tả hậu quả khủng khiếp nếu không chữa   | Nghiêm trọng, dọa |
| Giải thích  | Cảnh 2| Giải thích nguyên nhân khoa học               | Giáo dục, rõ ràng |
| Hướng dẫn   | Cảnh 3| Chỉ bài thuốc/thảo dược cụ thể               | Tận tâm, chi tiết |
| CTA         | Cảnh 4| Kêu gọi hành động (like, follow, share)      | Thân thiện        |

## QUY TẮC SCRIPT
- Mỗi cảnh: **30-35 từ tiếng Việt** (không hơn)
- Giọng: Mắng mỏ nhẹ nhàng → hướng dẫn tận tâm
- KHÔNG nói quá mức y khoa
- Kèm disclaimer: "Tham khảo bác sĩ trước khi áp dụng"

## QUY TRÌNH TƯƠNG TÁC

### Bước 1: Chọn vấn đề sức khỏe
Gợi ý các chủ đề phổ biến:
- Đau đầu / Migraine
- Mất ngủ / Insomnia
- Tiêu hóa kém
- Đau lưng / Xương khớp
- Ho / Viêm họng
- Tăng huyết áp

### Bước 2: Chi tiết thảo dược
1. Tên thảo dược (Việt + tên khoa học)
2. Công dụng chính
3. Cách sử dụng (bài thuốc cụ thể)
4. Lưu ý / Chống chỉ định

### Bước 3: Phân cảnh (4 cảnh mặc định)
Theo cấu trúc Scolding Script ở trên.

### Bước 4: Xuất prompt
- Ô 1: Script lời thoại (tiếng Việt, 30-35 từ/cảnh)
- Ô 2: Prompt tạo ảnh (tiếng Anh)
- Ô 3: Prompt tạo video Veo3 (tiếng Anh)
- Ô 4: Content media (Facebook + YouTube + TikTok)

## FORMAT PROMPT ẢNH
```
[Mô tả cảnh], 3D Pixar animation style, miniature diorama world.
[Mô tả bác sĩ chibi + thảo dược nhân hình].
[Bối cảnh phòng khám/vườn thảo dược].
Warm natural lighting, 8K render, 9:16 vertical.
```

## FORMAT PROMPT VIDEO VEO3
```
A [kiểu camera] shot. [Bác sĩ chibi] speaks angrily: "[lời thoại]".
[Hiệu ứng: cây thuốc phát sáng / hơi nước / viên thuốc bay].
3D Pixar animation style, miniature diorama, 9:16 vertical.
```

**Lưu ý:** Chủ đề sức khỏe CÓ lời thoại (khác với đồ ăn mini = chỉ ASMR).

## THẢO DƯỢC THƯỜNG DÙNG
- **Gừng (Zingiber officinale)**: Giảm đau, chống viêm, ấm bụng
- **Nghệ (Curcuma longa)**: Bảo vệ gan, đẹp da, chống oxy hóa
- **Tỏi (Allium sativum)**: Kháng khuẩn, tăng miễn dịch
- **Mật ong**: Kháng viêm, bổ dưỡng, trị ho
- **Rau má (Centella asiatica)**: Thanh nhiệt, giải độc, đẹp da
- **Cúc hoa (Chrysanthemum)**: Sáng mắt, hạ huyết áp, an thần
- **Bạc hà (Mentha)**: Giảm đau đầu, thông mũi, giải cảm
- **Atiso (Cynara scolymus)**: Lợi gan, giải độc, hạ cholesterol

Hãy bắt đầu bằng cách hỏi người dùng đang gặp vấn đề sức khỏe gì!
"""


def generate_du_lich_prompt() -> str:
    """Tạo GPT system prompt cho chủ đề Du Lịch."""
    return """# 🏔️ TRỢ LÝ AI — VIDEO DU LỊCH VIỆT NAM

## VAI TRÒ
Bạn là chuyên gia sáng tạo nội dung video du lịch Việt Nam, chuyên sản xuất video ngắn giới thiệu địa điểm và trải nghiệm du lịch.

## NHÂN VẬT
- **Du khách Chibi**: Mặc áo phông, ba lô, nón bucket hat
- **Hướng dẫn viên Chibi**: Mặc đồng phục tour guide, cầm cờ nhỏ
- **Cư dân địa phương Chibi**: Trang phục vùng miền tương ứng

## PHONG CÁCH
- 3D Pixar animation, miniature diorama
- Nhân vật chibi du khách với ba lô
- Bối cảnh: các địa danh nổi tiếng Việt Nam
- Ánh sáng: golden hour, dramatic, cinematic

## QUY TRÌNH TƯƠNG TÁC

### Bước 1: Chọn vùng miền / địa điểm
Gợi ý các điểm đến phổ biến:

**Miền Bắc:**
- Hà Nội (phố cổ, Hồ Gươm, Văn Miếu)
- Hạ Long (vịnh, hang động, đảo)
- Sapa (ruộng bậc thang, đồng bào dân tộc)
- Ninh Bình (Tràng An, Bái Đính, Hang Múa)

**Miền Trung:**
- Huế (Kinh thành, sông Hương, cung đình)
- Đà Nẵng (Cầu Rồng, Bà Nà Hills, Mỹ Khê)
- Hội An (phố cổ, đèn lồng, sông Hoài)
- Phú Yên (Gành Đá Dĩa, Mũi Điện)

**Miền Nam:**
- Sài Gòn (Bến Thành, Nhà thờ Đức Bà)
- Đà Lạt (hoa, sương mù, đồi thông)
- Phú Quốc (biển, san hô, sunset)
- Miền Tây (chợ nổi, vườn trái cây, sông nước)

### Bước 2: Chi tiết trải nghiệm
1. Top 3 điểm đến phải ghé
2. Món ăn đặc sản phải thử
3. Trải nghiệm đặc biệt
4. Thời điểm đẹp nhất trong năm

### Bước 3: Phân cảnh (6-10 cảnh)
| Giai đoạn  | Nội dung |
|-----------|----------|
| Mở đầu   | Cảnh wide shot địa danh + nhân vật xuất hiện |
| Khám phá  | 3-6 cảnh khám phá các điểm đến |
| Ẩm thực   | 1-2 cảnh thưởng thức món ăn đặc sản |
| Kết thúc  | Cảnh sunset/hoàng hôn + cảm xúc |

### Bước 4: Xuất prompt
- Ô 1: Prompt tạo ảnh (tiếng Anh)
- Ô 2: Prompt tạo video Veo3 (tiếng Anh)
- Ô 3: Content media (Facebook + YouTube + TikTok)

## FORMAT PROMPT ẢNH
```
[Mô tả cảnh địa danh chi tiết], 3D Pixar animation style, miniature diorama.
[Nhân vật chibi du khách + trang phục].
[Bối cảnh: địa danh cụ thể với chi tiết kiến trúc/thiên nhiên].
Dramatic cinematic lighting, golden hour, 8K, 9:16 vertical.
```

## FORMAT PROMPT VIDEO VEO3
```
A [kiểu camera] shot of [cảnh địa danh miniature].
[Nhân vật chibi] [hành động: đi bộ, leo trèo, ngắm cảnh].
[Hiệu ứng: gió, mây trôi, sóng vỗ, nắng chiều].
No dialogue, ambient nature sounds only.
3D Pixar animation style, miniature diorama, 9:16 vertical.
```

## QUY TẮC
1. Bối cảnh phải chính xác kiến trúc/thiên nhiên của địa danh
2. Mỗi video kể 1 câu chuyện du lịch hoàn chỉnh
3. Phải có cảnh ẩm thực đặc sản
4. Cảnh cuối phải có yếu tố cảm xúc (hoàng hôn, kỷ niệm)
5. Âm thanh: chỉ tiếng môi trường (gió, sóng, chim hót)

Hãy bắt đầu bằng cách hỏi người dùng muốn đi du lịch vùng nào!
"""


# ============================================================
# ĐĂNG KÝ THEME
# ============================================================

THEME_GENERATORS = {
    "do_an_mini": generate_do_an_mini_prompt,
    "suc_khoe": generate_suc_khoe_prompt,
    "du_lich": generate_du_lich_prompt,
}

THEME_DESCRIPTIONS = {
    "do_an_mini": "🍜 Đồ ăn mini — Miniature 3D Pixar, ẩm thực Việt Nam",
    "suc_khoe": "🌿 Sức khỏe — Thảo dược, scolding script",
    "du_lich": "🏔️ Du lịch — Khám phá địa danh Việt Nam",
}


# ============================================================
# MAIN
# ============================================================

def main():
    parser = argparse.ArgumentParser(
        description="Tạo GPT System Prompt cho trợ lý nội dung video AI",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Ví dụ:
  python scripts/create_gpt_prompt.py --theme do_an_mini --output output/gpt_prompt_do_an_mini.md
  python scripts/create_gpt_prompt.py --theme suc_khoe --output output/gpt_prompt_suc_khoe.md
  python scripts/create_gpt_prompt.py --theme du_lich --output output/gpt_prompt_du_lich.md
  python scripts/create_gpt_prompt.py --list
        """
    )
    parser.add_argument(
        "--theme", "-t",
        choices=list(THEME_GENERATORS.keys()) + ["custom"],
        help="Chủ đề: do_an_mini, suc_khoe, du_lich, custom"
    )
    parser.add_argument(
        "--analysis", "-a",
        default=None,
        help="File analysis.json (bắt buộc nếu theme=custom)"
    )
    parser.add_argument(
        "--output", "-o",
        default=None,
        help="File đầu ra .md (mặc định: output/gpt_prompt_{theme}.md)"
    )
    parser.add_argument(
        "--list", "-l",
        action="store_true",
        help="Liệt kê tất cả theme có sẵn"
    )

    args = parser.parse_args()

    # Liệt kê theme
    if args.list:
        print("\n📋 CÁC CHỦ ĐỀ CÓ SẴN:\n")
        for theme_id, desc in THEME_DESCRIPTIONS.items():
            print(f"  {theme_id:15s} → {desc}")
        print(f"\n  {'custom':15s} → 📝 Tự định nghĩa từ file phân tích")
        print(f"\nSử dụng: python scripts/create_gpt_prompt.py --theme <theme_id>")
        return

    if not args.theme:
        parser.print_help()
        sys.exit(1)

    # Xử lý custom theme
    if args.theme == "custom":
        if not args.analysis:
            print("[ERROR] Theme 'custom' yêu cầu --analysis <file.json>")
            sys.exit(1)
        if not os.path.exists(args.analysis):
            print(f"[ERROR] File không tồn tại: {args.analysis}")
            sys.exit(1)
        print("[INFO] Custom theme — sử dụng do_an_mini làm base, kết hợp analysis data.")
        prompt = generate_do_an_mini_prompt()
    else:
        generator = THEME_GENERATORS[args.theme]
        prompt = generator()

    # Xác định output path
    if args.output:
        output_path = Path(args.output)
    else:
        output_path = OUTPUT_DIR / f"gpt_prompt_{args.theme}.md"

    # Tạo thư mục nếu chưa có
    output_path.parent.mkdir(parents=True, exist_ok=True)

    # Lưu file
    with open(output_path, "w", encoding="utf-8") as f:
        f.write(prompt)

    print(f"\n{'='*60}")
    print(f"[DONE] GPT prompt đã được tạo thành công!")
    print(f"{'='*60}")
    print(f"  📄 File:     {output_path}")
    print(f"  📏 Độ dài:   {len(prompt):,} ký tự")
    print(f"  🎯 Theme:    {THEME_DESCRIPTIONS.get(args.theme, args.theme)}")
    print(f"{'='*60}")
    print(f"\n💡 HƯỚNG DẪN TIẾP THEO:")
    print(f"  1. Mở file: {output_path}")
    print(f"  2. Copy toàn bộ nội dung")
    print(f"  3. Truy cập ChatGPT → Explore GPTs → Create")
    print(f"  4. Paste vào mục 'Instructions'")
    print(f"  5. Upload ảnh tham chiếu nhân vật (nếu có)")
    print(f"  6. Save & bắt đầu sử dụng!")
    print(f"{'='*60}")


if __name__ == "__main__":
    main()

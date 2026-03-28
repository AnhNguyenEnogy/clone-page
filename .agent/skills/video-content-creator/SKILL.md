---
name: Video Content Creator
description: Skill phân tích video mẫu và tạo trợ lý AI chuyên viết prompt tạo ảnh/video cho các chủ đề cụ thể (đồ ăn mini, sức khỏe, du lịch...). Hỗ trợ tạo GPT system prompt, kịch bản phân cảnh, prompt ảnh và prompt video.
---

# Video Content Creator — Skill Tạo Trợ Lý Nội Dung Video AI

## Tổng Quan

Skill này cung cấp **quy trình hoàn chỉnh** để:
1. **Phân tích video mẫu** → rút ra cấu trúc, phong cách, quy luật kịch bản
2. **Tạo GPT System Prompt** → trợ lý ChatGPT/GPT chuyên viết nội dung cho 1 chủ đề cụ thể
3. **Sinh prompt ảnh & video** → đầu ra chi tiết cho từng cảnh, sẵn sàng dùng với Veo3/DALL-E/Midjourney
4. **Sinh nội dung truyền thông** → bài đăng Facebook, YouTube, TikTok kèm theo video

---

## Quy Trình Tổng Thể (5 Bước)

```
┌─────────────────────────────────────────────────────────────────┐
│  BƯỚC 1: Phân tích video mẫu (analyze_videos.py)               │
│  ↓                                                              │
│  BƯỚC 2: Xác định chủ đề + hệ thống nhân vật                   │
│  ↓                                                              │
│  BƯỚC 3: Tạo GPT System Prompt (create_gpt_prompt.py)           │
│  ↓                                                              │
│  BƯỚC 4: Đưa prompt vào ChatGPT Custom GPT                      │
│  ↓                                                              │
│  BƯỚC 5: Sử dụng GPT để sinh prompt ảnh/video cho từng video    │
└─────────────────────────────────────────────────────────────────┘
```

---

## Bước 1: Phân Tích Video Mẫu

### Mục đích
Thu thập metadata + cấu trúc cảnh từ các video mẫu đã có, để hiểu rõ phong cách, nhịp độ, và cấu trúc kịch bản.

### Cách sử dụng

```bash
python scripts/analyze_videos.py --input "đường/dẫn/thư_mục_video" --output "analysis_output"
```

**Tham số:**
| Tham số     | Mô tả                               | Mặc định          |
|-------------|--------------------------------------|--------------------|
| `--input`   | Thư mục chứa video mẫu (.mp4, .mov) | (bắt buộc)         |
| `--output`  | Thư mục lưu kết quả                 | `analysis_output`  |
| `--frames`  | Số frame trích xuất mỗi video       | `5`                |

**Kết quả đầu ra:**
- `analysis_output/analysis.json` — metadata + cấu trúc cảnh ước tính
- `analysis_output/frames/` — frame trích xuất từ các video

### Cấu trúc JSON phân tích

```json
{
  "video_id": "864515759639970",
  "duration_seconds": 22,
  "resolution": "1080x1920",
  "estimated_scene_count": 6,
  "analysis_notes": {
    "suggested_scene_structure": [
      {"scene": 1, "type": "intro", "name": "Giới thiệu"},
      {"scene": 2, "type": "preparation", "name": "Sơ chế"},
      {"scene": 3, "type": "cooking", "name": "Chế biến"},
      {"scene": 4, "type": "reveal", "name": "Thành phẩm"}
    ],
    "orientation": "vertical"
  }
}
```

---

## Bước 2: Xác Định Chủ Đề & Nhân Vật

### Các chủ đề hỗ trợ

| Theme          | Mô tả                                     | Template                     | GPT Prompt Output               |
|----------------|--------------------------------------------|------------------------------|----------------------------------|
| `do_an_mini`   | Đồ ăn mini phong cách miniature 3D Pixar   | `templates/do_an_mini.md`    | `output/gpt_prompt_do_an_mini.md`|
| `suc_khoe`     | Video sức khỏe, thảo dược                  | `templates/suc_khoe.md`      | `output/gpt_prompt_suc_khoe.md`  |
| `du_lich`      | Du lịch, khám phá vùng miền                | `templates/du_lich.md`       | `output/gpt_prompt_du_lich.md`   |
| `custom`       | Tự định nghĩa từ file phân tích            | `templates/base_template.md` | tuỳ chọn                         |

### Hệ thống nhân vật (chủ đề `do_an_mini`)

Chi tiết đầy đủ xem tại: `resources/character_reference.md`

**Tóm tắt:**
- **Ti** (nam chính): Chibi mập, áo bà ba **xanh dương đậm**, hở bụng, nón lá, khăn rằn. Tính cách: lười, ham chơi, ăn vụng
- **4 đồng đội** (2 nam + 2 nữ): CÙNG chiều cao 4cm, TẤT CẢ mặc áo bà ba **NÂU** + quần đen. Vai trò: làm việc chăm chỉ
- **QUY TẮC TUYỆT ĐỐI**: 5 nhân vật đều cao 4cm, Ti KHÔNG được to hơn đồng đội

### Cơ sở dữ liệu nội dung

| File                             | Mô tả                                          |
|----------------------------------|-------------------------------------------------|
| `resources/regional_dishes.json` | 20+ món ăn đặc sản theo vùng miền Việt Nam      |
| `resources/character_reference.md`| Mô tả chi tiết nhân vật + prompt tham chiếu     |
| `resources/ti_tun_reference.png` | Ảnh tham chiếu nhân vật                          |

---

## Bước 3: Tạo GPT System Prompt

### Cách sử dụng

```bash
python scripts/create_gpt_prompt.py --theme "do_an_mini" --output "output/gpt_prompt_do_an_mini.md"
```

**Tham số:**
| Tham số       | Mô tả                                      | Mặc định         |
|---------------|---------------------------------------------|-------------------|
| `--theme`     | Chủ đề: `do_an_mini`, `suc_khoe`, `du_lich` | (bắt buộc)       |
| `--analysis`  | File analysis.json (chỉ cho `custom`)        | `None`            |
| `--output`    | File đầu ra .md                              | `gpt_prompt.md`   |

### Kết quả đầu ra

File `.md` chứa toàn bộ GPT System Prompt sẵn sàng copy-paste vào ChatGPT Custom GPT.

---

## Bước 4: Đưa Prompt Vào ChatGPT Custom GPT

### Cách thực hiện

1. Truy cập [ChatGPT](https://chat.openai.com) → **Explore GPTs** → **Create**
2. Trong tab **Configure**:
   - **Name**: Đặt tên GPT (VD: "Thế Giới Đồ Ăn Mini Creator")
   - **Instructions**: Copy toàn bộ nội dung file `gpt_prompt_*.md` vào đây
   - **Knowledge**: Upload ảnh tham chiếu nhân vật (`resources/ti_tun_reference.png`)
3. **Save** → Bắt đầu sử dụng

### Lưu ý khi sử dụng API

```python
import openai

system_prompt = open("output/gpt_prompt_do_an_mini.md", "r", encoding="utf-8").read()

response = openai.ChatCompletion.create(
    model="gpt-4",
    messages=[
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": "Hãy tạo kịch bản cho món Phở Bò Hà Nội, 6 cảnh"}
    ]
)
```

---

## Bước 5: Sử Dụng GPT Để Sinh Prompt

### Quy trình tương tác với GPT

```
Người dùng → Chọn món ăn từ danh sách 20 món gợi ý
        ↓
GPT → Trình bày chi tiết món ăn (nguyên liệu, quy trình, bối cảnh)
        ↓
Người dùng → Xác nhận hoặc tuỳ chỉnh số cảnh (mặc định 6)
        ↓
GPT → Xuất ra 3 ô code:
        Ô 1: TOÀN BỘ prompt tạo ảnh (tất cả cảnh)
        Ô 2: TOÀN BỘ prompt tạo video Veo3 (tất cả cảnh)
        Ô 3: Nội dung truyền thông (Facebook + YouTube + TikTok)
```

### Format đầu ra GPT

#### Ô 1: 📷 PROMPT TẠO ẢNH
- Mỗi cảnh = 1 prompt tiếng Anh, mô tả chi tiết
- Bắt buộc có: mô tả nhân vật, kích thước 4cm, phong cách 3D Pixar, 8K, 9:16
- Ti tham chiếu từ ảnh: `"Ti (the chubby chibi boy from the reference image)"`

#### Ô 2: 🎬 PROMPT TẠO VIDEO VEO3
- Mỗi cảnh = 1 prompt tiếng Anh, mô tả chuyển động + ASMR
- Bắt buộc: "No dialogue, no speech, only ASMR cooking sounds"
- Camera chậm, mượt mà, mỗi clip = 8 giây

#### Ô 3: 📱 CONTENT MEDIA
- Facebook: Tiêu đề + Nội dung tương tác cao + Hashtag
- YouTube: Tiêu đề + Mô tả chi tiết + Hashtag
- TikTok: Tiêu đề ngắn gọn + Nội dung xu hướng + Hashtag

---

## Cấu Trúc GPT System Prompt (Thành Phần)

Mỗi GPT prompt hoàn chỉnh bao gồm 7 phần:

| # | Phần                      | Mô tả                                                  |
|---|---------------------------|---------------------------------------------------------|
| 1 | Vai trò & Nhiệm vụ       | Định nghĩa persona cho trợ lý                          |
| 2 | Thế giới thu nhỏ          | Quy tắc kích thước nhân vật vs đồ vật                  |
| 3 | Hệ thống nhân vật         | Mô tả chi tiết từng nhân vật + quy tắc trang phục      |
| 4 | Phong cách hình ảnh       | Kiểu render, ánh sáng, màu sắc, chất lượng             |
| 5 | Quy trình tương tác       | Luồng hội thoại 4 bước với người dùng                   |
| 6 | Quy tắc vàng              | 10 quy tắc bắt buộc + danh sách lỗi cần tránh          |
| 7 | Ví dụ mẫu                 | Kịch bản hoàn chỉnh 6 cảnh với prompt ảnh + video       |

---

## Quy Trình Tạo Chủ Đề Mới (Từ Đầu)

Khi muốn tạo GPT cho một chủ đề hoàn toàn mới (không phải đồ ăn mini):

### 1. Chuẩn bị video mẫu
- Thu thập 5-10 video mẫu theo chủ đề
- Đặt tất cả vào 1 thư mục

### 2. Phân tích video
```bash
python scripts/analyze_videos.py --input "path/to/videos" --output "analysis_output"
```

### 3. Xem kết quả phân tích
- Mở `analysis_output/analysis.json`
- Xem các frame trong `analysis_output/frames/`
- Ghi chú: phong cách, nhịp độ, cấu trúc cảnh, nhân vật

### 4. Thiết kế nhân vật
- Tạo file mô tả nhân vật tương tự `resources/character_reference.md`
- Tạo ảnh tham chiếu bằng DALL-E/Midjourney
- Xác định: tên, trang phục, tính cách, quy tắc kích thước

### 5. Xây dựng cơ sở dữ liệu nội dung
- Tạo file JSON tương tự `resources/regional_dishes.json`
- Cấu trúc: vùng miền → địa điểm → nội dung cụ thể

### 6. Viết GPT System Prompt
Dựa trên `templates/base_template.md`, điền các phần:
- Vai trò → persona phù hợp chủ đề
- Nhân vật → hệ thống nhân vật đã thiết kế
- Quy trình tương tác → luồng hội thoại phù hợp
- Template prompt → format prompt ảnh + video
- Quy tắc → 10 quy tắc vàng cho chủ đề
- Ví dụ mẫu → 1 kịch bản hoàn chỉnh

### 7. Test & Tinh chỉnh
- Đưa prompt vào ChatGPT
- Thử tạo 2-3 kịch bản
- Kiểm tra: nhân vật nhất quán? Prompt ra ảnh đúng style? Lỗi gì?
- Cập nhật quy tắc dựa trên lỗi thực tế

---

## 10 Quy Tắc Vàng — Áp Dụng Cho MỌI Chủ Đề

1. **KÍCH THƯỚC NHẤT QUÁN**: Tất cả nhân vật PHẢI cùng kích thước trong prompt
2. **TRANG PHỤC PHÂN BIỆT**: Nhân vật chính mặc màu riêng, phụ mặc đồng phục
3. **KHÔNG LỐ / SLAPSTICK**: Hài hước nhẹ nhàng, tự nhiên
4. **KHÔNG THOẠI — CHỈ ASMR**: Video không có lời thoại, chỉ tiếng môi trường
5. **CHUYỂN ĐỘNG CHẬM**: 8 giây = 1 hành động chậm rãi, mượt mà
6. **HIỆU ỨNG VẬT LÝ**: Mỗi prompt video có ít nhất 1 hiệu ứng (khói, nước, lửa)
7. **BỐI CẢNH CHÍNH XÁC**: Bối cảnh phải gắn đúng vùng miền/chủ đề
8. **DỤNG CỤ NHỎ**: Dụng cụ cầm tay nhỏ tương xứng nhân vật
9. **FORMAT 3 Ô CODE**: Đầu ra GPT luôn có 3 ô: ảnh + video + media
10. **XUẤT ĐẦY ĐỦ 1 LẦN**: Tất cả cảnh trong cùng 1 ô code, không tách lẻ

---

## Danh Sách Lỗi Thường Gặp

| Lỗi                          | Mô tả                                               | Cách khắc phục trong prompt                                  |
|-------------------------------|------------------------------------------------------|--------------------------------------------------------------|
| Nhân vật chính to hơn phụ     | AI vẽ nhân vật chính khổng lồ so với đồng đội        | Ghi "All characters are identically the same tiny size"      |
| Nhiều nhân vật chính          | Xuất hiện 2+ nhân vật mặc cùng màu chính             | Ghi "Only ONE character wears [color] = [tên]"               |
| Đồng đội mặc sai màu         | Đồng đội mặc hồng, tím thay vì nâu                   | Ghi "ALL teammates wear [color] uniforms, NO other colors"   |
| Có lời thoại                 | Video có giọng nói/narration                          | Ghi "No dialogue, no speech, only ASMR sounds"               |
| Dụng cụ cá nhân quá to       | Bát, đũa to bằng nhân vật                             | Ghi "tiny personal [tool] proportional to character size"     |
| Ăn đồ sống                   | Nhân vật ăn thịt/cá sống                              | Ghi rõ loại đồ ăn đã chín hoặc ăn liền                       |
| Hài quá lố                   | Nhân vật ngã vào nồi, rơi vào bát                     | Không dùng "falls into", "crashes", "slips"                   |
| Đứng trên đồ ăn               | Nhân vật đứng/ngồi trong bát đồ ăn                    | Ghi "sitting on the rim, feet NOT touching food"              |

---

## File Ownership

| File                                | Mô tả                                  |
|-------------------------------------|-----------------------------------------|
| `SKILL.md`                          | File hướng dẫn chính (file này)         |
| `scripts/analyze_videos.py`         | Script phân tích video (ffprobe/ffmpeg) |
| `scripts/create_gpt_prompt.py`      | Script tạo GPT system prompt            |
| `templates/base_template.md`        | Template cơ sở cho mọi chủ đề           |
| `templates/do_an_mini.md`           | Template chủ đề đồ ăn mini              |
| `templates/suc_khoe.md`             | Template chủ đề sức khỏe                |
| `output/gpt_prompt_do_an_mini.md`   | GPT prompt hoàn chỉnh — đồ ăn mini     |
| `examples/sample_script.md`         | Ví dụ kịch bản mẫu (Bún Thang)         |
| `resources/regional_dishes.json`    | Cơ sở dữ liệu món ăn vùng miền         |
| `resources/character_reference.md`  | Mô tả nhân vật + prompt tham chiếu      |
| `resources/ti_tun_reference.png`    | Ảnh tham chiếu nhân vật                 |

---

## Tích Hợp Với Các Skill Khác

| Skill              | Tích hợp                                              |
|--------------------|-------------------------------------------------------|
| `pyqt-desktop-app` | Có thể tích hợp UI tạo prompt video vào app desktop   |
| `backend-developer`| API layer cho việc gọi GPT API tự động                |
| `ui-ux-developer`  | Thiết kế trang Video Content Creator trong app         |
| `i18n-specialist`  | Hỗ trợ đa ngôn ngữ cho prompt output                  |

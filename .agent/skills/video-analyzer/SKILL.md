---
name: Video Analyzer
description: Skill phân tích video bất kỳ bằng Gemini AI — tự động phát hiện nhân vật, phân cảnh, tạo prompt ảnh và prompt video (Veo3/Sora) để tái tạo video. Áp dụng cho mọi thể loại video (phim, quảng cáo, animation, vlog, giáo dục...).
---

# Video Analyzer — Skill Phân Tích Video & Tạo Prompt Tái Tạo

## Tổng Quan

Skill này cung cấp khả năng:
1. **Phân tích video bất kỳ** → AI tự phát hiện nhân vật, hành động, bối cảnh, camera, ánh sáng
2. **Phân cảnh tự động** → Chia video thành các cảnh 8 giây (chuẩn Veo3)
3. **Tạo prompt ảnh** → Prompt chi tiết để tạo frame đại diện cho mỗi cảnh
4. **Tạo prompt video** → Prompt chi tiết để tái tạo chuyển động, lời thoại, camera
5. **Tạo nội dung truyền thông** → Bài đăng Facebook, YouTube, TikTok
6. **Tạo kịch bản tiếng Việt** → Script phân cảnh đầy đủ

**Điểm khác biệt:** Skill này KHÔNG sử dụng nhân vật tham chiếu cố định — AI tự phân tích và mô tả chi tiết từng nhân vật trong video.

---

## Quy Trình Sử Dụng

```
Bước 1: Cung cấp video đầu vào
         ↓
Bước 2: Cấu hình tham số (tuỳ chọn)
         - Ngôn ngữ prompt (vi/en)
         - Thời lượng mục tiêu
         - Phong cách hình ảnh
         - Giọng đọc
         - Ảnh tham chiếu nhân vật (nếu muốn)
         ↓
Bước 3: Gemini AI phân tích video
         - Phát hiện nhân vật (ngoại hình, trang phục, tính cách)
         - Phân cảnh theo mốc 8 giây
         - Tạo prompt ảnh + video cho từng cảnh
         ↓
Bước 4: Đầu ra
         - Danh sách nhân vật (label + mô tả chi tiết)
         - Kịch bản tiếng Việt (vietnamese_script)
         - Prompt ảnh cho mỗi cảnh (image_prompt)
         - Prompt video Veo3 cho mỗi cảnh (veo_prompt)
         - Nội dung truyền thông (Facebook/YouTube/TikTok)
```

---

## Cách Gọi API

### Hàm chính

```python
from video_analyzer import analyze_video

result = analyze_video(
    video_path="path/to/video.mp4",
    target_duration="60s",           # Tuỳ chọn: thời lượng mục tiêu
    language="vi",                   # "vi" hoặc "en"
    voice_description="",            # Mô tả giọng đọc (nếu có)
    reference_image_paths=[],        # Ảnh tham chiếu nhân vật (tuỳ chọn)
    style="",                        # Phong cách hình ảnh (tuỳ chọn)
    lock_scene_count=True,           # Khoá số cảnh theo thời lượng?
    character_names=[],              # Tên nhân vật (tuỳ chọn)
    log_callback=print,             # Hàm log
)
```

### Kết quả trả về

```python
result.characters      # list[dict] — [{label, description}, ...]
result.vietnamese_script  # str — Kịch bản tiếng Việt phân cảnh
result.scenes          # list[AnalyzedScene] — [{scene_number, image_prompt, veo_prompt}, ...]
result.social_content  # SocialContent — {facebook, youtube, tiktok}
```

---

## Cấu Trúc Đầu Ra JSON

```json
{
  "characters": [
    {
      "label": "the wise old man",
      "description": "An elderly man around 70, weathered dark skin, deep wrinkles, short silver-grey hair, thick grey eyebrows, wearing a faded navy blue cotton vest over white undershirt, rolled-up khaki trousers, brown leather sandals, worn straw hat"
    }
  ],
  "vietnamese_script": "Cảnh 1: Ông lão ngồi dưới gốc cây bồ đề...\nCảnh 2: ...",
  "scenes": [
    {
      "scene_number": 1,
      "image_prompt": "the wise old man (an elderly man around 70, weathered dark skin...) sits under a large bodhi tree, medium shot, warm golden hour lighting...",
      "veo_prompt": "the wise old man (elderly, dark skin, navy vest, straw hat) slowly turns to face the camera, speaking gently: \"Con ơi, cuộc đời này...\" Camera: slow dolly in, warm sunset lighting..."
    }
  ],
  "social_content": {
    "facebook": {"title": "...", "content": "...", "hashtags": "..."},
    "youtube": {"title": "...", "content": "...", "hashtags": "..."},
    "tiktok": {"title": "...", "content": "...", "hashtags": "..."}
  }
}
```

---

## Các Chế Độ Phân Tích

### 1. Không có ảnh tham chiếu (Mặc định)
AI tự phân tích video và mô tả **CỰC KỲ CHI TIẾT** mỗi nhân vật:
- Khuôn mặt: hình dáng, tông da, mắt, mũi, miệng, lông mày
- Tóc: màu, độ dài, kiểu, kết cấu
- Thể hình: giới tính, tuổi, chiều cao, dáng người
- Trang phục: từng món đồ, màu sắc, chất liệu, pattern
- Phụ kiện: kính, trang sức, túi, nón

### 2. Có ảnh tham chiếu (Tuỳ chọn)
Chỉ nhân vật CÓ ảnh tham chiếu → dùng `"(character taken from reference image)"` thay cho mô tả.
Nhân vật KHÔNG có ảnh tham chiếu → vẫn mô tả chi tiết như bình thường.

### 3. Có chỉ định phong cách (Tuỳ chọn)
AI sẽ áp dụng phong cách đã chỉ định vào MỌI prompt thay vì tự detect từ video.

---

## Quy Tắc Phân Tích (13 Quy Tắc)

### Prompt Engineering

1. **8 giây/cảnh**: Mỗi cảnh = 1 clip Veo3 = đúng 8 giây
2. **Lời thoại nguyên văn**: Nếu có lời nói → ghi nguyên văn trong dấu ngoặc kép
3. **Nhịp thoại tự nhiên**: Lời thoại phải vừa đủ 8 giây, có khoảng dừng tự nhiên
4. **Camera chuyên nghiệp**: Dùng thuật ngữ cinematography (Pan, Dolly, Tracking, Crane...)
5. **Hành động vi mô**: Chia hành động phức tạp thành micro-action chi tiết
6. **Hiệu ứng vật lý**: Mỗi prompt video phải có ít nhất 1 hiệu ứng (khói, nước, ánh sáng...)

### Nhân vật

7. **Label nhất quán**: Mỗi nhân vật có 1 label cố định dùng xuyên suốt
8. **Nhân vật bắt buộc**: Mỗi prompt PHẢI bắt đầu bằng label nhân vật (nếu có)
9. **Mô tả đầy đủ**: Prompt ảnh phải có mô tả chi tiết nhân vật trong ngoặc đơn
10. **Không đổi tên**: Label trong `characters[]` = label trong mọi prompt

### Video hành động

11. **Ưu tiên chuyển động**: Video nhiều action → tập trung mô tả chuyển động
12. **Vật lý & trọng lượng**: Mô tả momentum, trọng lực, tốc độ
13. **Biểu cảm trong action**: Kể cả khi action nhanh, vẫn mô tả biểu cảm

---

## Xử Lý Lỗi API Key

Script có hệ thống quản lý API key tự động:
- **Round-robin**: Phân đều key cho các request
- **Auto-retry**: Nếu key lỗi → tự chuyển sang key khác
- **Mark quota**: Key hết quota → đánh dấu bỏ qua
- **Mark invalid**: Key không hợp lệ → xoá khỏi file
- **Thread-safe**: An toàn khi chạy đa luồng

---

## File Ownership

| File                          | Mô tả                                              |
|-------------------------------|------------------------------------------------------|
| `SKILL.md`                    | Hướng dẫn chính (file này)                           |
| `scripts/video_analyzer.py`   | Script chính — phân tích video bằng Gemini AI         |
| `scripts/api_key_manager.py`  | Quản lý API key (thread-safe, round-robin)            |
| `scripts/export_result.py`    | Xuất kết quả ra markdown/JSON                         |
| `examples/sample_output.json` | Ví dụ kết quả phân tích mẫu                          |
| `resources/voices.json`       | Danh sách giọng đọc có sẵn                            |

---

## Áp Dụng Cho Mọi Thể Loại Video

| Thể loại        | AI xử lý thế nào                                        |
|------------------|----------------------------------------------------------|
| Phim ngắn        | Phân tích nhân vật, lời thoại, camera, ánh sáng          |
| Animation 3D     | Detect style (Pixar/Disney/Anime), mô tả chi tiết        |
| Vlog/Review       | Phân tích người nói, cảnh quay, B-roll                    |
| Quảng cáo        | Phát hiện sản phẩm, nhân vật, CTA, branding               |
| Giáo dục         | Script lời thoại, visual aids, bối cảnh                    |
| Đồ ăn/Cooking    | Mô tả nguyên liệu, quy trình, close-up đồ ăn             |
| Action/Thể thao  | Micro-action breakdown, vật lý, tốc độ                    |
| Nhạc/Dance       | Nhịp điệu, chuyển động cơ thể, ánh sáng sân khấu         |
| Thiên nhiên      | Cảnh quan, thời tiết, ánh sáng, ambient sounds             |

---

## Tích Hợp Với Các Skill Khác

| Skill                  | Tích hợp                                                 |
|------------------------|----------------------------------------------------------|
| `video-content-creator`| Dùng kết quả phân tích → tạo GPT prompt cho chủ đề cụ thể|
| `pyqt-desktop-app`     | Tích hợp UI phân tích video vào app desktop               |
| `backend-developer`    | API layer cho batch processing                             |

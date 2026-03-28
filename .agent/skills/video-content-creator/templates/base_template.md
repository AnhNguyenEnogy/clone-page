# Base Template — Cấu Trúc GPT System Prompt

## Cấu trúc bắt buộc cho mỗi GPT System Prompt

### 1. Vai Trò & Nhiệm Vụ
```
Bạn là [vai trò cụ thể] cho kênh [tên kênh].
Nhiệm vụ: [mô tả nhiệm vụ chính]
Phong cách: [mô tả phong cách hình ảnh]
```

### 2. Phong Cách Hình Ảnh Bắt Buộc
- Kiểu rendering: [3D Pixar / Realistic / Cartoon / ...]
- Nhân vật: [mô tả nhân vật mẫu]
- Ánh sáng: [kiểu ánh sáng]
- Màu sắc: [bảng màu]
- Tỷ lệ: [9:16 / 16:9 / 1:1]
- Chất lượng: [4K / 8K / ...]

### 3. Quy Trình Tương Tác
```
Bước 1: Gợi ý & Lựa chọn [chủ đề]
Bước 2: Chi tiết [nội dung]
Bước 3: Phân cảnh (số cảnh tùy chỉnh)
Bước 4: Tạo Prompt (ảnh + video)
```

### 4. Template Prompt Ảnh
```
[Mô tả cảnh], [phong cách render], [mô tả nhân vật],
[bối cảnh], [ánh sáng], [màu sắc], [chất lượng],
[hiệu ứng], [tỷ lệ]
```

### 5. Template Prompt Video
```
[Mô tả chuyển động], camera [loại camera movement],
[hiệu ứng vật lý], [thời lượng],
[chất lượng], [phong cách]
```

### 6. Ràng Buộc Kỹ Thuật
- Nhất quán phong cách xuyên suốt video
- Keywords bắt buộc trong mỗi prompt
- Giới hạn số từ mỗi prompt
- Ngôn ngữ prompt (tiếng Anh cho generation)

### 7. Ví Dụ Mẫu
Ít nhất 1 kịch bản hoàn chỉnh với đầy đủ prompt cho mỗi cảnh

---

## Biến Tùy Chỉnh

| Biến               | Mô tả                          | Ví dụ                    |
| ------------------- | ------------------------------- | ------------------------ |
| `{theme}`           | Chủ đề nội dung                | đồ ăn mini               |
| `{channel_name}`    | Tên kênh                       | Thế Giới Đồ Ăn Mini     |
| `{render_style}`    | Phong cách render              | 3D Pixar animation       |
| `{character_desc}`  | Mô tả nhân vật                | 2 chibi dễ thương        |
| `{aspect_ratio}`    | Tỷ lệ khung hình              | 9:16                     |
| `{video_duration}`  | Thời lượng mục tiêu           | 20-25 giây               |
| `{default_scenes}`  | Số cảnh mặc định              | 6                        |
| `{quality}`         | Chất lượng render              | 8K                       |
| `{lighting}`        | Kiểu ánh sáng                 | warm cinematic            |

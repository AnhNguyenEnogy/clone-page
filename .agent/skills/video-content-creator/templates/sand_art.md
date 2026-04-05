# Template Sand Art Storytelling — Vẽ Cát Kể Chuyện

## Thông Tin Chủ Đề

| Thuộc tính | Giá trị |
|------------|---------|
| **Theme** | `sand_art` |
| **Tên** | Sand Art Storytelling — Vẽ Cát Kể Chuyện |
| **Đối tượng** | Trẻ em 2-8 tuổi, phụ huynh |
| **Phong cách** | Nghệ thuật vẽ cát trên lightbox |
| **Tỷ lệ** | 16:9 (ngang) |
| **Chất lượng** | 4K sand art animation |
| **Mỗi cảnh** | 8 giây (1 clip Veo3) |
| ** GPT Prompt Output** | `output/gpt_prompt_sand_art_storytelling.md` |

---

## 5 NGUYÊN TẮC VÀNG (BẮT BUỘC)

1.  **Góc máy**: Luôn sử dụng "Góc máy rộng từ trên xuống (top-down), đặt cố định trên bàn đèn."
2.  **Đôi tay nghệ nhân**: Luôn miêu tả tay rải cát, gạt, xoay, miết… để hình hiện ra từng bước.
3.  **Ánh sáng bàn đèn**: Luôn có "Ánh sáng xuyên thấu vàng hổ phách" hoặc "xanh lam".
4.  **Mô tả quá trình hình thành**: Nét cát phải từ từ hình thành qua thao tác của đôi tay, không được có sẵn.
5.  **Chuyển động sau khi hoàn thiện**: Sau khi hoàn thành, nhân vật khẽ cử động (bơi, đung đưa, nháy mắt, mỉm cười…).
6.  **Không có chữ**: Tuyệt đối không để chữ xuất hiện. Luôn thêm "Không có chữ xuất hiện." (No text, no titles).
7.  **Nhất quán nhân vật**: Phải mô tả chi tiết đặc điểm nhân vật (màu cát, vệt vẽ) và giữ nguyên mô tả đó xuyên suốt tất cả các cảnh. Chỉ thay đổi hành động và biểu cảm.

---

## CẤU TRÚC PROMPT VIDEO (5 PHẦN)

Mọi prompt video trong kịch bản phải tuân thủ:

1.  **Environment**: Góc máy rộng từ trên xuống (top-down) đặt cố định trên bàn đèn. Bề mặt cát mịn, ánh sáng xuyên thấu [màu].
2.  **Action**: Miêu tả thao tác đôi tay (sprinkle, sweep, swirl, trace, push...).
3.  **Creation**: Mô tả hình ảnh nhân vật/bối cảnh đang được vẽ dần bằng cát.
4.  **Lighting**: Ánh sáng bàn đèn xuyên thấu, lung linh, cảm giác thủ công tinh xảo. Không có chữ.
5.  **Motion**: Sau khi hoàn thiện bức tranh, [nhân vật] khẽ chuyển động [hành động].

---

## Cấu Trúc Câu Chuyện (Mặc định 7 Cảnh)

| # | Giai đoạn | Nội dung | Thao tác cát chính |
|---|-----------|----------|-------------------|
| 1 | Mở đầu/Giới thiệu | Nhân vật xuất hiện | Rải cát tạo nền, miết nét nhân vật |
| 2 | Phát triển | Bối cảnh câu chuyện | Thêm chi tiết bối cảnh xung quanh |
| 3 | Xung đột 1 | Sự kiện xảy ra | Thay đổi nét mặt, di chuyển cát |
| 4 | Xung đột 2 | Phản ứng nhân vật | Sửa biểu cảm (close-up) |
| 5 | Hậu quả | Kết quả/Bài học | Gom cát tạo bóng đổ, biểu cảm buồn |
| 6 | Sửa sai | Hành động đúng | Gạt cát vẽ lại nét tươi sáng |
| 7 | Kết thúc | Happy ending | Chấm cát lung linh, chuyển động vui |

---

## Keywords Bắt Buộc cho Video

```
"Sand art performance on a bright backlit lightbox"
"Top-down view"
"Two real human hands"
"Sprinkle, spread, trace, push, dab"
"Backlight glow"
"No speech"
"No text, no titles, no captions"
"8 seconds"
```

---

## Biến Tùy Chỉnh

| Biến | Mô tả | Ví dụ |
|------|--------|-------|
| `{story_title}` | Tên câu chuyện | Thỏ Trắng Không Đánh Răng |
| `{character_1}` | Nhân vật chính | Thỏ Trắng (cream-white sand) |
| `{character_2}` | Nhân vật phụ | Cáo Cam (reddish-orange sand) |
| `{lesson}` | Bài học | Đánh răng mỗi ngày |
| `{scene_count}` | Số cảnh | 7 |
| `{aspect_ratio}` | Tỷ lệ | 16:9 |
| `{quality}` | Chất lượng | 4K sand art |
| `{light_color}` | Màu ánh sáng | Amber yellow / Amber blue |

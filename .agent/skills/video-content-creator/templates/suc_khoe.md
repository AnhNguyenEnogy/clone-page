# Template — Sức Khỏe & Thảo Dược

## Metadata

| Thuộc tính         | Giá trị                                           |
|--------------------|----------------------------------------------------|
| Theme ID           | `suc_khoe`                                         |
| Tên kênh           | [Tùy chỉnh: VD "Bí Quyết Sức Khỏe"]              |
| Phong cách render  | 3D Pixar Animation, Miniature Diorama              |
| Tỷ lệ khung hình  | 9:16 (dọc, TikTok/Reels)                          |
| Chất lượng         | 8K render quality                                   |
| Mỗi cảnh           | 8 giây (1 clip Veo3)                               |
| Số cảnh mặc định   | 4 cảnh (kịch bản mắng — scolding script)           |
| Âm thanh           | Có lời thoại (giọng mắng mỏ, dọa nạt hài hước)    |

---

## Hệ Thống Nhân Vật

### Nhân vật chính — Bác sĩ Chibi
- **Hình dáng**: Chibi dễ thương, mặc áo blouse trắng, đeo ống nghe
- **Tính cách**: Nghiêm túc nhưng hài hước, hay "mắng" người dùng vì thói quen xấu
- **Phong cách giảng dạy**: Dọa → Giải thích → Hướng dẫn → Kêu gọi

### Nhân vật phụ — Thảo dược nhân hình
- **Hình dáng**: Cây thảo dược được nhân hóa (có tay chân, biểu cảm)
- **Vai trò**: Xuất hiện khi được "triệu hồi" bởi bác sĩ để giải quyết vấn đề

---

## Cấu Trúc Kịch Bản 4 Giai Đoạn (Scolding Script)

| Giai đoạn   | Cảnh  | Nội dung                                    | Giọng điệu       |
|-------------|-------|---------------------------------------------|-------------------|
| Dọa nạt     | Cảnh 1| Mô tả hậu quả khủng khiếp nếu không chữa   | Nghiêm trọng, dọa |
| Giải thích  | Cảnh 2| Giải thích nguyên nhân khoa học               | Giáo dục, rõ ràng |
| Hướng dẫn   | Cảnh 3| Chỉ bài thuốc/thảo dược cụ thể               | Tận tâm, chi tiết |
| CTA         | Cảnh 4| Kêu gọi hành động (like, follow, share)      | Thân thiện        |

---

## Quy Tắc Script

- Mỗi cảnh: **30-35 từ tiếng Việt** (không hơn)
- Giọng điệu: Mắng mỏ nhẹ nhàng → chuyển sang hướng dẫn tận tâm
- KHÔNG nói quá mức y khoa (chỉ mức dân gian / thảo dược)
- Luôn kèm disclaimer: "Tham khảo bác sĩ trước khi áp dụng"

---

## Format Prompt Ảnh

```
[Mô tả cảnh], 3D Pixar animation style, miniature diorama world.
[Mô tả nhân vật bác sĩ chibi + thảo dược].
[Bối cảnh: phòng khám / vườn thảo dược / nhà bếp].
Warm natural lighting, 8K render quality, detailed textures, 9:16 vertical.
```

---

## Format Prompt Video Veo3

```
A [kiểu camera] shot of [mô tả cảnh].
[Nhân vật bác sĩ chibi] speaks angrily: "[lời thoại tiếng Việt]".
[Hiệu ứng: cây thuốc phát sáng / hơi nước bốc lên / viên thuốc bay].
3D Pixar animation style, miniature diorama, warm lighting, 9:16 vertical.
```

**Lưu ý:** Chủ đề sức khỏe CÓ lời thoại (khác với đồ ăn mini là ASMR).

---

## Cơ Sở Dữ Liệu Chủ Đề Sức Khỏe

### Nhóm 1: Thảo dược thường gặp
- Gừng (giảm đau, chống viêm)
- Nghệ (bảo vệ gan, đẹp da)
- Tỏi (kháng khuẩn, tăng miễn dịch)
- Mật ong (kháng viêm, bổ dưỡng)
- Rau má (thanh nhiệt, giải độc)

### Nhóm 2: Vấn đề sức khỏe
- Đau đầu / Migraine
- Mất ngủ / Insomnia
- Tiêu hóa kém
- Đau lưng / Xương khớp
- Tăng huyết áp
- Ho / Viêm họng

---

## Checklist Prompt Sức Khỏe

- [ ] Script đúng 30-35 từ/cảnh?
- [ ] Đúng 4 giai đoạn (Dọa → Giải thích → Hướng dẫn → CTA)?
- [ ] Thảo dược được mô tả chính xác (tên khoa học nếu cần)?
- [ ] Có disclaimer y khoa?
- [ ] Nhân vật nhất quán xuyên suốt video?
- [ ] Hiệu ứng vật lý có trong mỗi prompt video?

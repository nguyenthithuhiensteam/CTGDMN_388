# IMPORT_CORE_REPORT.md

## Báo cáo import dữ liệu lõi CT388

- Thời điểm import: `2026-08-05 14:31:15`
- Phạm vi: chỉ import sheet lõi; không import hồ sơ cá nhân, portfolio, bảng kiểm lớp, nhật ký quan sát.
- Cơ chế chạy lại: KHÔNG xóa dữ liệu lõi cũ — mọi bảng ghi qua upsert theo mã ổn định (hoặc find-or-update theo tiêu đề), giữ nguyên id đã có, an toàn khi chạy lại nhiều lần.
- Dọn rác từ lỗi import trước đây: xóa `1` hoạt động và `22` lĩnh vực rác đã xác nhận không còn bị tham chiếu.

## Tổng hợp theo sheet

| File | Sheet | Dòng đọc | Import thành công | Bỏ qua | Cảnh báo |
|---|---|---:|---:|---:|---|
| `BoTaiLieu_MauGiao_3-6T_CT388_2026-2027.xlsx` | `KHUNGNL` | 30 | 30 | 0 | Có cột Column N không rõ nhãn; đã bỏ qua các cột này. |
| `BoTaiLieu_MauGiao_3-6T_CT388_2026-2027.xlsx` | `MATRANYCCD` | 30 | 30 | 0 | Có cột Column N không rõ nhãn; đã bỏ qua các cột này. |
| `BoTaiLieu_MauGiao_3-6T_CT388_2026-2027.xlsx` | `NGANHANGHD` | 30 | 30 | 0 | Có cột Column N không rõ nhãn; đã bỏ qua các cột này. |
| `BoTaiLieu_MauGiao_3-6T_CT388_2026-2027.xlsx` | `RUBRIC` | 30 | 30 | 0 | Có cột Column N không rõ nhãn; đã bỏ qua các cột này. |
| `BoTaiLieu_MauGiao_3-6T_CT388_2026-2027.xlsx` | `KHNAM_3_4T` | 52 | 30 | 22 | Có cột Column N không rõ nhãn; đã bỏ qua các cột này. |
| `BoTaiLieu_MauGiao_3-6T_CT388_2026-2027.xlsx` | `KHNAM_4_5T` | 52 | 30 | 22 | Có cột Column N không rõ nhãn; đã bỏ qua các cột này. |
| `BoTaiLieu_MauGiao_3-6T_CT388_2026-2027.xlsx` | `KHNAM_5_6T` | 52 | 30 | 22 | Có cột Column N không rõ nhãn; đã bỏ qua các cột này. |
| `BoTaiLieu_NhaTre_12-36T_CT388_2026-2027_DieuChinh.xlsx` | `6. CẦU NỐI KHUNG NL` | 6 | 5 | 1 |  |
| `BoTaiLieu_NhaTre_12-36T_CT388_2026-2027_DieuChinh.xlsx` | `8. NGÂN HÀNG HOẠT ĐỘNG` | 9 | 8 | 1 | Có cột Column N không rõ nhãn; đã bỏ qua các cột này. |
| `BoTaiLieu_NhaTre_12-36T_CT388_2026-2027_DieuChinh.xlsx` | `8. NGÂN HÀNG HOẠT ĐỘNG` | 19 | 19 | 0 | Có cột Column N không rõ nhãn; đã bỏ qua các cột này. |
| `BoTaiLieu_NhaTre_12-36T_CT388_2026-2027_DieuChinh.xlsx` | `8. NGÂN HÀNG HOẠT ĐỘNG` | 22 | 22 | 0 | Có cột Column N không rõ nhãn; đã bỏ qua các cột này. |
| `BoTaiLieu_NhaTre_12-36T_CT388_2026-2027_DieuChinh.xlsx` | `8. NGÂN HÀNG HOẠT ĐỘNG` | 14 | 14 | 0 | Có cột Column N không rõ nhãn; đã bỏ qua các cột này. |
| `BoTaiLieu_NhaTre_12-36T_CT388_2026-2027_DieuChinh.xlsx` | `8. NGÂN HÀNG HOẠT ĐỘNG` | 16 | 16 | 0 | Có cột Column N không rõ nhãn; đã bỏ qua các cột này. |
| `BoTaiLieu_NhaTre_12-36T_CT388_2026-2027_DieuChinh.xlsx` | `8. NGÂN HÀNG HOẠT ĐỘNG` | 11 | 11 | 0 | Có cột Column N không rõ nhãn; đã bỏ qua các cột này. |
| `BoTaiLieu_NhaTre_12-36T_CT388_2026-2027_DieuChinh.xlsx` | `9b. GIÁO DỤC TRONG SINH HOẠT` | 6 | 6 | 0 |  |
| `BoTaiLieu_NhaTre_12-36T_CT388_2026-2027_DieuChinh.xlsx` | `11. RUBRIC NHÀ TRẺ` | 82 | 82 | 0 |  |
| `BoTaiLieu_NhaTre_12-36T_CT388_2026-2027_DieuChinh.xlsx` | `2. FRAMEWORK` | 82 | 82 | 0 | Có cột Column N không rõ nhãn; đã bỏ qua các cột này. |

## Lý do bỏ qua

### `KHNAM_3_4T`
- Thiếu Lĩnh vực/Mã/Mục tiêu năm học: `22` dòng
  - Dòng 40: Thiếu Lĩnh vực/Mã/Mục tiêu năm học
  - Dòng 41: Thiếu Lĩnh vực/Mã/Mục tiêu năm học
  - Dòng 42: Thiếu Lĩnh vực/Mã/Mục tiêu năm học
  - Dòng 43: Thiếu Lĩnh vực/Mã/Mục tiêu năm học
  - Dòng 44: Thiếu Lĩnh vực/Mã/Mục tiêu năm học
  - Dòng 45: Thiếu Lĩnh vực/Mã/Mục tiêu năm học
  - Dòng 46: Thiếu Lĩnh vực/Mã/Mục tiêu năm học
  - Dòng 47: Thiếu Lĩnh vực/Mã/Mục tiêu năm học
  - Dòng 48: Thiếu Lĩnh vực/Mã/Mục tiêu năm học
  - Dòng 49: Thiếu Lĩnh vực/Mã/Mục tiêu năm học
  - Dòng 50: Thiếu Lĩnh vực/Mã/Mục tiêu năm học
  - Dòng 51: Thiếu Lĩnh vực/Mã/Mục tiêu năm học
  - Dòng 53: Thiếu Lĩnh vực/Mã/Mục tiêu năm học
  - Dòng 54: Thiếu Lĩnh vực/Mã/Mục tiêu năm học
  - Dòng 55: Thiếu Lĩnh vực/Mã/Mục tiêu năm học
  - Dòng 56: Thiếu Lĩnh vực/Mã/Mục tiêu năm học
  - Dòng 57: Thiếu Lĩnh vực/Mã/Mục tiêu năm học
  - Dòng 58: Thiếu Lĩnh vực/Mã/Mục tiêu năm học
  - Dòng 60: Thiếu Lĩnh vực/Mã/Mục tiêu năm học
  - Dòng 61: Thiếu Lĩnh vực/Mã/Mục tiêu năm học
  - Dòng 63: Thiếu Lĩnh vực/Mã/Mục tiêu năm học
  - Dòng 64: Thiếu Lĩnh vực/Mã/Mục tiêu năm học
### `KHNAM_4_5T`
- Thiếu Lĩnh vực/Mã/Mục tiêu năm học: `22` dòng
  - Dòng 40: Thiếu Lĩnh vực/Mã/Mục tiêu năm học
  - Dòng 41: Thiếu Lĩnh vực/Mã/Mục tiêu năm học
  - Dòng 42: Thiếu Lĩnh vực/Mã/Mục tiêu năm học
  - Dòng 43: Thiếu Lĩnh vực/Mã/Mục tiêu năm học
  - Dòng 44: Thiếu Lĩnh vực/Mã/Mục tiêu năm học
  - Dòng 45: Thiếu Lĩnh vực/Mã/Mục tiêu năm học
  - Dòng 46: Thiếu Lĩnh vực/Mã/Mục tiêu năm học
  - Dòng 47: Thiếu Lĩnh vực/Mã/Mục tiêu năm học
  - Dòng 48: Thiếu Lĩnh vực/Mã/Mục tiêu năm học
  - Dòng 49: Thiếu Lĩnh vực/Mã/Mục tiêu năm học
  - Dòng 50: Thiếu Lĩnh vực/Mã/Mục tiêu năm học
  - Dòng 51: Thiếu Lĩnh vực/Mã/Mục tiêu năm học
  - Dòng 53: Thiếu Lĩnh vực/Mã/Mục tiêu năm học
  - Dòng 54: Thiếu Lĩnh vực/Mã/Mục tiêu năm học
  - Dòng 55: Thiếu Lĩnh vực/Mã/Mục tiêu năm học
  - Dòng 56: Thiếu Lĩnh vực/Mã/Mục tiêu năm học
  - Dòng 57: Thiếu Lĩnh vực/Mã/Mục tiêu năm học
  - Dòng 58: Thiếu Lĩnh vực/Mã/Mục tiêu năm học
  - Dòng 60: Thiếu Lĩnh vực/Mã/Mục tiêu năm học
  - Dòng 61: Thiếu Lĩnh vực/Mã/Mục tiêu năm học
  - Dòng 63: Thiếu Lĩnh vực/Mã/Mục tiêu năm học
  - Dòng 64: Thiếu Lĩnh vực/Mã/Mục tiêu năm học
### `KHNAM_5_6T`
- Thiếu Lĩnh vực/Mã/Mục tiêu năm học: `22` dòng
  - Dòng 40: Thiếu Lĩnh vực/Mã/Mục tiêu năm học
  - Dòng 41: Thiếu Lĩnh vực/Mã/Mục tiêu năm học
  - Dòng 42: Thiếu Lĩnh vực/Mã/Mục tiêu năm học
  - Dòng 43: Thiếu Lĩnh vực/Mã/Mục tiêu năm học
  - Dòng 44: Thiếu Lĩnh vực/Mã/Mục tiêu năm học
  - Dòng 45: Thiếu Lĩnh vực/Mã/Mục tiêu năm học
  - Dòng 46: Thiếu Lĩnh vực/Mã/Mục tiêu năm học
  - Dòng 47: Thiếu Lĩnh vực/Mã/Mục tiêu năm học
  - Dòng 48: Thiếu Lĩnh vực/Mã/Mục tiêu năm học
  - Dòng 49: Thiếu Lĩnh vực/Mã/Mục tiêu năm học
  - Dòng 50: Thiếu Lĩnh vực/Mã/Mục tiêu năm học
  - Dòng 51: Thiếu Lĩnh vực/Mã/Mục tiêu năm học
  - Dòng 53: Thiếu Lĩnh vực/Mã/Mục tiêu năm học
  - Dòng 54: Thiếu Lĩnh vực/Mã/Mục tiêu năm học
  - Dòng 55: Thiếu Lĩnh vực/Mã/Mục tiêu năm học
  - Dòng 56: Thiếu Lĩnh vực/Mã/Mục tiêu năm học
  - Dòng 57: Thiếu Lĩnh vực/Mã/Mục tiêu năm học
  - Dòng 58: Thiếu Lĩnh vực/Mã/Mục tiêu năm học
  - Dòng 60: Thiếu Lĩnh vực/Mã/Mục tiêu năm học
  - Dòng 61: Thiếu Lĩnh vực/Mã/Mục tiêu năm học
  - Dòng 63: Thiếu Lĩnh vực/Mã/Mục tiêu năm học
  - Dòng 64: Thiếu Lĩnh vực/Mã/Mục tiêu năm học
### `6. CẦU NỐI KHUNG NL`
- Dòng ghi chú cuối bảng, không phải lĩnh vực: `1` dòng
  - Dòng 12: Dòng ghi chú cuối bảng, không phải lĩnh vực
### `8. NGÂN HÀNG HOẠT ĐỘNG`
- Thiếu Mã hoặc Hoạt động gợi ý: `1` dòng
  - Dòng 15: Thiếu Mã hoặc Hoạt động gợi ý

## Danh sách sheet import được

- `BoTaiLieu_MauGiao_3-6T_CT388_2026-2027.xlsx` / `KHUNGNL`: `30` dòng
- `BoTaiLieu_MauGiao_3-6T_CT388_2026-2027.xlsx` / `MATRANYCCD`: `30` dòng
- `BoTaiLieu_MauGiao_3-6T_CT388_2026-2027.xlsx` / `NGANHANGHD`: `30` dòng
- `BoTaiLieu_MauGiao_3-6T_CT388_2026-2027.xlsx` / `RUBRIC`: `30` dòng
- `BoTaiLieu_MauGiao_3-6T_CT388_2026-2027.xlsx` / `KHNAM_3_4T`: `30` dòng
- `BoTaiLieu_MauGiao_3-6T_CT388_2026-2027.xlsx` / `KHNAM_4_5T`: `30` dòng
- `BoTaiLieu_MauGiao_3-6T_CT388_2026-2027.xlsx` / `KHNAM_5_6T`: `30` dòng
- `BoTaiLieu_NhaTre_12-36T_CT388_2026-2027_DieuChinh.xlsx` / `6. CẦU NỐI KHUNG NL`: `5` dòng
- `BoTaiLieu_NhaTre_12-36T_CT388_2026-2027_DieuChinh.xlsx` / `8. NGÂN HÀNG HOẠT ĐỘNG`: `8` dòng
- `BoTaiLieu_NhaTre_12-36T_CT388_2026-2027_DieuChinh.xlsx` / `8. NGÂN HÀNG HOẠT ĐỘNG`: `19` dòng
- `BoTaiLieu_NhaTre_12-36T_CT388_2026-2027_DieuChinh.xlsx` / `8. NGÂN HÀNG HOẠT ĐỘNG`: `22` dòng
- `BoTaiLieu_NhaTre_12-36T_CT388_2026-2027_DieuChinh.xlsx` / `8. NGÂN HÀNG HOẠT ĐỘNG`: `14` dòng
- `BoTaiLieu_NhaTre_12-36T_CT388_2026-2027_DieuChinh.xlsx` / `8. NGÂN HÀNG HOẠT ĐỘNG`: `16` dòng
- `BoTaiLieu_NhaTre_12-36T_CT388_2026-2027_DieuChinh.xlsx` / `8. NGÂN HÀNG HOẠT ĐỘNG`: `11` dòng
- `BoTaiLieu_NhaTre_12-36T_CT388_2026-2027_DieuChinh.xlsx` / `9b. GIÁO DỤC TRONG SINH HOẠT`: `6` dòng
- `BoTaiLieu_NhaTre_12-36T_CT388_2026-2027_DieuChinh.xlsx` / `11. RUBRIC NHÀ TRẺ`: `82` dòng
- `BoTaiLieu_NhaTre_12-36T_CT388_2026-2027_DieuChinh.xlsx` / `2. FRAMEWORK`: `82` dòng

## Danh sách sheet cần kiểm tra thủ công

- Nhà trẻ: 1. ĐỒNG BỘ KẾ HOẠCH
- Nhà trẻ: 3. THƯ VIỆN SỐ
- Nhà trẻ: 4. TRA CỨU NHANH
- Nhà trẻ: 7. KHUNG NL TÓM TẮT
- Mẫu giáo: MOCPT
- Mẫu giáo: PHIENCHE
- Hồ sơ cá nhân/portfolio/bảng kiểm lớp/nhật ký quan sát

## Điểm schema cần cân nhắc trước import sâu

- Thiếu bảng nối activity-competency, activity-quality, plan-yccd.
- milestones chưa có competency_id/yccd_id nên mốc đang lưu gián tiếp qua title/description.
- activities thiếu cột riêng cho câu hỏi, biểu hiện, minh chứng, hòa nhập, mở rộng; giữ trong notes.
- year_plans thiếu bảng chi tiết mục tiêu năm theo mã; mỗi mục tiêu lưu thành một dòng.

## Số bản ghi hiện có trong database

| Bảng | Số bản ghi |
|---|---:|
| `age_groups` | 5 |
| `domains` | 10 |
| `competencies` | 125 |
| `qualities` | 11 |
| `yccd` | 112 |
| `milestones` | 992 |
| `activities` | 126 |
| `rubrics` | 112 |
| `year_plans` | 90 |
| `month_plans` | 0 |
| `week_plans` | 0 |
| `day_plans` | 0 |
| `schools` | 34 |
| `users` | 34 |
| `children` | 1 |
| `observations` | 0 |
| `assessments` | 0 |
| `portfolio` | 0 |
| `school_settings` | 0 |
| `licenses` | 0 |

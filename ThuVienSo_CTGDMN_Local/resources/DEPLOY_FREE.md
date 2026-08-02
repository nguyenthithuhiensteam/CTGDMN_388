# Triển khai miễn phí (không cần thẻ thanh toán)

Kết hợp: **Render** (chạy web + API, gói Free) + **Neon** (database PostgreSQL, gói Free, không tự xoá dữ liệu).

## 1. Tạo database PostgreSQL miễn phí trên Neon
1. Vào [neon.tech](https://neon.tech) → **Sign up** (đăng ký bằng Google hoặc GitHub cho nhanh, không cần thẻ)
2. Sau khi vào dashboard, bấm **Create a project** (hoặc project mặc định đã tự tạo sẵn)
3. Đặt tên project (vd: `ct388`), chọn region gần Việt Nam nhất (vd: Singapore nếu có)
4. Vào phần **Connection Details** / **Connection string** của project → copy chuỗi kết nối, dạng:
   `postgresql://neondb_owner:xxxxx@ep-xxxx-xxxx.ap-southeast1.aws.neon.tech/neondb?sslmode=require`
5. Giữ lại chuỗi này — sẽ dùng làm biến `DATABASE_URL` ở bước sau

## 2. Deploy web service miễn phí trên Render
1. Vào [render.com](https://render.com) → **Sign up** (đăng ký bằng GitHub cho nhanh, không cần thẻ)
2. Bấm **New +** → **Blueprint**
3. Kết nối tài khoản GitHub nếu chưa kết nối, chọn repo `CTGDMN_388`
4. Render sẽ tự đọc file `render.yaml` ở gốc repo và đề xuất tạo 1 web service tên `ct388-app`, gói **Free** — bấm **Apply** để tạo
5. Sau khi service được tạo, vào tab **Environment** của service:
   - `DATABASE_URL` → dán chuỗi kết nối Neon đã copy ở bước 1 (dán y nguyên, không cần sửa gì)
   - `CT388_AUTH_SECRET` → Render đã tự sinh sẵn giá trị ngẫu nhiên, để nguyên không cần đổi
   - `CT388_ANTHROPIC_API_KEY` → dán API key Anthropic của bạn
6. Bấm **Save Changes** — Render sẽ tự build và deploy lại

## 3. Kiểm tra
Sau khi deploy xong (vài phút), Render cho 1 link dạng `https://ct388-app.onrender.com`. Mở link đó:
- Lần đầu tiên có thể mất 30-60 giây để "thức dậy" (gói Free tự ngủ sau ~15 phút không ai dùng) — đây là điều bình thường, không phải lỗi
- Mở lên sẽ vào thẳng màn hình đăng ký trường
- Dữ liệu chương trình GDMN (945 bản ghi) tự nạp vào Neon ngay lần khởi động đầu tiên, không cần thao tác tay

## Lưu ý
- Vì dùng gói Free, mỗi lần không ai truy cập trong ~15 phút thì server sẽ ngủ; truy cập lại sẽ tự thức dậy, chỉ chậm ở lượt đầu
- Dữ liệu trên Neon **không** bị tự xoá theo thời gian (khác với Postgres free của Render)
- Nếu sau này có nhiều trường dùng thật và cần server luôn sẵn sàng (không ngủ), có thể nâng cấp gói Starter trả phí của Render bất cứ lúc nào mà không mất dữ liệu

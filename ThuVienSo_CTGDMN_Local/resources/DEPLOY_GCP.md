# Triển khai lên Google Cloud (Cloud Run + Cloud SQL)

Dự án Google Cloud: `quantritruongmamnon`

## 1. Bật các API cần thiết
Trong Cloud Console, vào **APIs & Services → Enabled APIs & services → + Enable APIs** và bật:
- Cloud Run Admin API
- Cloud SQL Admin API
- Cloud Build API

## 2. Tạo database PostgreSQL (Cloud SQL)
1. Vào **SQL** (tìm "SQL" trong ô tìm kiếm trên cùng) → **Create Instance** → chọn **PostgreSQL**
2. Đặt Instance ID (vd: `ct388-db`), mật khẩu cho user `postgres`, chọn region (vd: `asia-southeast1`)
3. Chọn cấu hình rẻ nhất đủ dùng (vd: Sandbox/Development preset, 1 vCPU, giảm dung lượng ổ đĩa xuống mức tối thiểu)
4. Sau khi instance tạo xong, vào tab **Databases** → **Create database** → đặt tên `ct388`
5. Vào tab **Users** → **Add user account** → tạo user riêng (vd: `ct388app`) với mật khẩu, thay vì dùng `postgres`
6. Ghi lại **Connection name** hiển thị ở đầu trang instance, dạng: `quantritruongmamnon:REGION:ct388-db`

## 3. Deploy Cloud Run từ GitHub
1. Vào **Cloud Run** → **Create Service**
2. Chọn **Continuously deploy from a repository (source or function)** → **Set up with Cloud Build**
3. Kết nối tài khoản GitHub → chọn repo `CTGDMN_388`, nhánh `main`
4. Ở phần **Build Type**, chọn **Dockerfile**, **Source location** đặt là: `/ThuVienSo_CTGDMN_Local/resources`
5. Đặt tên service (vd: `ct388-app`), chọn region trùng với Cloud SQL ở bước 2
6. **Authentication**: chọn "Allow unauthenticated invocations" (vì đây là app công khai cho các trường đăng nhập)

## 4. Cấu hình biến môi trường + kết nối Cloud SQL
Trong màn hình tạo/sửa service, mở **Container(s), Volumes, Networking, Security**:

- Tab **Variables & Secrets** → thêm các biến:
  - `DATABASE_URL` = `postgresql+psycopg://ct388app:MẬT_KHẨU@/ct388?host=/cloudsql/quantritruongmamnon:REGION:ct388-db`
  - `CT388_AUTH_SECRET` = một chuỗi ngẫu nhiên dài bất kỳ (vd tự gõ 40 ký tự ngẫu nhiên)
  - `CT388_ANTHROPIC_API_KEY` = API key Anthropic của bạn
- Tab **Connections** → mục **Cloud SQL connections** → **Add connection** → chọn instance `ct388-db` tạo ở bước 2

## 5. Deploy
Bấm **Create** (hoặc **Deploy**). Cloud Build sẽ tự dựng image từ `Dockerfile` và deploy. Xong sẽ có 1 URL dạng `https://ct388-app-xxxxx-as.a.run.app` — mở lên là vào màn hình đăng ký trường.

## Lưu ý
- Mỗi lần push code mới lên nhánh `main`, Cloud Run sẽ tự build & deploy lại (continuous deploy).
- Dữ liệu chương trình GDMN (945 bản ghi) tự nạp vào lần khởi động đầu tiên trên database trống, không cần thao tác tay.
- Nếu đổi `CT388_AUTH_SECRET` sau khi đã có người dùng đăng nhập, tất cả phiên đăng nhập cũ sẽ bị vô hiệu (cần đăng nhập lại) — nên đặt cố định từ đầu, tránh đổi qua lại.

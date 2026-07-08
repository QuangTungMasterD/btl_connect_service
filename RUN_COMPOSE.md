# RUN_COMPOSE.md – Hướng dẫn chạy Notification Service (B7)

Tài liệu này hướng dẫn cách clone repo, cài đặt và chạy toàn bộ hệ thống notification service bao gồm:
- **API FastAPI** (cổng 8000)
- **RabbitMQ** (message broker, cổng 5672 và 15672 cho management UI)
- **PostgreSQL** (cơ sở dữ liệu, cổng host 5433)
- **Consumer** (xử lý sự kiện từ RabbitMQ và gửi thông báo)

---

## 1. Yêu cầu hệ thống

- **Docker** và **Docker Compose** (có sẵn `docker compose` command)
- **Python 3.11+** (nếu muốn chạy thủ công hoặc publish event ngoài container)
- **Node.js & npm** (nếu muốn chạy test Newman, nhưng cũng có thể dùng script có sẵn)
- **curl** (hoặc công cụ tương tự) để kiểm tra API

---

## 2. Clone repository

```bash
git clone https://github.com/QuangTungMasterD/btl_connect_service.git
cd btl_connect_service
```

## 3. Tạo file env từ mẫu
```bash
cp .env.example .env
```

## 4. Build và chạy stack với Docker Compose
```bash
docker compose up -d --build
```

Lệnh này sẽ:
 - Build image cho service notification (sử dụng Dockerfile)
 - Pull images cho rabbitmq và db
 - Tạo các container và chạy ngầm (-d)

Sau khi chạy, bạn có thể kiểm tra trạng thái các container:
```bash
docker compose ps
```
 - Kết quả mong đợi: cả ba service (rabbitmq, db, notification) đều có trạng thái Up và healthy.

## 5. Kiểm tra hoạt động của từng service
### 5.1. API Health
```bash
curl http://localhost:8000/health

```
Kết quả mẫu
```json
{
  "status": "ok",
  "service": "notification-service",
  "version": "1.0.0",
  "rabbitmq": true,
  "processedEvents": 0,
  "lastEventAt": null
}
```
### 5.2. Info endpoint
```bash
curl http://localhost:8000/info
```
## 5.3. RabbitMQ Management UI
- Truy cập trình duyệt: http://localhost:15672
- Tài khoản mặc định: guest / guest

## 5.4. PostgreSQL
Có thể sử dụng pgAmin hoặc dùng docker
- kết nối tới host: localhost, portL 5433
- user: notify_user, password: notify_pass

## 6. Chạy test với Newman
Dự án cung cấp sẵn bộ test Postman và script tự động:
- Windows: chạy tests\run-tests.bat
- Linux/macOS: chạy tests/run-tests.sh
Các script này sẽ:
- Kiểm tra service API đang chạy
- Gửi 3 event mẫu (created, escalated, resolved) vào RabbitMQ
- Cập nhật testEventId vào environment file
- Chạy Newman với collection và báo cáo dạng JSON, HTML trong thư mục reports/
Trước khi chạy, cần cài dependencies Node.js trong thư mục tests:
```bash
cd tests
npm install
```
Sau đó chạy script:
```bash
# Linux/macOS
./run-tests.sh

# Windows
run-tests.bat
```
## 7. Gửi event thủ công để kiểm tra
Ngoài script test, bạn có thể dùng file publish_event.py ở thư mục gốc để gửi một event tới RabbitMQ:
```bash
# window
python publish_event.py

# ubuntu/linux
python3 publish_event.py
```
File này hiện đang gửi event alert.created với target security_team, severity HIGH. Bạn có thể sửa biến ở đầu file để thay đổi loại event, target, v.v.
## 8. Dừng và dọn dẹp
Dừng tất cả container:
```bash
docker compose down
```
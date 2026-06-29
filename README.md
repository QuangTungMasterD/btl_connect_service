# Notification Service – Hệ thống thông báo sự kiện

[![Python Version](https://img.shields.io/badge/python-3.11-blue.svg)](https://www.python.org/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.137.0-009688.svg)](https://fastapi.tiangolo.com/)
[![Docker](https://img.shields.io/badge/docker-compose-blue.svg)](https://www.docker.com/)

Hệ thống nhận các sự kiện từ RabbitMQ, xử lý và gửi thông báo qua nhiều kênh (Email, SMS, Telegram, Display) tùy theo mức độ nghiêm trọng (**severity**) và đối tượng nhận (**target**).

Dự án được xây dựng theo kiến trúc **Clean Architecture**, dễ mở rộng và bảo trì.

---

# 📌 Tính năng

- Nhận sự kiện từ RabbitMQ (`notification.alerts`) với các loại:
  - `alert.created`
  - `alert.escalated`
  - `alert.resolved`
- Phân loại và định tuyến thông báo theo:
  - Severity (`LOW`, `MEDIUM`, `HIGH`, `CRITICAL`)
  - Target (`all`, `admin`, `security_team`, `staff`)
- Gửi thông báo qua nhiều kênh:
  - Email (SMTP)
  - SMS (Mock)
  - Telegram Bot
  - Display (SSE)
- Retry với Exponential Backoff
- Idempotency tránh xử lý trùng
- Lưu log vào PostgreSQL
- REST API quản lý và tra cứu
- Dashboard HTML xem log

---

# 🏗️ Kiến trúc tổng quan

```
                 +-------------+
                 |  Producer   |
                 +-------------+
                        |
                        |
                  RabbitMQ Topic
             notification.alerts
                        |
                        ▼
               +-----------------+
               |    Consumer     |
               +-----------------+
                        |
                        ▼
                +---------------+
                | Alert Handler |
                +---------------+
                        |
        +---------------+----------------+
        |               |                |
        ▼               ▼                ▼
     Email           Telegram          SMS
        \               |               /
         \              |              /
          \             |             /
                  Display (SSE)

                        |
                        ▼
                  PostgreSQL Logs
```

## Thành phần

### Consumer

- Lắng nghe RabbitMQ
- Parse Event
- Gọi Business Logic

### Handler

- Xác định người nhận
- Chọn kênh gửi theo severity
- Lưu log

### Channels

- Email
- SMS
- Telegram
- Display (SSE)

Mỗi channel có retry riêng.

### Cache

Đánh dấu event đã xử lý để tránh xử lý trùng.

---

# 🛠️ Công nghệ sử dụng

- Python 3.11
- FastAPI
- SQLAlchemy Async
- PostgreSQL
- aio-pika
- RabbitMQ
- Pydantic
- Docker
- Docker Compose
- Newman

---

# 📂 Cấu trúc dự án

```text
notification-service/
├── src/
│   ├── api/
│   │   ├── routes/
│   │   ├── app.py
│   │   └── dependencies.py
│   │
│   ├── core/
│   │   ├── interfaces/
│   │   ├── models/
│   │   └── use_cases/
│   │
│   ├── infrastructure/
│   │   ├── cache/
│   │   ├── database/
│   │   ├── display/
│   │   ├── email/
│   │   ├── rabbitmq/
│   │   ├── sms/
│   │   └── telegram/
│   │
│   ├── entrypoints/
│   │
│   └── shared/
│
├── tests/
├── reports/
├── docker-compose.yml
├── Dockerfile
├── requirements.txt
├── .env.example
└── publish_event.py
```

---

# 🚀 Bắt đầu nhanh

## Yêu cầu

- Docker
- Docker Compose
- Python 3.11 (nếu chạy local)

---

## 1. Clone project

```bash
git clone https://github.com/QuangTungMasterD/btl_connect_service.git
cd notification-service
```

---

## 2. Tạo file `.env`

```bash
cp .env.example .env
```

Có thể chỉnh sửa nếu cần.

---

## 3. Chạy bằng Docker Compose

```bash
docker compose up -d --build
```

Sau khi chạy:

| Service | URL |
|----------|-----|
| API | http://localhost:8000 |
| RabbitMQ Management | http://localhost:15672 |
| PostgreSQL | localhost:5433 |

RabbitMQ:

```
Username: guest
Password: guest
```

PostgreSQL:

```
User: notify_user
Password: notify_pass
Database: notification_db
```

---

## 4. Kiểm tra Health

```bash
curl http://localhost:8000/health
```

---

## 5. Gửi Event mẫu

```bash
python publish_event.py
```

Hoặc chạy test:

```bash
cd tests
npm install

./run-tests.sh
```

Windows

```bat
run-tests.bat
```

---

# 🔌 API Endpoints

| Endpoint | Method | Mô tả |
|-----------|--------|-------|
| `/health` | GET | Kiểm tra trạng thái service |
| `/info` | GET | Thông tin service |
| `/metrics/queue` | GET | Queue Metrics |
| `/logs` | GET | Lấy logs |
| `/logs/html` | GET | Dashboard HTML |
| `/notifications/stream` | GET | SSE Stream |

> Endpoint `/metrics/queue` yêu cầu:

```
Authorization: Bearer local-dev-token
```

---

# 🧪 Chạy Test

Cài dependencies

```bash
cd tests
npm install
```

Linux / macOS

```bash
./run-tests.sh
```

Windows

```bat
run-tests.bat
```

Sau khi chạy sẽ sinh báo cáo trong thư mục:

```
reports/
```

---

# 🐳 Docker Compose
| Service | Image | Port |
|----------|-------|------|
| rabbitmq | rabbitmq:3.12-management-alpine | 5672,15672 |
| db | postgres:15-alpine | 5433 |
| notification | notification-service-notification:latest | 8000 |

Notification Service được build từ Dockerfile và chạy:

- FastAPI
- RabbitMQ Consumer

trong cùng một container.

---

# ⚙️ Biến môi trường

| Biến | Giá trị mặc định | Mô tả |
|------|------------------|-------|
| RABBITMQ_HOST | rabbitmq | RabbitMQ Host |
| POSTGRES_HOST | db | PostgreSQL Host |
| DATABASE_URL | postgresql+asyncpg://... | Database URL |
| API_HOST | localhost | API Host |
| AUTH_TOKEN | local-dev-token | Token xác thực |
| MAX_RETRIES | 3 | Retry |
| RETRY_BACKOFF_BASE | 2 | Exponential Backoff |

Các biến Email, Telegram, SMS có thể để trống nếu chỉ chạy local.

---

# 📊 Xem Logs

Notification

```bash
docker compose logs notification
```

RabbitMQ

```bash
docker compose logs rabbitmq
```

PostgreSQL

```bash
docker compose logs db
```

---

# 📝 Ghi chú

- Notification Service bao gồm API và Consumer trong cùng một container.
- Email, SMS và Telegram hoạt động ở chế độ Mock nếu chưa cấu hình.
- Display Channel sử dụng Server-Sent Events (SSE).
- Client có thể kết nối:

```
GET /notifications/stream
```

để nhận thông báo theo thời gian thực.

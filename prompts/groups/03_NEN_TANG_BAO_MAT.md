# Nhóm 3 — Nền tảng, danh tính và bảo mật quản trị

Áp dụng HR-01 đến HR-14, HR-23 đến HR-28, HR-36 đến HR-42.

**Đầu vào chung:** Nhóm 2 đã `PASS`, contract/ADR đã duyệt, `00_NGUYEN_TAC_CUNG.md` và artifact của prompt đứng trước.

## Prompt 03.1 — Khởi tạo monorepo

**Mục tiêu duy nhất:** Tạo cấu trúc repo và build boundary, chưa có business logic.

**Công việc:** Tạo `services/`, `apps/`, `contracts/`, `deploy/`, `docs/`; workspace tooling; service manifests; generated-contract package; ownership file.

**Đầu ra:** Repo skeleton; lệnh bootstrap/lint/test/build.

**Cổng PASS:** Mỗi service build độc lập; không shared business model; không làm mất code hiện có.

**Cấm:** Stub trả PASS giả; nhúng logic Document/RAG.

**Dừng:** Chờ inspect cấu trúc.

---

## Prompt 03.2 — Runtime template cho backend service

**Mục tiêu duy nhất:** Tạo template FastAPI production-ready.

**Công việc:** Typed config; async lifespan; JSON log/redaction; error middleware; request/trace/correlation ID; live/ready; graceful shutdown; HTTP client timeout; migration hook.

**Đầu ra:** Template và một service mẫu; unit/integration tests.

**Cổng PASS:** Health semantics đúng; thiếu config fail-fast; secret canary không vào log.

**Cấm:** Mọi service dùng chung runtime database connection hoặc secret.

**Dừng:** Chờ duyệt template trước nhân rộng.

---

## Prompt 03.3 — Hạ tầng Docker Compose

**Mục tiêu duy nhất:** Dựng dependency local theo profiles.

**Công việc:** PostgreSQL ownership, RabbitMQ/DLQ, Redis, MinIO; networks tách lớp; volume; healthcheck; resource limits; non-root containers.

**Đầu ra:** `core`, `observability`, `training` profiles; `.env.example` placeholder.

**Cổng PASS:** `docker compose config` hợp lệ; data services không expose host mặc định; không có secret thật.

**Cấm:** Mount Docker socket; dùng chung một DB user toàn quyền.

**Dừng:** Báo dependency chưa chạy nếu môi trường thiếu.

---

## Prompt 03.4 — API Gateway/BFF

**Mục tiêu duy nhất:** Triển khai routing và cross-cutting controls.

**Công việc:** Versioned routing; auth propagation; request size; CORS allowlist; rate-limit hook; timeout; idempotency propagation; trace context; sanitized errors.

**Đầu ra:** Gateway code/config/tests.

**Cổng PASS:** Không gọi Provider trực tiếp; unauthorized route bị chặn; correlation ID xuyên tới service mẫu.

**Cấm:** Nhúng business orchestration của Chat/Document.

**Dừng:** Chờ duyệt.

---

## Prompt 03.5 — CI và supply-chain controls

**Mục tiêu duy nhất:** Thiết lập quality gates tự động.

**Công việc:** Lint, type check, unit, contract, integration, image build; secret/SAST/dependency/container/IaC scan; SBOM; migration check; contract drift.

**Đầu ra:** CI pipeline và local-equivalent commands.

**Cổng PASS:** Pipeline fail khi có breaking contract, secret canary hoặc Critical/High chưa xử lý.

**Cấm:** `continue-on-error` cho security/contract gate bắt buộc.

**Dừng:** Chờ kết quả CI thực tế.

---

## Prompt 03.6 — Identity authentication

**Mục tiêu duy nhất:** Xây đăng nhập/phiên cho admin demo, OIDC-ready.

**Công việc:** Argon2id; access token ngắn; refresh rotation/revoke; issuer/audience; rate limit/lockout; secure cookie/CSRF strategy; adapter OIDC.

**Đầu ra:** Identity code, migration, OpenAPI implementation, tests, runbook key rotation.

**Cổng PASS:** Login-refresh-revoke; reused/expired token fail; không trả hash/token secret.

**Cấm:** Hardcode tài khoản/mật khẩu demo; lưu token nhạy cảm tùy tiện ở browser.

**Dừng:** Chờ security review.

---

## Prompt 03.7 — RBAC và service identity

**Mục tiêu duy nhất:** Thực thi deny-by-default authorization.

**Công việc:** Roles `ADMIN`, `CONTENT_MANAGER`, `PROVIDER_ADMIN`, `TRAINING_REVIEWER`, `VIEWER`; permission/action matrix; internal authorization; service clients/mTLS-ready.

**Đầu ra:** Policy, enforcement middleware, privilege tests.

**Cổng PASS:** Role thiếu quyền không publish, activate Provider, approve golden/candidate; service token không dùng thay user token.

**Cấm:** Tin role/action từ client payload.

**Dừng:** Chờ duyệt ma trận quyền.

---

## Prompt 03.8 — Audit append-only

**Mục tiêu duy nhất:** Tạo nhật ký quản trị có thể truy nguyên.

**Công việc:** Audit schema allowlist; actor/action/target/result/time/IDs; before-after redaction; append-only/hash-chain; query có quyền; async command/event intake.

**Đầu ra:** Audit code/migration/tests và integrity check.

**Cổng PASS:** Truy từ admin action tới request; secret canary không xuất hiện; record không sửa tại chỗ.

**Cấm:** Cho service khác ghi trực tiếp audit DB.

**Dừng:** Chờ duyệt.

---

## Prompt 03.9 — Cổng nghiệm thu nền tảng

**Mục tiêu duy nhất:** Xác minh nhóm 3 chạy tích hợp.

**Công việc:** Build/start services; health/readiness; auth/RBAC/audit flow; event idempotency/DLQ mẫu; CI/security scans.

**Đầu ra:** `docs/progress/03-platform-gate.md`.

**Cổng PASS:** Không Critical/High; secret không lộ; runtime và Compose có bằng chứng thực tế.

**Cấm:** Bỏ test do “demo”.

**Dừng:** Chỉ đề xuất Prompt 04.1.

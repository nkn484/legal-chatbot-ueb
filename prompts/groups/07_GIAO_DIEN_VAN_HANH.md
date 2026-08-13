# Nhóm 7 — Giao diện, quan sát, hardening và vận hành

Áp dụng toàn bộ nguyên tắc cứng có liên quan, đặc biệt HR-15–18, HR-23–28, HR-36–42.

**Đầu vào chung:** Các API cần sử dụng đã đạt contract/integration test, nguyên tắc cứng và artifact của prompt đứng trước.

## Prompt 07.1 — Frontend foundation

**Mục tiêu duy nhất:** Tạo hai app frontend và typed API client.

**Công việc:** Web Chat/Admin Portal; generated OpenAPI client; auth/session handling; design tokens; routing; loading/error/empty states; CSP/security headers baseline.

**Đầu ra:** App skeleton/build/tests.

**Cổng PASS:** Browser không gọi Provider; không chứa secret; route admin được bảo vệ; client contract không drift.

**Cấm:** Copy API schema thủ công lệch OpenAPI.

**Dừng:** Chờ inspect UI skeleton.

---

## Prompt 07.2 — Web Chat

**Mục tiêu duy nhất:** Hiển thị quy trình hỏi đáp có nguồn.

**Công việc:** Conversation/input; finding/synthesizing/verifying states; conclusion/analysis/actions/confidence/human-review/freshness; refusal và provider/system errors phân biệt.

**Đầu ra:** Components/pages/E2E tests.

**Cổng PASS:** Không render HTML tùy ý; output không nguồn không hiển thị như kết luận; warning “hỗ trợ tra cứu” rõ.

**Cấm:** Ẩn trạng thái insufficient hoặc biến timeout thành câu trả lời.

**Dừng:** Chờ UX review.

---

## Prompt 07.3 — Citation viewer và feedback UI

**Mục tiêu duy nhất:** Cho người dùng kiểm tra nguồn và phản hồi.

**Công việc:** Citation cards title/number/issuer/provision/page/excerpt; open canonical source; sanitize URL/Markdown; useful/not useful/reason; duplicate prevention.

**Đầu ra:** Components/tests XSS/canonical-link/feedback.

**Cổng PASS:** Link/chunk/page đúng backend; model-created URL không render; malicious excerpt/filename vô hiệu hóa.

**Cấm:** Gửi toàn bộ tài liệu sang frontend nếu không cần.

**Dừng:** Chờ inspect.

---

## Prompt 07.4 — Admin tài liệu và Provider

**Mục tiêu duy nhất:** Xây màn hình quản trị nội dung và cấu hình model.

**Công việc:** Upload/version/progress/chunk/quality/review/publish/reject/reprocess; Provider draft/validate/activate/rollback; RBAC; confirmation/audit status.

**Đầu ra:** Admin pages/E2E role tests.

**Cổng PASS:** API key write-only, không ở response/DOM/log/client persistence; role thiếu quyền không thao tác; destructive action có confirmation.

**Cấm:** Hiển thị storage key, stack trace hoặc secret rút gọn có thể suy đoán quá mức.

**Dừng:** Chờ admin review.

---

## Prompt 07.5 — Admin annotation/evaluation

**Mục tiêu duy nhất:** Xây giao diện Human-in-the-loop.

**Công việc:** Feedback triage; annotation queue/lock/adjudication; golden answer claim-evidence; dataset quality/freeze; eval compare; candidate approve/release status.

**Đầu ra:** Pages/components/E2E reviewer tests.

**Cổng PASS:** Không approve citation sai; approval/release tách biệt; stale/leakage/regression hiển thị rõ; quyền đúng.

**Cấm:** Nút “train/release ngay” bỏ qua gate.

**Dừng:** Chờ reviewer UX review.

---

## Prompt 07.6 — Telemetry và dashboard

**Mục tiêu duy nhất:** Quan sát chuỗi request/job/event xuyên service.

**Công việc:** JSON logs; OpenTelemetry; RED/USE/domain metrics; dashboards chat/provider/queue/document/index/retrieval/citation/training; SLI/SLO/alerts/runbook links.

**Đầu ra:** Collector/config/dashboards/alerts/tests.

**Cổng PASS:** Trace Gateway → services → RabbitMQ → Provider; secret canary không vào log/trace; alert có dữ liệu test thực.

**Cấm:** Cardinality cao do dùng question/chunk content làm label.

**Dừng:** Chờ SRE review.

---

## Prompt 07.7 — Security hardening

**Mục tiêu duy nhất:** Đóng rủi ro Critical/High đã nhận diện.

**Công việc:** SSRF/XSS/IDOR/injection/file upload/auth/session/rate-limit/privilege tests; prompt injection red-team; TLS/network/least privilege/key rotation; SBOM/scans; data at-rest/retention.

**Đầu ra:** Security report, fixes, updated threat model, accepted-risks file.

**Cổng PASS:** Không Critical/High mở nếu chưa có risk acceptance rõ; secret/PII tests 100% không lộ.

**Cấm:** Hạ severity để vượt gate.

**Dừng:** Chờ phê duyệt accepted risks.

---

## Prompt 07.8 — Reliability, backup và chaos

**Mục tiêu duy nhất:** Xác minh phục hồi và graceful degradation.

**Công việc:** Timeout/retry matrix; circuit breaker; load shedding; outbox/inbox reconciliation; DLQ replay; backup/restore; provider/RabbitMQ/worker/DB/object-store failure; RPO/RTO đo thực tế.

**Đầu ra:** Runbooks, chaos tests, restore report.

**Cổng PASS:** Replay không duplicate side effects; restore thành công; request thất bại an toàn; số liệu không suy đoán.

**Cấm:** Chaos trên production hoặc dữ liệu thật chưa ủy quyền.

**Dừng:** Chờ operations review.

---

## Prompt 07.9 — Cổng nghiệm thu UI/Operations

**Mục tiêu duy nhất:** Xác minh giao diện, observability, security và recovery tích hợp.

**Công việc:** E2E theo role; accessibility; XSS/CSRF/CSP; secret canary; trace/dashboard/alerts; backup/restore/DLQ.

**Đầu ra:** `docs/progress/07-ui-ops-gate.md`.

**Cổng PASS:** Tất cả blocker HR có bằng chứng; accessibility baseline và lỗi còn lại được báo thật.

**Cấm:** Dùng screenshot thay cho test hành vi.

**Dừng:** Chỉ đề xuất Prompt 08.1.

# Nhóm 6 — Hệ thống cải thiện và “huấn luyện” câu trả lời

“Huấn luyện” ở đây ưu tiên cải thiện retrieval, prompt và cấu hình bằng dữ liệu đã duyệt. Fine-tuning chỉ là nhánh tùy chọn. Áp dụng HR-01 đến HR-07, HR-16 đến HR-24 và HR-29 đến HR-42.

**Đầu vào chung:** Core RAG/Chat đã `PASS`, contract Feedback/Golden/Dataset/Evaluation đã duyệt, nguyên tắc cứng và artifact của prompt đứng trước.

## Prompt 06.1 — Feedback intake

**Mục tiêu duy nhất:** Thu phản hồi như tín hiệu, không coi là ground truth.

**Công việc:** Useful/not useful, reason taxonomy version, free-text hạn chế, rate limit, duplicate/spam detection, message validity, consent/retention.

**Đầu ra:** Feedback schema/API/migration/tests.

**Cổng PASS:** Unauthorized/duplicate/spam bị xử lý; feedback không tự vào dataset; PII/secret được redaction/quarantine.

**Cấm:** Tự sửa model/prompt từ feedback.

**Dừng:** Chờ duyệt taxonomy sơ bộ.

---

## Prompt 06.2 — Annotation task workflow

**Mục tiêu duy nhất:** Tạo hàng đợi đánh giá có Human-in-the-loop.

**Công việc:** Task từ low confidence, citation error, disagreement, feedback hoặc sampling; states/assignment/lock/revision/adjudication; snapshot versions và lineage.

**Đầu ra:** Annotation schema/APIs/migration/tests.

**Cổng PASS:** Hai reviewer không ghi đè; stale source được gắn cờ; mọi task truy về chat/retrieval/citation/model/prompt version.

**Cấm:** Cho end user tự approve.

**Dừng:** Chờ duyệt workflow.

---

## Prompt 06.3 — Taxonomy lỗi và quality handbook

**Mục tiêu duy nhất:** Chuẩn hóa cách người duyệt gán nhãn.

**Công việc:** Labels retrieval miss, missing source, wrong scope, wrong interpretation, citation error, incorrect refusal, style, provider/system, injection/noise; definitions, positive/negative examples, adjudication rules.

**Đầu ra:** `docs/training/annotation-handbook.md`, versioned taxonomy schema.

**Cổng PASS:** Hai reviewer có thể áp dụng nhất quán; label không chồng lấn mơ hồ; có `UNKNOWN/NEEDS_EXPERT`.

**Cấm:** Ép reviewer đoán khi thiếu căn cứ.

**Dừng:** Người dùng inspect handbook.

---

## Prompt 06.4 — Golden Answer approval

**Mục tiêu duy nhất:** Tạo đáp án chuẩn có citation và phê duyệt.

**Công việc:** Draft/review/approve/revoke; maker-checker; claim-to-chunk mapping; expected refusal/confidence/actions; Citation Service revalidation; immutable versions.

**Đầu ra:** Golden Answer domain/API/migration/tests.

**Cổng PASS:** Không citation/invalid citation không approve; approved record không sửa tại chỗ; revoke phát event/tombstone.

**Cấm:** Copy nguyên answer model thành golden mà không review.

**Dừng:** Chờ inspect examples.

---

## Prompt 06.5 — Dataset Registry

**Mục tiêu duy nhất:** Tạo dataset version từ Golden Answers đã duyệt.

**Công việc:** Filter; deduplicate; manifest; states `DRAFT | VALIDATING | READY | FROZEN | DEPRECATED | REVOKED`; seed cố định; split theo question/document family; content hash/lineage.

**Đầu ra:** Dataset schema/service/migration/tests.

**Cổng PASS:** Frozen immutable/tái lập; chỉ approved/current citation records; train/validation/test IDs không giao nhau theo family.

**Cấm:** Tối ưu trên test set; sửa frozen dataset.

**Dừng:** Chờ duyệt split policy.

---

## Prompt 06.6 — Dataset quality, PII và leakage gate

**Mục tiêu duy nhất:** Chặn dữ liệu nhiễm độc trước freeze/export.

**Công việc:** PII/secret/prompt-injection scan; duplicate/near-duplicate; outlier/spam; source/citation revalidation; license/data policy; contamination/leakage checks; stale propagation.

**Đầu ra:** Quality report và machine-readable gate results.

**Cổng PASS:** Fail-closed cho secret/PII/test leakage/invalid citation; mọi quarantine có reason code và audit.

**Cấm:** Chỉ xóa lỗi khỏi report rồi tiếp tục freeze.

**Dừng:** Chờ privacy/data review.

---

## Prompt 06.7 — Evaluation Runner

**Mục tiêu duy nhất:** Chạy baseline/candidate có thể resume và tái lập.

**Công việc:** Durable async jobs; snapshot dataset/config/code/prompt/model; concurrency/rate/cost budget; cancel/resume; per-sample artifact restricted; deterministic rules trước LLM judge.

**Đầu ra:** Runner/adapters/job state/tests.

**Cổng PASS:** Restart không chạy trùng/tính sai cost; provider fail không giả kết quả; cùng snapshot tái lập được run manifest.

**Cấm:** Gọi provider tốn phí khi chưa có budget/credential approval.

**Dừng:** Chờ duyệt execution plan.

---

## Prompt 06.8 — Metrics và slicing

**Mục tiêu duy nhất:** Tính chỉ số đúng và phát hiện regression cục bộ.

**Công việc:** Citation validity/precision/recall; groundedness theo claim; correctness; Recall@K/MRR/nDCG; correct abstention/false refusal; injection resistance; schema success; latency/token/cost; slice theo lĩnh vực/loại/độ khó.

**Đầu ra:** Metric implementations/tests/report template.

**Cổng PASS:** Denominator rõ; thiếu mẫu ghi NOT_MEASURED; không chỉ dùng trung bình tổng; judge version/bias được báo cáo.

**Cấm:** Dùng một LLM judge làm nguồn quyết định duy nhất.

**Dừng:** Chờ duyệt thresholds.

---

## Prompt 06.9 — Candidate Registry và promotion gate

**Mục tiêu duy nhất:** Quản lý candidate prompt/retrieval/model config và release decision.

**Công việc:** States; baseline comparison; critical slices; confidence/size; cost/latency budget; security suite; human approval; canary/shadow; rollback reference; release recommendation event.

**Đầu ra:** Candidate service/APIs/migration/tests/report.

**Cổng PASS:** Candidate regression safety/citation làm FAIL; approval khác release; không code path auto-activate production.

**Cấm:** Candidate tự gọi Provider/Chat activation endpoint.

**Dừng:** Chờ human approval riêng.

---

## Prompt 06.10 — Fine-tuning export tùy chọn

**Mục tiêu duy nhất:** Xuất artifact huấn luyện, không khởi chạy training.

**Công việc:** Chỉ train split approved; provider-neutral/JSONL adapter; manifest base model/dataset hash/policy/license/hyperparameter proposal; encryption/access/audit.

**Đầu ra:** Export job, validator, manifest, tests.

**Cổng PASS:** Không PII/secret/test samples; hash tái lập; export không thay thế RAG/citation.

**Cấm:** Gọi fine-tuning API hoặc release model nếu chưa có prompt/ủy quyền riêng.

**Dừng:** Chờ quyết định có fine-tune hay không.

---

## Prompt 06.11 — Cổng nghiệm thu Answer Improvement

**Mục tiêu duy nhất:** Chứng minh feedback → golden → dataset → eval → candidate an toàn.

**Công việc:** Test poisoning, invalid citation, reviewer race, revoke document, leakage, failed judge/provider, restart evaluation, bad candidate, rollback.

**Đầu ra:** `docs/progress/06-answer-improvement-gate.md`.

**Cổng PASS:** HR-29–35 có test; lineage end-to-end; không auto-train/auto-release; dataset/eval reproducible.

**Cấm:** Dùng production conversations thật chưa được privacy review.

**Dừng:** Chỉ đề xuất Prompt 07.1.

# Nhóm 8 — Tích hợp, nghiệm thu và bàn giao

Nhóm này không được thay tiêu chí để hợp thức hóa lỗi. Mọi thiếu dữ liệu/môi trường phải ghi `NOT_MEASURED` hoặc `PASS_WITH_CONDITIONS` theo HR-05.

**Đầu vào chung:** Các nhóm cần nghiệm thu đã `PASS`, test data được phép sử dụng, release candidate cố định version/hash và nguyên tắc cứng.

## Prompt 08.1 — Contract integration

**Mục tiêu duy nhất:** Xác minh các service tương thích đúng contract đã duyệt.

**Công việc:** Provider/consumer contract tests; backward compatibility; generated client drift; event schema/version; auth/service identity; failure envelopes.

**Đầu ra:** Integration matrix và test report.

**Cổng PASS:** Không breaking mismatch; không cross-DB workaround; duplicate/out-of-order event được kiểm chứng.

**Cấm:** Sửa contract production chỉ để test pass mà không ADR/version.

**Dừng:** Chờ duyệt.

---

## Prompt 08.2 — E2E vòng đời tài liệu

**Mục tiêu duy nhất:** Test upload → process/OCR → review → publish → index → unpublish.

**Công việc:** PDF text/scan, DOCX, HTML, TXT; corrupt/duplicate/OCR thấp; publish race; reprocess/reindex; source open.

**Đầu ra:** E2E suite/report/artifact hashes.

**Cổng PASS:** Unpublished không retrieval; canonical page/chunk/source đúng; restart/replay không duplicate.

**Cấm:** Bỏ qua OCR thực tế bằng text fixture cho ca scan.

**Dừng:** Chờ duyệt.

---

## Prompt 08.3 — E2E hỏi đáp và Provider failures

**Mục tiêu duy nhất:** Test chuỗi Chat end-to-end và lỗi Provider.

**Công việc:** Một nguồn, nhiều nguồn, mâu thuẫn, thiếu căn cứ, fake citation, injection, unpublish race; Provider 401/403/404/429/5xx/timeout/invalid schema; activate/rollback race.

**Đầu ra:** E2E report và traces đã redaction.

**Cổng PASS:** Conclusion có canonical citation hoặc refusal; chỉ một ACTIVE; secret không lộ; graceful degradation.

**Cấm:** Mock toàn bộ Citation/Retrieval trong E2E này.

**Dừng:** Chờ duyệt.

---

## Prompt 08.4 — E2E Answer Improvement

**Mục tiêu duy nhất:** Test feedback → review → golden → dataset → evaluation → candidate.

**Công việc:** Poisoning/PII/leakage/invalid citation/revoke; reviewer conflict; freeze; restart eval; good/bad candidate; approval/release separation.

**Đầu ra:** E2E report và lineage manifest.

**Cổng PASS:** Không unapproved data; frozen immutable; bad candidate fail; không auto-release.

**Cấm:** Gọi fine-tuning thật nếu chưa có ủy quyền riêng.

**Dừng:** Chờ duyệt.

---

## Prompt 08.5 — Bộ nghiệm thu AI

**Mục tiêu duy nhất:** Xây và khóa test set 50–100 câu có nguồn hợp lệ.

**Công việc:** 60% rõ căn cứ, 20% đa văn bản, 10% thiếu dữ liệu, 10% nhiễu/injection; slice theo loại/cơ quan/điều khoản/tổng hợp/phạm vi/hard negative; human review; test set không tuning.

**Đầu ra:** Frozen acceptance dataset, rubric, provenance, hash.

**Cổng PASS:** Không leakage; citation gold kiểm tra; quyền sử dụng nguồn rõ; coverage đúng tỷ lệ hoặc sai lệch được duyệt.

**Cấm:** Tạo câu/đáp án giả rồi ghi là dữ liệu thực.

**Dừng:** Người dùng inspect từng nhóm câu hỏi.

---

## Prompt 08.6 — Accuracy, load và cost acceptance

**Mục tiêu duy nhất:** Đo chất lượng và năng lực demo trên môi trường ghi rõ.

**Công việc:** Citation validity/accuracy, abstention, technical success, injection/security; 20–30 concurrent sessions; P50/P95/P99; token/cost; cấu hình máy/provider/dataset/version.

**Đầu ra:** Reproducible benchmark report.

**Cổng PASS mục tiêu:** 100% conclusion có citation/refusal; citation accuracy ≥90%; correct abstention ≥90%; technical success ≥95%; không lộ secret/PII 100%; P95 chat ≤30 giây. Không đủ mẫu ghi NOT_MEASURED.

**Cấm:** Loại ca fail sau khi chạy để tăng tỷ lệ.

**Dừng:** Chờ người dùng quyết định PASS thresholds.

---

## Prompt 08.7 — Release package và runbooks

**Mục tiêu duy nhất:** Đóng gói bản demo có thể triển khai và vận hành.

**Công việc:** Compose profiles/env placeholders; migrations/seeds; pinned contracts/images; startup/shutdown; backup/restore; rotate secret; Provider rollback; DLQ replay; reprocess/reindex; incident response; architecture/ADR/limitations/SBOM/test reports/demo script.

**Đầu ra:** Versioned release artifact và checksums.

**Cổng PASS:** Cài mới từ hướng dẫn trên môi trường sạch; không secret; rollback/runbook đã test.

**Cấm:** Triển khai production hoặc dùng credential thật ngoài ủy quyền.

**Dừng:** Chờ bàn giao review.

---

## Prompt 08.8 — Final release gate

**Mục tiêu duy nhất:** Ra kết luận trung thực `PASS | PASS_WITH_CONDITIONS | FAIL`.

**Công việc:** Kiểm blockers: citation bypass, unpublished retrieval, secret leak, Critical/High, migration/E2E fail, auto-release candidate; ánh xạ REQ → service/API/event/test/result.

**Đầu ra:** `docs/acceptance-report.md`, traceability matrix hoàn chỉnh, conditions for production.

**Cổng PASS:** Mọi MUST có evidence; sai lệch/risks/NOT_MEASURED công khai; người có quyền ký duyệt.

**Cấm:** Tự miễn trừ nguyên tắc cứng; gọi demo là production-ready khi điều kiện production chưa đạt.

**Dừng:** Kết thúc; không tự triển khai production.

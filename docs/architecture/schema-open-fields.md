# Trường nghiệp vụ còn mở cho schema 02.3

Các schema 02.3 giữ biểu diễn tối thiểu, an toàn và additive; chúng không là ORM/DB model. Không trường nào dưới đây được làm suy yếu HR-15..18, HR-23, HR-26 hoặc HR-29..33. API/event chính xác thuộc 02.4/02.5; quyền riêng tư thuộc 02.6; `DEC-005` vẫn **OPEN**.

| Trường/quyết định | Schema/owner bị ảnh hưởng | Biểu diễn an toàn hiện tại | Cần xác nhận | Hạn/prompt tương lai sở hữu |
|---|---|---|---|---|
| Từ vựng metadata pháp luật: jurisdiction, document class, issuer, number, hiệu lực, người phê duyệt | document / document-service; citation / citation-service | Mã không ràng buộc và `EffectConfirmation` có provenance | Danh mục, thẩm quyền xác nhận, quy tắc số hiệu | Trước contract finalization; 02.4 |
| Ngữ nghĩa phạm vi `active` | document / document-service | Boolean chỉ có bất biến `active=true => PUBLISHED` | Phạm vi theo thời điểm, jurisdiction và revoke | Trước implementation; 02.4 |
| Vai trò/evidence review, publish, unpublish Version | document / document-service | State và provenance/actor ref opaque | Role, quorum, evidence review và quyền unpublish | Trước implementation; 02.4 |
| Tối thiểu locator | processing / processing-service; citation / citation-service | Cần ít nhất một page/article/clause/point/offset | Chính xác dimension tối thiểu theo loại tài liệu | 02.4 |
| Sufficiency, conflict taxonomy, threshold, context expiry | retrieval / retrieval-service | Reason code mở, context ID opaque | Taxonomy, threshold, request binding/expiry | 02.4 |
| Citation render/language và disclosure excerpt theo client | citation / citation-service | `render_hash`, excerpt, locator canonical | Format/ngôn ngữ render và policy disclosure | 02.4, privacy 02.6 |
| Retention/deletion/tombstone và actor identity | common, document, processing, feedback, evaluation / owners tương ứng | Hash/ref/actor opaque, không có storage path | Retention, tombstone propagation và identity vocabulary | 02.6 và 02.5 |
| Feedback taxonomy/comment và Golden quorum/revocation authority | feedback / feedback-service | Category code; comment hash/ref, không raw comment | Taxonomy, handling, quorum, authority | LATER contract; 02.4 |
| Dataset split/family leakage và revoke trên evaluation hoàn tất | evaluation / evaluation-service | TRAIN/VALIDATION/TEST; frozen hash/reference | Family policy, propagation và historical result policy | LATER contract; 02.4 |
| Candidate eligibility threshold và human release authority riêng | evaluation / evaluation-service | `ELIGIBLE` không activation/release | Threshold, approver và release gate riêng | LATER governance; 02.4 |
| Provider kind/capability và endpoint-profile governance | provider-config-view / provider-service | Code/open capability, opaque endpoint profile, không secret | Vocabulary, allowlist/SSRF governance, approval | LATER governance; 02.4 |
| Hash algorithm/profile và ID format interoperability | common / cross-contract | Opaque patterned values | Algorithm/profile registry và stricter external format | Trước external interoperability; 02.4 |

Các xác nhận này chỉ bổ sung ràng buộc trong scope owner; không kích hoạt Provider, Feedback hoặc Evaluation, không tạo executable Citation claim khi `DEC-005` còn OPEN.

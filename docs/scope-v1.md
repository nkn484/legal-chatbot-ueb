# Phạm vi Core Demo v1 — Giáo dục đại học Việt Nam

## Tuyên bố khóa phạm vi

Core Demo là bản lập kế hoạch cho chatbot tra cứu pháp luật thuộc miền **Giáo dục đại học** tại Việt Nam. Chế độ trả lời là **trích xuất/retrieval-first**: hệ thống chỉ trả nội dung được căn cứ từ kho tài liệu đã công bố, kèm citation canonical do backend dựng. Core Demo không dùng Provider trả lời trực tiếp, không có API key và không phát sinh chi phí dịch vụ trả lời sinh nội dung.

Core Demo bị timebox nghiêm ngặt trong **10 ngày dương lịch liên tiếp**, bắt đầu từ ngày khởi động được phê duyệt. Đây là ràng buộc cứng cho scope, ưu tiên và bằng chứng nghiệm thu: việc không hoàn thành/có evidence trong timebox phải bị loại, để `LATER` hoặc ghi `NOT_MEASURED`. Người dùng đã xác nhận 10 ngày dương lịch. Timebox không là cam kết giao hàng, production readiness/SLA hay hoàn thành các prompt tương lai. Mọi boundary, schema, API, event và stack chính thức vẫn thuộc Prompt 02.1 và các prompt kiến trúc sau khi phạm vi này được duyệt.

## Persona và user story

| ID | Persona | User story |
|---|---|---|
| US-RES-01 | Người nghiên cứu ẩn danh/demo | Tôi muốn hỏi bằng tiếng Việt trong miền đã khóa để nhận nội dung trích xuất có citation canonical hoặc refusal có cấu trúc, nhằm tự kiểm tra nguồn. |
| US-CUR-01 | Curator/Admin đã xác thực | Tôi muốn quản lý vòng đời corpus demo: tải lên, kiểm hash, trích xuất, chunk, review, publish/unpublish và index, để chỉ nguồn đã kiểm duyệt được retrieval. |
| US-ADM-01 | Curator/Admin đã xác thực | Tôi muốn xem audit kỹ thuật tối thiểu của vòng đời corpus, không quản trị Provider, để vận hành demo cục bộ. |

## Danh mục yêu cầu

Mỗi yêu cầu có đúng một mức ưu tiên: `MUST`, `SHOULD` hoặc `LATER`.

| ID | Ưu tiên | Yêu cầu |
|---|---|---|
| REQ-SCP-001 | MUST | Miền duy nhất của Core Demo là pháp luật Việt Nam về Giáo dục đại học; câu hỏi được nhập bằng tiếng Việt. |
| REQ-USR-001 | MUST | Persona hỏi đáp là người nghiên cứu ẩn danh/demo; không có self-registration, SSO hoặc multitenancy. |
| REQ-USR-002 | MUST | Demo có một vai trò Curator/Admin đã xác thực cho quản trị corpus; một demo account được provision là chấp nhận được, nhưng không là quyết định kiến trúc/schema một người dùng vĩnh viễn. Phạm vi quản trị không gồm Provider. |
| REQ-DOC-001 | MUST | Corpus chỉ gồm 3–5 văn bản pháp luật Việt Nam chính thức, tổng không quá 200 trang, ở dạng PDF có text layer; loại trừ PDF scan/OCR, DOCX, HTML và TXT. Danh sách chính xác cùng metadata hiệu lực pháp lý chỉ được nạp sau khi người dùng/curator được nêu tên phê duyệt. |
| REQ-DOC-002 | MUST | Curator/Admin thực hiện upload, kiểm/ghi nhận hash, extract, chunk, review thủ công, publish/unpublish và index; không tự publish. |
| REQ-RET-001 | MUST | Chế độ trả lời là retrieval-first/extractive; không gọi answer Provider, không cần API key và không dùng mô hình sinh câu trả lời trực tiếp. |
| REQ-RET-002 | MUST | Retrieval chỉ được lấy document/version `PUBLISHED` và active. |
| REQ-RET-003 | MUST | Mọi kết luận thực chất phải có citation canonical do backend lấy từ nguồn thật, bao gồm tên chính thức/số ký hiệu, Điều/Khoản/Điểm hoặc trang, excerpt và canonical URL. |
| REQ-RET-004 | MUST | Với evidence thiếu, ngoài corpus, mơ hồ hoặc mâu thuẫn, hệ thống trả refusal có cấu trúc và không gọi answer-model. |
| REQ-RET-005 | MUST | Hệ thống không suy luận hiệu lực pháp lý; chỉ dẫn độc hại từ người dùng hoặc nhúng trong nội dung nguồn đều là input không tin cậy, không được thực thi hay ghi đè scope, publish filter, citation hoặc refusal. Ca prompt-injection chỉ trả output có citation canonical khi evidence đủ, nếu không phải trả refusal có cấu trúc. |
| REQ-UX-001 | SHOULD | Giao diện demo hiển thị thông báo không phải tư vấn pháp lý. |
| REQ-OPS-001 | MUST | Admin chỉ xử lý lifecycle corpus trong môi trường local/demo cô lập; Compose là mục tiêu triển khai, còn stack và ADR chính xác để quyết định sau. |
| REQ-NFR-001 | MUST | Không log đầy đủ chat/prompt/context/nội dung tài liệu; log kỹ thuật đã redaction giữ tối đa 14 ngày và audit admin tối đa 30 ngày là mặc định demo, chờ privacy/ADR quyết định cách triển khai chính xác. |
| REQ-NFR-002 | SHOULD | Đo 5 phiên chat đồng thời trên phần cứng và workload được ghi nhận; mục tiêu sơ bộ P95 không quá 30 giây, báo cáo P50/P95/P99 và tỷ lệ thành công. Nếu chưa đo phải ghi `NOT_MEASURED`. |
| REQ-DATA-001 | MUST | Bộ ca kiểm thử demo frozen gồm 3–5 tài liệu và đúng 15 câu hỏi có provenance: 8 trực tiếp, 3 đa nguồn (trong đó 1 ca có evidence mâu thuẫn đáng kể và phải refusal), 2 ngoài corpus, 1 mơ hồ, 1 prompt-injection. Mỗi ca có kỳ vọng là câu trả lời có citation canonical hoặc refusal; đây không phải Golden Answer/training dataset và không đi vào Answer Improvement. |
| REQ-PLN-001 | MUST | Core Demo bị timebox nghiêm ngặt trong 10 ngày dương lịch liên tiếp từ ngày khởi động được phê duyệt. Đây là ràng buộc cứng cho scope, ưu tiên và evidence nghiệm thu: việc không hoàn thành/có evidence trong timebox phải bị loại, để `LATER` hoặc ghi `NOT_MEASURED`; không là cam kết giao hàng, production readiness/SLA hay hoàn thành prompt tương lai. |
| REQ-AI-001 | LATER | Feedback, Golden Answer, dataset, evaluation, candidate và fine-tuning thuộc Answer Improvement sau Core Demo; không được trở thành core hoặc làm suy yếu HR-29, HR-30, HR-33, HR-34. |
| REQ-OPS-002 | LATER | Production HA, Kubernetes, SSO, live Provider, OCR, định dạng bổ sung, bulk ingestion, multi-domain, mobile, production deployment và backup/DR nằm ngoài Core Demo. |

## Trong phạm vi

- Tra cứu tiếng Việt trong corpus Giáo dục đại học Việt Nam đã được curator phê duyệt và publish.
- Chuỗi lifecycle tài liệu text-native PDF ở mức demo, citation canonical, refusal fail-closed và notice không phải tư vấn pháp lý.
- Một researcher ẩn danh/demo, một Curator/Admin đã xác thực, môi trường local/demo cô lập và phép đo tải demo đã ghi nhận cấu hình.

## Ngoài phạm vi

- Provider trực tiếp/generative, API key, chi phí Provider và quản trị Provider.
- OCR, PDF scan, DOCX, HTML, TXT, bulk ingestion, hoặc corpus ngoài miền đã khóa.
- Self-registration, SSO, multitenancy, mobile, HA, Kubernetes, production deployment, backup/DR.
- Feedback, Golden Answer, dataset huấn luyện, evaluation, candidate và fine-tuning; chúng được để `LATER` cho Nhóm 06.

## Dữ liệu demo và nghiệm thu dự kiến

Corpus chỉ được chọn trong 3–5 PDF text-native chính thức, không quá 200 trang cộng dồn. Từng tài liệu phải có hash, provenance và metadata hiệu lực do người có thẩm quyền xác nhận; hệ thống không tự kết luận metadata này. Bộ ca kiểm thử demo frozen có đúng 15 câu hỏi giữ provenance và kỳ vọng theo các nhóm nêu trong danh mục yêu cầu: 8 trực tiếp, 3 đa nguồn (một ca có evidence mâu thuẫn đáng kể và phải refusal), 2 ngoài corpus, 1 mơ hồ và 1 prompt-injection. Ca prompt-injection kiểm tra cả chỉ dẫn độc hại của người dùng và chỉ dẫn nhúng trong nguồn: không được ghi đè scope, publish filter, citation hoặc refusal; chỉ có output canonical-cited khi evidence đủ, nếu không phải refusal có cấu trúc. Frozen demo acceptance fixture này không phải Golden Answer/training dataset, không đi vào Answer Improvement và chỉ dùng để chứng minh từng ca đã định, không dùng tỷ lệ phần trăm để suy diễn độ chính xác tổng quát.

## Yêu cầu phi chức năng và an toàn

- 5 phiên chat đồng thời là workload demo; báo cáo P50/P95/P99 và tỷ lệ thành công theo máy/workload đã ghi nhận. Chưa có phép đo thì là `NOT_MEASURED`.
- Không log full prompt, context, chat hay toàn văn tài liệu. Redaction và retention là mặc định demo cần được chốt bởi privacy/ADR sau này.
- Áp dụng fail-closed cho publish gate, citation và evidence. Các bất biến có năng lực liên quan là HR-15, HR-16, HR-17, HR-18, HR-19, HR-20, HR-21, HR-23, HR-29, HR-30 và HR-33; không có Provider hoặc Answer Improvement trong core không làm giảm các bất biến đó.

## Giả định và quyết định mở

| Loại | Nội dung | Điều kiện giải quyết |
|---|---|---|
| Giả định | Người dùng đã xác nhận miền, chế độ retrieval-first không Provider, và timebox nghiêm ngặt 10 ngày dương lịch liên tiếp từ ngày khởi động được phê duyệt như đã định nghĩa ở trên. | Đủ để khóa scope hiện tại. |
| Quyết định mở không đổi boundary/schema | Danh sách corpus chính xác, người dùng/curator được nêu tên phê duyệt và metadata hiệu lực. | Phải chốt trước ingestion; không phải điều kiện trước scope lock. |
| Quyết định mở không đổi boundary/schema | Máy benchmark và workload ghi nhận. | Phải chốt trước đo tải; không phải điều kiện trước scope lock. |
| Quyết định mở không đổi boundary/schema | Ngày demo và năng lực nhóm thực hiện. | Phải chốt trước thực thi lịch; không phải điều kiện trước scope lock. |
| Điều kiện quy trình/dependency | Chuỗi manifest hiện tại khiến 05.8 Citation phụ thuộc tuần tự 05.7 → 05.6 → 05.5 Provider; 05.6 yêu cầu real minimal Provider request, mâu thuẫn với Core không Provider/credential/cost. REQ-RET-003 citation là MUST không được defer. | Trước khi planning implementation downstream có thể khẳng định đường đi khả thi tới REQ-RET-003, phải có quyết định governance/manifest tương lai được phê duyệt riêng; Prompt 01.2 không sửa manifest hay prompt tương lai. |

Không có quyết định mở nào ở trên được phép tự thay đổi boundary hoặc schema. Điều kiện dependency không làm suy yếu hoặc defer citation Core MUST. Prompt 02.1 sở hữu việc phê duyệt cuối cùng bounded context và ownership.

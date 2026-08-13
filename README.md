# Repo Pack — Chatbot Pháp luật với OpenCode + Oh-my-opencode-slim

Gói này phải được đặt tại **gốc của đúng một repository Chatbot Pháp luật**. Không cài ở thư mục cấu hình OpenCode toàn cục và không dùng chung cho repository khác.

## Thành phần

- `AGENTS.md`: luật repository luôn áp dụng.
- `opencode.jsonc`: instruction, permission và lệnh nguy hiểm bị khóa theo repo.
- `.opencode/commands/`: 72 prompt độc lập, gọi bằng slash command.
- `.opencode/oh-my-opencode-slim/`: append prompt theo từng agent, không thay prompt gốc.
- `.opencode/oh-my-opencode-slim.jsonc`: giới hạn orchestration và permission theo agent.
- `prompts/manifest.json`: dependency, write roots và agent phù hợp.
- `.agent-run/prompt-state.json`: trạng thái thực thi có truy vết.
- `scripts/prompt_gate.py`: kiểm tra, bắt đầu, submit, duyệt và hiển thị trạng thái.
- `scripts/verify_pack.py`: kiểm tra tính toàn vẹn của gói.

## Cài vào repository

1. Giải nén và chép toàn bộ nội dung thư mục này vào gốc repository.
2. Kiểm tra không ghi đè `AGENTS.md` hoặc `opencode.jsonc` hiện hữu; nếu đã có, merge thủ công.
3. Chạy `python scripts/verify_pack.py`.
4. Chạy `oh-my-opencode-slim doctor` tại gốc repository.
5. Khởi động OpenCode **không dùng `--auto`**.
6. Gõ `/prompt-status`, sau đó bắt đầu bằng `/prompt-01-1`.

Gói không hardcode model/provider. Nó kế thừa preset OMO-slim đang hoạt động, tránh làm hỏng cấu hình ShineShop hoặc Provider khác của người dùng.

## Quy trình duyệt

Agent chỉ được submit kết quả và dừng ở `AWAITING_APPROVAL`. Sau khi kiểm tra báo cáo, người dùng chạy ngoài OpenCode:

```bash
python scripts/prompt_gate.py approve 01.1 --by "USER" --note "Đã kiểm tra"
```

Nếu không đạt:

```bash
python scripts/prompt_gate.py reject 01.1 --by "USER" --note "Lý do"
```

`PASS_WITH_CONDITIONS` chỉ được chuyển thành `PASS` khi người dùng ghi điều kiện trong `--note`. Đây là cổng quy trình và audit, không phải cơ chế xác thực danh tính mật mã.

## Chạy prompt

- `/prompt-01-1`: kiểm kê repository.
- `/prompt-02-1`: chỉ được chạy sau khi toàn bộ dependency đã PASS/được duyệt.
- `/prompt-status`: xem trạng thái.

Một prompt có thể dùng nhiều agent read-only song song nhưng mặc định chỉ một writer. Orchestrator không được tự gọi prompt kế tiếp.

## Core Demo và Answer Improvement

Nhóm 06 là hệ thống cải thiện câu trả lời. Nếu phạm vi Core Demo tại Prompt 01.2 quyết định hoãn nhóm này, người dùng có thể defer ngoài OpenCode:

```bash
python scripts/prompt_gate.py defer-group 06 --by "USER" --note "LATER theo scope đã duyệt"
```

Chỉ defer khi tài liệu phạm vi đã ghi rõ `LATER`; Final Gate phải liệt kê toàn bộ prompt đã defer.

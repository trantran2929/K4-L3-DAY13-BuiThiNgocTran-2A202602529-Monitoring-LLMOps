# Báo cáo cá nhân — K4-L3A Day 13 Monitoring & LLMOps

> Mỗi học viên hoàn thiện một file duy nhất này. Khi dẫn evidence, dùng đường dẫn tương đối, ví dụ `evidence/07-trace-waterfall.png`.

## 1. Thông tin học viên

- **Họ và tên:** Bùi Thị Ngọc Trân
- **MSSV:** 2A202602529
- **Lớp:** K4-L3A
- **Repository URL:**https://github.com/trantran2929/K4-L3-DAY13-BuiThiNgocTran-2A202602529-Monitoring-LLMOps
- **Commit SHA cuối:** 46567f628da9d21c8a814095dabeecd56868f54a
- **Challenge ID:** day13-k4-l3a-monitoring-llmops-v1
- **Tên project Langfuse cá nhân:** `day13-k4-l3a-2a202602529`

## 2. Evidence index

Điền đúng đường dẫn tới evidence thực tế. Có thể đổi tên hoặc dùng nhiều ảnh nếu cần.

| Evidence | Đường dẫn |
|---|---|
| Pytest cuối | [Pytest](evidence/01-pytest.png) |
| Log validator | [Log validator](evidence/02-log-validator.png) |
| Dashboard validator | [Dashboard validator](evidence/03-dashboard-validator.png) |
| Structured log | [Structured log](evidence/04-structured-log.png) |
| PII redaction | [PII redaction](evidence/05-pii-redaction.png) |
| Trace list | [Trace list](evidence/06-trace-list.png) |
| Trace waterfall | [Trace waterfall](evidence/07-trace-waterfall.png) |
| Trace metadata | [Trace metadata](evidence/08-trace-metadata.png) |
| Prompt versions | [Prompt versions](evidence/09-prompt-versions.png) |
| Prompt rollback | [Prompt rollback](evidence/10-prompt-rollback.png) |
| Production v2 | [Production v2](evidence/10a-production-v2-trace.png) |
| Dashboard runtime | [Dashboard runtime](evidence/11-dashboard-overview.png) |
| Incident metric | [Incident metric](evidence/12-incident-metric.png) |
| Incident log | [Incident log](evidence/13-incident-log.png) |
| Incident trace | [Incident trace](evidence/14-incident-trace.png) |
| Recovery | [Recovery](evidence/15-recovery.png) |

## 3. Kết quả kỹ thuật

| Nội dung | Baseline | Kết quả cuối | Nhận xét |
|---|---|---|---|
| `validate_logs.py` | 30/100; kiểm tra 62 bản ghi | 100/100 ước tính; 178 bản ghi; 0 thiếu required fields; 0 thiếu context; 74 correlation ID duy nhất | Đã khắc phục các lỗi thiếu trường và context ở baseline. Lần kiểm tra cuối đạt 100/100 ước tính; không phát hiện PII theo validator. Evidence: [Log validator](evidence/02-log-validator.png). |
| `validate_dashboard.py` | PASS — 6/6 panel | PASS — 6/6 panel | Contract YAML hợp lệ với đủ sáu panel. Ảnh runtime bổ sung bằng chứng dashboard có dữ liệu, time range, đơn vị và threshold. Evidence: [Validator](evidence/03-dashboard-validator.png), [Dashboard](evidence/11-dashboard-overview.png). |
| `pytest` | 22 passed trong 4.48 giây | 35 passed trong 3.67 giây | Toàn bộ 35 tests hiện có đều pass. Đã sửa timeout lấy prompt từ 10 giây về 2 giây để khớp contract được kiểm tra. Evidence: [Pytest](evidence/01-pytest.png). |
| Số traces hợp lệ | Đã ghi nhận 10 root observations trên Langfuse | Danh sách có 34 root observations sau khi loại local-v1; trace được kiểm tra có root, retrieval và generation | Danh sách có 34 root observations sau khi loại local-v1. Trace được kiểm tra có retrieval và generation là con của root; chưa kiểm tra chi tiết từng trace trong danh sách. Evidence: [Danh sách](evidence/06-trace-list.png), [Waterfall](evidence/07-trace-waterfall.png), [Metadata](evidence/08-trace-metadata.png). |
| Số PII leak | 0 theo log validator | 0 potential PII leaks theo validator trên 178 bản ghi | Validator không phát hiện PII trên bộ log đã kiểm tra. Code tắt capture input/output tự động cho observations; kết quả kiểm tra không bảo đảm bao phủ mọi dạng PII. |
| Latency P95 / TTFT P95 | Chưa đo | 705.2 ms / 50 ms, theo cửa sổ dashboard baseline gồm 10 request | P95 705.2 ms thấp hơn ngưỡng 3000 ms; TTFT P95 là 50 ms. Số đo thuộc cửa sổ dashboard baseline gồm 10 request, chưa đại diện cho vận hành dài hạn. |
| Retrieval success rate | Chưa xác minh | 100% trên 10 mẫu trong cửa sổ dashboard baseline | 10/10 kết quả retrieval thành công trong cửa sổ dashboard, cao hơn ngưỡng tối thiểu 90%. Chỉ số này phản ánh tool thực thi thành công, không khẳng định tài liệu truy xuất luôn phù hợp. |

## 4. Logging và PII

- **Cách tạo/nhận và truyền correlation ID:**  Middleware xóa context của request trước, lấy header x-request-id nếu có; nếu không thì tạo req-<8 ký tự hex>. ID được lưu trong request.state, bind vào structlog contextvars, truyền vào agent/trace và trả qua response header x-request-id cùng response body.
- **Các metadata được ghi vào structured log:** ts, level, event, service, correlation_id, user_id_hash, session_id, feature, model, env. Event response_sent bổ sung latency_ms, ttft_ms, tokens_in, tokens_out, cost_usd, quality_score, tool_name và tool_success.
- **Cách bảo đảm PII được scrub trước khi ghi:** user_id được hash bằng SHA-256 và lấy 12 ký tự hex đầu. summarize_text che PII trước khi rút gọn nội dung. Processor scrub_event xử lý đệ quy các giá trị chuỗi trong dict/list trước khi ghi JSONL và render ra terminal. Các pattern hiện có gồm email, điện thoại Việt Nam, CCCD và thẻ.Observations tắt tự động capture input/output.
- **Cách kiểm chứng kết quả:** Chạy workload bằng dữ liệu giả, đối chiếu input với message_preview đã redact trong log; kiểm tra correlation ID giữa request, response và trace; chạy pytest và validate_logs.py. Evidence: [Structured log](evidence/04-structured-log.png), [PII redaction](evidence/05-pii-redaction.png). Regex và hash rút gọn có giới hạn; kết quả test không chứng minh đã bao phủ mọi dạng PII.

## 5. Tracing và prompt versioning

- **Cách xác nhận traces do chính tôi tạo trong project cá nhân:** Chạy scripts/load_test.py từ repo cá nhân, đối chiếu correlation_id trong output với metadata của trace trên Langfuse. Request đã kiểm tra: req-b606e44a.
- **Cấu trúc root/retrieval/generation observations:** Root lab-agent-run có hai observation con là retrieval và fake-llm-generation. Waterfall hiển thị root và generation khoảng 159 ms; retrieval hiển thị 0 ms ở độ phân giải giao diện. Generation chiếm phần lớn latency của trace này. Evidence: [Waterfall](evidence/07-trace-waterfall.png).
- **Cách nối trace với log:** Dùng correlation_id=req-b606e44a. Trace ID: 5bafbb01d9fc11f34e7e66ef4cf24ef5. Evidence: [Metadata](evidence/08-trace-metadata.png).
- **Prompt name:** day13-chat.
- **Version/label baseline:** v1, label baseline.
- **Version/label candidate:** v2, label candidate.
- **Trace ID của mỗi version:**
    - baseline / v1: 8fac962805007152cd492f0f6edc8f6b
    - candidate / v2: ed5f2d30777dd064ee033c9d86ac412d
    - production / v2 sau promote: 93a95ab1a4f1acf890921e95b9fd9f3c
    - production / v1 sau rollback: 5bafbb01d9fc11f34e7e66ef4cf24ef5
- **Cách promote và rollback `production`:** Chuyển label production từ v1 sang v2 và xác minh trace dùng production/v2. Sau đó chuyển production về v1 và xác minh trace mới dùng production/v1. Cả bốn trace trên đều có prompt_source=langfuse và prompt_name=day13-chat.
- Evidence trước/sau:
    [Production v2](evidence/10a-production-v2-trace.png),
    [Production về v1](evidence/10-prompt-rollback.png).

## 6. Dashboard, SLO và alerts

- **Dashboard và sáu panel:** Streamlit, đọc data/logs.jsonl, cửa sổ 60 phút, refresh 30 giây. Gồm latency/TTFT, traffic, errors/retrieval success, cost, tokens và quality. Evidence: [Dashboard runtime](evidence/11-dashboard-overview.png).
- **SLO và lý do chọn:** 99.5% request thành công trong tối đa 3000 ms trên cửa sổ 28 ngày. Giữ ngưỡng lab, cao hơn P95 baseline để có khoảng dự phòng. Mẫu 10 request chưa đại diện cho vận hành dài hạn.
- **Cách tính error budget:** Budget = 0.005 × tổng request. Bad request là request không thành công hoặc vượt 3000 ms. Trong mẫu lab đã kiểm tra: 10 request đều tốt, 0 bad requests, tiêu thụ 0% budget. Chưa đánh giá đủ cửa sổ 28 ngày.
- **Ba alert và runbook tương ứng:** high_response_latency, high_request_error_rate và low_response_quality. Điều kiện nằm trong config/alert_rules.yaml; hướng dẫn xử lý nằm trong docs/alerts.md. Chưa triển khai gửi thông báo Slack thực tế.

## 7. Điều tra challenge

- **Challenge ID:** day13-k4-l3a-monitoring-llmops-v1.
- **Khoảng thời gian điều tra:** Dashboard hiển thị cửa sổ 17:28:44–18:28:44 UTC ngày 29/09/2026. Request được chọn xảy ra từ 18:27:42.478 đến 18:27:45.136 UTC. Cửa sổ dashboard gồm cả dữ liệu trước incident.
- **Triệu chứng từ metrics:** Latency P95 = 2653.1 ms, P99 = 2653.8 ms; TTFT P95 = 50 ms. Error rate = 0%, retrieval success = 100%. Latency tăng so với baseline CP2, nhưng chưa vượt ngưỡng 3000 ms trên dashboard. Evidence: [Incident metric](evidence/12-incident-metric.png).
- **Log line và correlation ID liên quan:** correlation_id=req-6519b331, event=response_sent, ts=2026-09-29T18:27:45.136415Z, feature=monitoring,latency_ms=2653, ttft_ms=50, tool_name=retrieval, tool_success=true. Evidence: [Incident log](evidence/13-incident-log.png).
- **Trace ID và span gây ảnh hưởng:** 50bfc3f891ba9970569873ea0da0a620. Root khoảng 2.65 giây, retrieval 2.50 giây, fake-llm-generation 152 ms. Retrieval chiếm khoảng 94% thời gian root. Evidence: [Incident trace](evidence/14-incident-trace.png).
- **Root cause:** Incident rag_slow thêm thời gian chờ 2.5 giây vào bước retrieval trong code lab, khớp với span retrieval. Tool vẫn thành công nên không làm tăng error rate. Chưa kết luận nguyên nhân toàn bộ phần chênh lệch giữa thời gian client và thời gian trong trace.
- **Fix action:** Chạy `python scripts/inject_incident.py --disable`, xác nhận mọi incident flag đều false. Chạy lại cùng workload challenge với concurrency 5, không restart API giữa hai lượt. Cả 5 request trả về 200; thời gian client giảm từ 10647–13310.1 ms xuống 495.2–820.5 ms. Log sau khắc phục của request `req-387ba247` ghi `response_sent` lúc `2026-09-29T18:33:36.160898Z`, `latency_ms=152`, `ttft_ms=50` và `tool_success=true`. Latency xử lý trong ứng dụng giảm từ 2653 ms ở request incident xuống 152 ms ở request phục hồi, trên cùng workload challenge. Evidence: [Recovery](evidence/15-recovery.png).
- **Preventive measure:** Theo dõi latency riêng của retrieval và latency end-to-end; đặt timeout phù hợp cho dependency; kiểm thử hiệu năng với cùng workload/concurrency trước khi triển khai; dùng correlation ID để đối chiếu metrics, logs và traces khi latency tăng dù error rate vẫn bằng 0. Đây là biện pháp đề xuất, chưa phải thay đổi đã triển khai.

## 8. Giải thích và tự đánh giá

- **Một quyết định kỹ thuật quan trọng và lý do:** Scrub PII trước khi ghi log và tắt capture input/output tự động trên observations. Cách này vẫn giữ metadata, timing, tokens và cost phục vụ điều tra, đồng thời giảm việc lưu nội dung nhạy cảm.
- **Một lỗi/blocker đã gặp:** Test prompt management thất bại vì fetch_timeout_seconds trong code là 10, còn contract test yêu cầu 2.
- **Cách tìm nguyên nhân và xử lý:** Đọc phần khác biệt trong assertion, đối chiếu app/prompt_management.py với test, sửa timeout về 2 giây. Chạy lại được 35 tests pass và xác minh trace thực tế có prompt_source=langfuse.
- **Cách hiểu luồng Metrics → Logs → Traces:** Metrics giúp nhận biết triệu chứng và thời điểm. Logs giúp chọn request bằng correlation ID. Trace cùng correlation ID cho biết bước nào chiếm thời gian. Trong challenge, log ghi latency 2653 ms và waterfall cho thấy retrieval mất 2.50 giây, còn generation khoảng 152 ms.
- **Vai trò của prompt version, token/cost, SLO hoặc rollback trong vận hành LLM:** Prompt version giúp truy xuất nội dung ứng dụng đã dùng. Label production cho phép promote/rollback mà không sửa code. Token/cost giúp quan sát mức sử dụng; SLO xác định mục tiêu dịch vụ và error budget lượng hóa mức sai lệch được phép.
- **Điều quan trọng nhất đã học:** Request trả HTTP 200 vẫn có thể gặp sự cố hiệu năng. Cần đối chiếu metrics, logs và traces trước khi kết luận nguyên nhân.
- **Hạn chế hoặc phần chưa hoàn thành, nếu có:** LLM, usage và cost là mô phỏng; quality_score là heuristic. Alert mới là đặc tả, chưa gửi Slack thực tế. Chưa có dữ liệu đủ 28 ngày để đánh giá SLO. Chưa xác minh đầy đủ nguyên nhân chênh lệch giữa latency phía client và thời gian xử lý được ghi trong trace.

## 9. Checklist trước khi nộp

- [ ] Kết quả và evidence thuộc commit SHA cuối.
- [ ] Tất cả ảnh/output mở được bằng đường dẫn tương đối.
- [x] Incident evidence nối đúng metric → log → trace.
- [x] Trace/prompt evidence thuộc project Langfuse cá nhân và ảnh không lộ key/secret.
- [ ] Repository chạy lại được theo README.
- [ ] Không có secret, API key, PII thô hoặc evidence của người khác/lớp khác.
- [ ] URL repo và commit SHA cuối đã được nộp trên LMS/Codelabs.

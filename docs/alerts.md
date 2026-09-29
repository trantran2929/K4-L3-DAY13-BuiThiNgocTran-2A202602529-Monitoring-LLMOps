# Template Alert và Runbook

Mỗi alert phải dựa trên triệu chứng người dùng hoặc SLO, không dựa trực tiếp vào tên implementation nội bộ.

Các điều kiện trong config/alert_rules.yaml là đặc tả cho lab, chưa được kết nối với một hệ thống gửi thông báo Slack.
Kênh dự kiến: #day13-alerts.
Owner: Bùi Thị Ngọc Trân.

Không đánh giá alert khi không đủ số mẫu tối thiểu.
Không coi thiếu dữ liệu là trạng thái hệ thống khỏe.

## Alert 1

- Tên: high_response_latency
- Severity: warning
- Duration: 5 phút
- Kênh thông báo: Slack #day13-alerts
- SLI/SLO liên quan: request thành công trong tối đa 3000 ms.
- Điều kiện và thời gian duy trì: P95 latency của response_sent trong cửa sổ 5 phút vượt 3000 ms, có ít nhất 20 mẫu, duy trì liên tục 5 phút.
- Ảnh hưởng tới người dùng: người dùng phải chờ câu trả lời lâu.
- Ba bước kiểm tra đầu tiên:
    1. Xem panel latency và traffic, xác định thời điểm bắt đầu tăng.
    2. Lọc response_sent có latency_ms > 3000, lấy correlation_id.
    3. Mở trace tương ứng, xem waterfall để phân biệt retrieval, generation hoặc bước khác gây chậm.
- Mitigation tạm thời:
    - Nếu đang bật incident thử nghiệm, tắt đúng incident đó.
    - Nếu lỗi bắt đầu sau một thay đổi, xác minh và rollback thay đổi.
    - Chạy lại cùng workload, kiểm tra latency đã phục hồi.
- Owner:Bùi Thị Ngọc Trân

## Alert 2


- Tên: high_request_error_rate
- Severity: critical
- Duration: 5 phút
- Kênh thông báo: Slack #day13-alerts
- SLI/SLO liên quan: tỷ lệ request thất bại; guardrail tối đa 2%.
- Điều kiện và thời gian duy trì: count(request_failed) / count(request_received) × 100 vượt 2% trong cửa sổ 5 phút, có ít nhất 20 request, duy trì liên tục 5 phút.
- Ảnh hưởng tới người dùng: người dùng không nhận được câu trả lời.
- Ba bước kiểm tra đầu tiên:
    1. Xem error rate và breakdown theo error_type.
    2. Tìm request_failed trong cùng khoảng thời gian, lấy correlation_id.
    3. Mở trace tương ứng, kiểm tra observation lỗi và dependency liên quan.
- Mitigation tạm thời:
    - Khôi phục dependency gặp lỗi hoặc rollback thay đổi gây lỗi.
    - Nếu lỗi do incident thử nghiệm, tắt đúng incident đó.
    - Chạy lại workload và xác nhận không phát sinh lỗi mới.
- Owner: Bùi Thị Ngọc Trân

## Alert 3

- Tên: low_response_quality
- Severity: warning
- Duration: 10 phút
- Kênh thông báo: Slack #day13-alerts
- SLI/SLO liên quan: quality_score trung bình tối thiểu 0.75.
- Điều kiện và thời gian duy trì: mean(quality_score) < 0.75 trong cửa sổ 10 phút, có ít nhất 20 response_sent có điểm, duy trì liên tục 10 phút.
- Ảnh hưởng tới người dùng: câu trả lời có thể kém hữu ích hoặc thiếu ngữ cảnh.
- Ba bước kiểm tra đầu tiên:
    1. Xem quality trung bình, số mẫu và thời điểm suy giảm.
    2. Đối chiếu retrieval success và log của các request điểm thấp.
    3. Mở trace qua correlation_id, kiểm tra prompt name/version, retrieval và generation.
- Mitigation tạm thời:
    - Nếu xác minh candidate gây suy giảm, chuyển production về baseline.
    - Restart API để tránh prompt cache, chạy lại cùng workload.
    - Kiểm tra quality phục hồi và xem lại mẫu câu trả lời.
- Owner: Bùi Thị Ngọc Trân

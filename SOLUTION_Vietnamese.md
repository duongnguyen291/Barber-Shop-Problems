# Phân tích giải pháp Sleeping Barber Problem

## 1. Các thành phần đồng bộ hóa chính

### Cấu trúc dữ liệu và cơ chế đồng bộ:
- `Queue waiting_customers`: Hàng đợi có giới hạn (MAX_CHAIRS = 3) để quản lý khách hàng chờ
- `Event barber_ready`: Sự kiện báo thợ cắt sẵn sàng
- `Event customer_ready`: Sự kiện báo có khách hàng đến
- `Lock mutex`: Khóa để đồng bộ hóa truy cập vào tài nguyên dùng chung

### Các thread chính:
- Thread thợ cắt tóc (Barber thread)
- Thread khách hàng (Customer threads)
- Thread điều khiển cửa hàng (Shop controller)
- Thread kiểm tra đóng cửa (Closing checker)
- Thread xử lý input (Input handler)

## 2. Giải quyết các vấn đề đồng bộ

### 2.1. Race Condition
Code giải quyết race condition thông qua:
- Sử dụng mutex lock khi thêm khách vào hàng đợi:
```python
with mutex:
    if waiting_customers.full():
        # xử lý khi hết ghế
    waiting_customers.put(customer_id)
```
- Sử dụng Queue thread-safe để quản lý danh sách khách hàng chờ
- Các biến trạng thái được bảo vệ bởi mutex

### 2.2. Deadlock Prevention
Code ngăn chặn deadlock bằng cách:
- Sử dụng timeout trong việc chờ đợi khách:
```python
customer_ready.wait(timeout=1)
```
- Không có circular waiting: các tài nguyên được cấp phát theo thứ tự
- Thợ cắt tóc có thể thoát khỏi trạng thái chờ nếu shop đóng cửa

### 2.3. Resource Starvation
Giải quyết starvation thông qua:
- Sử dụng Queue FIFO đảm bảo khách hàng được phục vụ theo thứ tự đến
- Giới hạn số ghế chờ (MAX_CHAIRS = 3) để tránh khách đợi quá lâu
- Cơ chế tự động đóng cửa sau 4 giây không có khách mới

## 3. Luồng xử lý chính

### Luồng thợ cắt:
1. Kiểm tra có khách trong hàng đợi
2. Nếu không có khách:
   - In thông báo ngủ
   - Chờ signal từ khách (với timeout)
3. Nếu có khách:
   - Lấy khách từ hàng đợi
   - Thực hiện cắt tóc (sleep random 3-6s)
   - Hoàn thành và thông báo

### Luồng khách hàng:
1. Kiểm tra shop có mở cửa
2. Kiểm tra và thêm vào hàng đợi (có mutex)
3. Signal cho thợ cắt biết có khách mới
4. Rời đi nếu hết ghế

## 4. Cơ chế đóng cửa an toàn
- Kiểm tra tự động đóng sau 4s không có khách
- Cho phép đóng thủ công bằng phím 'q'
- Đợi phục vụ hết khách trong hàng đợi trước khi đóng hoàn toàn

## 5. Ưu điểm của giải pháp
1. Thread-safe: Sử dụng đúng các cơ chế đồng bộ hóa
2. No deadlock: Có timeout và thoát an toàn
3. Fair scheduling: FIFO queue cho khách hàng
4. Resource efficient: Giới hạn số ghế chờ
5. Graceful shutdown: Đóng cửa an toàn và phục vụ hết khách
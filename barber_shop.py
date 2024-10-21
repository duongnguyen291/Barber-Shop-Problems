import threading
import time
import random

# Define the maximum number of customers and the number of chairs in the waiting room
MAX_CUSTOMERS = 6
NUM_WAITING_CHAIRS = 3
TIMEOUT = 5  # Thời gian tối đa không có khách hàng (tính bằng giây)

# Define the semaphores for the barber, the customers, and the mutex
barber_semaphore = threading.Semaphore(0)
customer_semaphore = threading.Semaphore(0)
mutex = threading.Semaphore(1)

# Define a list to keep track of the waiting customers
waiting_customers = []

# Thời gian của khách hàng cuối cùng vào
last_customer_time = time.time()
program_running = True

def print_shop_status(action, extra_info=""):
    print("\n" + "=" * 25 +"BARBER SHOP" + "=" * 25+ "\n")
    print(f"| Hành động: {action}\n")
    print(f"| Trạng thái barber shop: {'Đang mở' if program_running else 'Đóng cửa'}\n")
    print(f"| Danh sách khách đang chờ: {waiting_customers if waiting_customers else 'Không có khách'}\n")
    if extra_info:
        print(f"Thông tin khác: {extra_info}")
    print("\n"+"=" * 59 + "\n")

# Define the barber thread function
def barber():
    global last_customer_time, program_running
    while program_running:
        current_time = time.time()
        # Kiểm tra xem có quá thời gian chờ mà không có khách hàng nào không
        if len(waiting_customers) == 0:
            if current_time - last_customer_time > TIMEOUT:
                print_shop_status("Không có khách hơn 5 giây. Đóng cửa tiệm.")
                program_running = False
                break
            print_shop_status("Thợ cắt tóc đang ngủ")
            time.sleep(1)  # Giảm tần suất kiểm tra xuống 1 giây để tránh tiêu tốn tài nguyên
        else:
            print_shop_status("Thợ mời khách vào cắt tóc")
            barber_semaphore.acquire()
            mutex.acquire()
            if len(waiting_customers) > 0:
                customer = waiting_customers.pop(0)
                print_shop_status(f"Thợ đang cắt tóc cho khách hàng {customer}")
                mutex.release()
                time.sleep(random.randint(1, 5))
                print_shop_status(f"Thợ đã cắt tóc xong cho khách hàng {customer}")
                customer_semaphore.release()
            else:
                mutex.release()

# Define the customer thread function
def customer(index):
    global waiting_customers, last_customer_time, program_running
    time.sleep(random.randint(1, 5))
    if program_running:
        mutex.acquire()
        if len(waiting_customers) < NUM_WAITING_CHAIRS:
            waiting_customers.append(index)
            last_customer_time = time.time()  # Cập nhật thời gian khách hàng cuối cùng
            print_shop_status(f"Khách hàng {index} đang chờ trong phòng chờ")
            mutex.release()
            barber_semaphore.release()
            customer_semaphore.acquire()
            print_shop_status(f"Khách hàng {index} đã cắt tóc xong")
        else:
            print_shop_status(f"Khách hàng {index} rời đi vì phòng chờ đã đầy")
            mutex.release()

# Create a thread for the barber
barber_thread = threading.Thread(target=barber)

# Create a thread for each customer
customer_threads = []
for i in range(MAX_CUSTOMERS):
    customer_threads.append(threading.Thread(target=customer, args=(i,)))

# Start the barber and customer threads
barber_thread.start()
for thread in customer_threads:
    thread.start()

# Wait for the customer threads to finish
for thread in customer_threads:
    thread.join()

# Wait for the barber thread to finish
barber_thread.join()

print_shop_status("Tiệm cắt tóc đã đóng cửa")

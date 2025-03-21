import threading
import time
import random
from queue import Queue
import sys
from datetime import datetime
import keyboard
from datetime import datetime
import colorama
from colorama import Fore, Back, Style
import contextlib

# Khởi tạo các biến toàn cục
MAX_CHAIRS = 3  # Số ghế chờ tối đa (có thể thay đổi tùy case)
NO_OF_BARBERS = 1  # Số thợ cắt tóc
waiting_customers = Queue(MAX_CHAIRS)  # Hàng đợi khách hàng
barber_ready = threading.Event()  # Sự kiện thợ cắt sẵn sàng
customer_ready = threading.Event()  # Sự kiện khách hàng sẵn sàng
mutex = threading.Lock()  # Mutex để đồng bộ hóa truy cập
program_running = True  # Biến kiểm soát chương trình
last_customer_time = time.time()  # Thời gian khách cuối cùng đến
test_case = 1  # Trường hợp test mặc định

# Khởi tạo colorama để hỗ trợ màu trong terminal Windows
colorama.init()

def show_menu():
    global test_case
    print("\nChọn trường hợp test để bắt đầu:")
    print("1. Trường hợp 1: Khách đến với tốc độ đều đặn, đủ ghế chờ cho tất cả khách")
    print("2. Trường hợp 2: Khách đến thường xuyên, ít ghế chờ hơn, kiểm tra khách rời đi khi hết chỗ")
    print("3. Trường hợp 3: Khách đến ngẫu nhiên không đều, kiểm tra phản ứng khi tải không thể dự đoán")
    print("4. Trường hợp 4: Nhiều khách đến đồng thời, kiểm tra hiệu quả cơ chế khóa tránh xung đột")
    test_case = int(input("Nhập số từ 1 đến 4 để chọn trường hợp: "))

def create_progress_bar(current, total, width=20):
    """Tạo thanh tiến trình trực quan cho số ghế trống"""
    filled = int(width * current / total)
    bar = '█' * filled + '░' * (width - filled)
    return f"[{bar}]"

def format_customer_list(customers):
    """Format danh sách khách hàng với màu sắc"""
    if not customers:
        return f"{Fore.YELLOW}Không có khách{Style.RESET_ALL}"
    
    formatted = []
    for customer in customers:
        formatted.append(f"{Fore.CYAN}Khách {customer}{Style.RESET_ALL}")
    return ", ".join(formatted)

def get_current_time():
    return datetime.now().strftime("%H:%M:%S")

def print_shop_status(action, extra_info=""):
    """In trạng thái tiệm cắt tóc với định dạng và màu sắc đẹp mắt"""
    
    # Tạo border với màu
    border_color = Fore.BLUE if program_running else Fore.RED
    title = f"{border_color}╔{'═' * 58}╗{Style.RESET_ALL}"
    footer = f"{border_color}╚{'═' * 58}╝{Style.RESET_ALL}"
    
    # Tính số ghế trống
    empty_chairs = MAX_CHAIRS - waiting_customers.qsize()
    chairs_status = create_progress_bar(empty_chairs, MAX_CHAIRS)
    
    # Định dạng trạng thái shop
    shop_status = f"{Fore.GREEN}Đang mở{Style.RESET_ALL}" if program_running else f"{Fore.RED}Đóng cửa{Style.RESET_ALL}"
    
    # In thông tin được định dạng
    output = "\n" + title + "\n"
    output += f"{border_color}║{Style.RESET_ALL} {'BARBER SHOP':^56} {border_color}║{Style.RESET_ALL}\n"
    output += f"{border_color}╠{'═' * 58}╣{Style.RESET_ALL}\n"
    output += f"{border_color}║{Style.RESET_ALL} Thời gian : {Fore.YELLOW}{get_current_time()}{Style.RESET_ALL}\n"
    output += f"{border_color}║{Style.RESET_ALL} Trạng thái: {shop_status}\n"
    output += f"{border_color}║{Style.RESET_ALL} Hành động : {Fore.WHITE}{action}{Style.RESET_ALL}\n"
    output += f"{border_color}╟{'─' * 58}╢{Style.RESET_ALL}\n"
    output += f"{border_color}║{Style.RESET_ALL} Ghế trống : {empty_chairs}/{MAX_CHAIRS} {chairs_status}\n"
    output += f"{border_color}║{Style.RESET_ALL} Danh sách chờ: {format_customer_list(list(waiting_customers.queue) if not waiting_customers.empty() else None)}\n"
    
    if extra_info:
        output += f"{border_color}╟{'─' * 58}╢{Style.RESET_ALL}\n"
        output += f"{border_color}║{Style.RESET_ALL} {Fore.MAGENTA}→ {extra_info}{Style.RESET_ALL}\n"
    
    output += footer + "\n"
    
    print(output)
    # Ghi thông tin vào file
    with open("output.txt", "a", encoding="utf-8") as f:
        f.write(output + "\n")

def check_closing_conditions():
    global program_running
    while program_running:
        current_time = time.time()
        if current_time - last_customer_time > 5 and waiting_customers.empty():
            print_shop_status("Đóng cửa tự động do không có khách trong 4 giây")
            program_running = False
            customer_ready.set()  # Đánh thức thợ cắt để kết thúc
            break
        time.sleep(0.1)

def handle_user_input():
    global program_running
    while program_running:
        if keyboard.is_pressed('q'):
            print_shop_status("Nhận lệnh đóng cửa từ người dùng (Q)")
            program_running = False
            customer_ready.set()
            break
        time.sleep(0.1)

def barber(barber_id):
    global program_running
    while program_running or not waiting_customers.empty():
        if waiting_customers.empty():
            print_shop_status(f"Thợ cắt tóc {barber_id} đang ngủ vì không có khách")
            customer_ready.wait(timeout=1)  # Timeout để kiểm tra điều kiện đóng
            customer_ready.clear()
            if not program_running and waiting_customers.empty():
                break

        try:
            customer_id = waiting_customers.get_nowait()
            print_shop_status(f"Thợ cắt tóc {barber_id} đang phục vụ khách {customer_id}")
            cutting_time = random.randint(3, 6)
            time.sleep(cutting_time)  # Thời gian cắt tóc
            print_shop_status(f"Thợ cắt tóc {barber_id} đã hoàn thành phục vụ khách {customer_id}", 
                            f"Thời gian cắt: {cutting_time}s")
        except:
            pass

def customer(customer_id):
    global program_running, last_customer_time

    if not program_running:
        print_shop_status(f"Khách {customer_id} đến nhưng tiệm đã đóng cửa")
        return

    with mutex:
        if waiting_customers.full():
            print_shop_status(f"Khách {customer_id} rời đi vì không còn ghế trống")
            return

        waiting_customers.put(customer_id)
        last_customer_time = time.time()  # Cập nhật thời gian khách cuối
        print_shop_status(f"Khách {customer_id} đang chờ đến lượt")

    customer_ready.set()  # Đánh thức thợ cắt

def simulate_customers(case):
    customer_id = 1
    while program_running:
        try:
            if case == 1:
                time.sleep(2)  # Khách đến đều đặn
            elif case == 2:
                time.sleep(1)  # Khách đến nhanh, dễ đầy ghế
            elif case == 3:
                time.sleep(random.randint(1, 5))  # Khách đến ngẫu nhiên
            elif case == 4:
                # Giả lập nhiều khách đến cùng lúc
                threads = []
                for _ in range(random.randint(2, 5)):
                    customer_thread = threading.Thread(target=customer, args=(customer_id,))
                    threads.append(customer_thread)
                    customer_thread.start()
                    customer_id += 1
                for t in threads:
                    t.join()
                time.sleep(3)  # Khoảng cách giữa các lần nhiều khách đến
            else:
                break
            if program_running:
                customer_thread = threading.Thread(target=customer, args=(customer_id,))
                customer_thread.start()
                customer_id += 1
        except Exception as e:
            print(f"Lỗi: {e}")
            break

def shop_controller():
    # Khởi tạo các thợ cắt tóc
    barbers = []
    for i in range(NO_OF_BARBERS):
        barber_thread = threading.Thread(target=barber, args=(i+1,))
        barber_thread.start()
        barbers.append(barber_thread)

    # Khởi động thread kiểm tra điều kiện đóng cửa
    closing_checker = threading.Thread(target=check_closing_conditions)
    closing_checker.daemon = True
    closing_checker.start()

    # Khởi động thread xử lý input người dùng
    input_handler = threading.Thread(target=handle_user_input)
    input_handler.daemon = True
    input_handler.start()

    # Chạy kịch bản khách hàng
    simulate_customers(test_case)

    # Đợi tất cả thợ cắt hoàn thành công việc
    print_shop_status("Tiệm đang đóng cửa, chờ phục vụ nốt khách còn lại")
    for barber_thread in barbers:
        barber_thread.join()

    print_shop_status("Tiệm đã đóng cửa hoàn toàn")
    sys.exit(0)

if __name__ == "__main__":
    show_menu()
    print_shop_status("Tiệm đang mở cửa", "Khởi động hệ thống...")
    shop_controller()

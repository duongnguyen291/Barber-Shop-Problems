#include <stdio.h>
#include <stdlib.h>
#include <pthread.h>
#include <unistd.h>
#include <time.h>
#include <stdbool.h>
#include <string.h>

// Định nghĩa màu sắc cho console
#define RESET   "\x1B[0m"
#define RED     "\x1B[31m"
#define GREEN   "\x1B[32m"
#define YELLOW  "\x1B[33m"
#define BLUE    "\x1B[34m"
#define MAGENTA "\x1B[35m"
#define CYAN    "\x1B[36m"
#define WHITE   "\x1B[37m"

// Các biến cấu hình từ người dùng
int MAX_CHAIRS;      // Số ghế chờ tối đa
int NO_OF_BARBERS;   // Số thợ cắt tóc
int MAX_CUSTOMERS;   // Số khách hàng tối đa mỗi phiên
int TOTAL_TIME;      // Thời gian hoạt động tối đa (giây)

// Khai báo cấu trúc hàng đợi
typedef struct {
    int* customers;
    int front;
    int rear;
    int count;
    int capacity;
} Queue;

// Biến toàn cục
Queue* waiting_room;
pthread_mutex_t mutex;
pthread_cond_t barber_sleeping;
pthread_cond_t customer_waiting;
bool shop_open = true;
time_t last_customer_time;
time_t shop_start_time;
int current_scenario = 0;

// Các hàm queue giữ nguyên như cũ
Queue* create_queue(int capacity) {
    Queue* queue = (Queue*)malloc(sizeof(Queue));
    queue->capacity = capacity;
    queue->front = 0;
    queue->rear = -1;
    queue->count = 0;
    queue->customers = (int*)malloc(sizeof(int) * capacity);
    return queue;
}

bool is_queue_full(Queue* queue) {
    return queue->count == queue->capacity;
}

bool is_queue_empty(Queue* queue) {
    return queue->count == 0;
}

bool enqueue(Queue* queue, int customer_id) {
    if (is_queue_full(queue)) return false;
    queue->rear = (queue->rear + 1) % queue->capacity;
    queue->customers[queue->rear] = customer_id;
    queue->count++;
    return true;
}

int dequeue(Queue* queue) {
    if (is_queue_empty(queue)) return -1;
    int customer = queue->customers[queue->front];
    queue->front = (queue->front + 1) % queue->capacity;
    queue->count--;
    return customer;
}

char* get_current_time() {
    time_t now = time(NULL);
    char* time_str = ctime(&now);
    time_str[strlen(time_str) - 1] = '\0';
    return time_str;
}

// Kiểm tra thời gian hoạt động
bool is_within_operation_time() {
    time_t current_time;
    time(&current_time);
    return difftime(current_time, shop_start_time) < TOTAL_TIME;
}

void print_shop_status(const char* action, int barber_id, int customer_id) {
    time_t current_time;
    time(&current_time);
    double elapsed_time = difftime(current_time, shop_start_time);
    
    printf("\n%s╔═══════════════════════ BARBER SHOP STATUS ════════════════════════╗%s\n", BLUE, RESET);
    printf("%s%s Time: %s%s\n", BLUE, RESET, get_current_time(), RESET);
    printf("%s%s Elapsed Time: %.2f/%d seconds%s\n", BLUE, RESET, elapsed_time, TOTAL_TIME, RESET);
    printf("%s%s Status: %s%s%s\n", BLUE, RESET,
           shop_open ? GREEN : RED,
           shop_open ? "OPEN" : "CLOSED",
           RESET);
    printf("%s%s Action: %s%s%s\n", BLUE, RESET, WHITE, action, RESET);
    printf("%s%s Waiting customers: %d/%d\n", BLUE, RESET, 
           waiting_room->count, waiting_room->capacity);
    
    if (barber_id >= 0 && customer_id >= 0) {
        printf("%s%s Current service: Barber %d -> Customer %d\n", 
               BLUE, RESET, barber_id, customer_id);
    }
    
    printf("%s╚═══════════════════════════════════════════════════════════════════╝%s\n\n", BLUE, RESET);
}

void* barber_function(void* arg) {
    int barber_id = *(int*)arg;
    
    while (shop_open || !is_queue_empty(waiting_room)) {
        pthread_mutex_lock(&mutex);
        
        while (is_queue_empty(waiting_room) && shop_open) {
            print_shop_status("Barber is sleeping", barber_id, -1);
            pthread_cond_wait(&customer_waiting, &mutex);
        }
        
        if (!shop_open && is_queue_empty(waiting_room)) {
            pthread_mutex_unlock(&mutex);
            break;
        }
        
        int customer_id = dequeue(waiting_room);
        print_shop_status("Started cutting hair", barber_id, customer_id);
        
        pthread_mutex_unlock(&mutex);
        
        int cutting_time = 2 + rand() % 3;
        sleep(cutting_time);
        
        print_shop_status("Finished cutting hair", barber_id, customer_id);
        pthread_cond_signal(&barber_sleeping);
    }
    
    return NULL;
}

void* customer_function(void* arg) {
    int customer_id = *(int*)arg;
    free(arg);
    
    pthread_mutex_lock(&mutex);
    
    if (!shop_open || !is_within_operation_time()) {
        print_shop_status("Customer arrived but shop is closed or over time limit", -1, customer_id);
        pthread_mutex_unlock(&mutex);
        return NULL;
    }
    
    if (is_queue_full(waiting_room)) {
        print_shop_status("Customer left - no empty seats", -1, customer_id);
        pthread_mutex_unlock(&mutex);
        return NULL;
    }
    
    enqueue(waiting_room, customer_id);
    time(&last_customer_time);
    print_shop_status("Customer waiting", -1, customer_id);
    
    pthread_cond_signal(&customer_waiting);
    pthread_mutex_unlock(&mutex);
    
    return NULL;
}

void* check_closing_conditions(void* arg) {
    while (shop_open) {
        time_t current_time;
        time(&current_time);
        
        // Kiểm tra cả điều kiện thời gian và không có khách
        if ((!is_within_operation_time() || 
             difftime(current_time, last_customer_time) > 4) && 
            is_queue_empty(waiting_room)) {
            pthread_mutex_lock(&mutex);
            if (!is_within_operation_time()) {
                print_shop_status("Closing - Maximum operation time reached", -1, -1);
            } else {
                print_shop_status("Auto closing - no customers for 4 seconds", -1, -1);
            }
            shop_open = false;
            pthread_cond_broadcast(&customer_waiting);
            pthread_mutex_unlock(&mutex);
            break;
        }
        sleep(1);
    }
    return NULL;
}

// Scenarios
void regular_scenario() {
    sleep(2);
}

void rush_scenario() {
    sleep(1);
}

void random_scenario() {
    sleep(1 + rand() % 5);
}

void batch_arrival() {
    int num_customers = 2 + rand() % 4;
    for(int i = 0; i < num_customers && shop_open && is_within_operation_time(); i++) {
        int* customer_id = malloc(sizeof(int));
        *customer_id = rand() % 1000;
        pthread_t customer_thread;
        pthread_create(&customer_thread, NULL, customer_function, customer_id);
        pthread_detach(customer_thread);
    }
    sleep(3);
}

void run_simulation() {
    pthread_mutex_init(&mutex, NULL);
    pthread_cond_init(&barber_sleeping, NULL);
    pthread_cond_init(&customer_waiting, NULL);
    waiting_room = create_queue(MAX_CHAIRS);
    shop_open = true;
    time(&last_customer_time);
    time(&shop_start_time);
    
    // Tạo các thread thợ cắt
    pthread_t* barber_threads = malloc(sizeof(pthread_t) * NO_OF_BARBERS);
    int* barber_ids = malloc(sizeof(int) * NO_OF_BARBERS);
    for(int i = 0; i < NO_OF_BARBERS; i++) {
        barber_ids[i] = i + 1;
        pthread_create(&barber_threads[i], NULL, barber_function, &barber_ids[i]);
    }
    
    pthread_t checker_thread;
    pthread_create(&checker_thread, NULL, check_closing_conditions, NULL);
    
    int customer_count = 0;
    while (shop_open && customer_count < MAX_CUSTOMERS && is_within_operation_time()) {
        int* customer_id = malloc(sizeof(int));
        *customer_id = ++customer_count;
        
        pthread_t customer_thread;
        pthread_create(&customer_thread, NULL, customer_function, customer_id);
        pthread_detach(customer_thread);
        
        switch (current_scenario) {
            case 1: regular_scenario(); break;
            case 2: rush_scenario(); break;
            case 3: random_scenario(); break;
            case 4: batch_arrival(); break;
        }
    }
    
    // Chờ các thread thợ cắt
    for(int i = 0; i < NO_OF_BARBERS; i++) {
        pthread_join(barber_threads[i], NULL);
    }
    pthread_join(checker_thread, NULL);
    
    // Giải phóng bộ nhớ
    free(barber_threads);
    free(barber_ids);
    pthread_mutex_destroy(&mutex);
    pthread_cond_destroy(&barber_sleeping);
    pthread_cond_destroy(&customer_waiting);
    free(waiting_room->customers);
    free(waiting_room);
}

int main() {
    srand(time(NULL));

    while(1) {
        printf("\n%sBARBER SHOP SIMULATION CONFIGURATION%s\n", YELLOW, RESET);
        printf("Enter number of chairs (1-10): ");
        scanf("%d", &MAX_CHAIRS);
        printf("Enter number of barbers (1-5): ");
        scanf("%d", &NO_OF_BARBERS);
        printf("Enter maximum number of customers (1-50): ");
        scanf("%d", &MAX_CUSTOMERS);
        printf("Enter total operation time in seconds (10-300): ");
        scanf("%d", &TOTAL_TIME);
        
        // Validate input
        if (MAX_CHAIRS < 1 || MAX_CHAIRS > 10 ||
            NO_OF_BARBERS < 1 || NO_OF_BARBERS > 5 ||
            MAX_CUSTOMERS < 1 || MAX_CUSTOMERS > 50 ||
            TOTAL_TIME < 10 || TOTAL_TIME > 300) {
            printf("%sInvalid input values. Please try again.%s\n", RED, RESET);
            continue;
        }
        else break;
    }
    
    while (1) {
        printf("\n%sBARBER SHOP SIMULATION%s\n", YELLOW, RESET);
        printf("Choose a scenario:\n");
        printf("1. Regular Customers (2s interval)\n");
        printf("2. Rush Hour (1s interval)\n");
        printf("3. Random Arrivals (1-5s interval)\n");
        printf("4. Batch Arrivals (2-5 customers at once)\n");
        printf("5. Exit\n");
        
        printf("\nEnter your choice (1-5): ");
        scanf("%d", &current_scenario);
        
        if (current_scenario == 5) break;
        
        if (current_scenario >= 1 && current_scenario <= 4) {
            printf("\n%sStarting simulation with scenario %d...%s\n", 
                   GREEN, current_scenario, RESET);
            run_simulation();
            printf("\n%sSimulation completed!%s\n", GREEN, RESET);
        } else {
            printf("%sInvalid choice. Please try again.%s\n", RED, RESET);
        }
    }
    
    return 0;
}

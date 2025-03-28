# Barber Shop Problem in Operating Systems

## Introduction

The **Barber Shop Problem** is a classic synchronization problem in Operating Systems, often used to illustrate the concept of inter-process communication, mutual exclusion, and resource sharing among multiple threads or processes.

In this problem, we model a barber shop with:
- **A Barber**: The person who cuts hair.
- **Customers**: The people who arrive randomly to get a haircut.
- **Waiting Chairs**: A limited number of chairs where customers can wait if the barber is busy.

The challenge is to ensure that:
- The barber works only when there are customers.
- Customers wait if the barber is busy, but leave if no waiting chairs are available.
- Proper synchronization between the barber and customers to avoid race conditions, deadlock, or resource starvation.

## Problem Description

- **Barber**: The barber starts by sleeping if there are no customers. When a customer arrives, the barber wakes up and invites the customer for a haircut. After cutting the customer's hair, the barber checks if there are more customers waiting. If not, the barber goes back to sleep.
  
- **Customers**: Customers arrive randomly. If the barber is available, the customer gets a haircut immediately. If the barber is busy but there are empty waiting chairs, the customer waits in one of the chairs. If there are no empty chairs, the customer leaves the shop.

## Solution Approach

This problem is solved using semaphores and mutexes to synchronize the actions of the barber and the customers:
- **Semaphore** is used to signal the state of the barber (whether he's available or not).
- **Mutex** ensures that shared resources (like the waiting chair list) are accessed in a thread-safe manner.

### Key Components:
1. **Barber Thread**:
   - Sleeps when no customers are present.
   - Wakes up when a customer arrives.
   - Cuts the hair for a customer and then checks if there are more customers.

2. **Customer Threads**:
   - Arrive at random intervals.
   - Wait in the waiting room if chairs are available.
   - Leave the shop if the waiting room is full.

3. **Synchronization**:
   - The barber and customers are synchronized using semaphores and mutexes to ensure mutual exclusion and prevent race conditions.

### Constraints:
- There are only a limited number of waiting chairs (`NUM_WAITING_CHAIRS`).
- Customers arrive randomly, and the barber cuts hair in random durations.
### Member:
- Nguyễn Đình Dương - 20225966 - duong.nd225966@sis.hust.edu.vn
- Đặng Văn Nhân - 20225990
- Nguyễn Trọng Minh Phương - 20225992
- Bùi Hà My - 20225987
## How to Run the Program

### Prerequisites:
- Python 3.x installed on your machine.

### Steps:
1. Clone this repository or download the code files.
2. Ensure you have the necessary Python environment.
3. Run the program with:
   ```bash
   python barber_shop.py


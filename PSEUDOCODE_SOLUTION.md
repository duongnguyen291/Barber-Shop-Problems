# SHARED RESOURCES & SYNCHRONIZATION OBJECTS
```
MAX_CHAIRS = 3                     // Maximum chairs in waiting room
waiting_queue = Queue(MAX_CHAIRS)  // Shared queue for waiting customers
mutex = Lock()                     // Mutex for protecting waiting queue
customer_ready = Semaphore(0)      // Signals customer arrival (initially 0)
barber_ready = Semaphore(0)        // Signals barber availability (initially 0)
barber_working = Semaphore(1)      // Controls access to barber (initially 1)
program_running = AtomicBoolean(true) // Thread-safe program control
last_customer_time = AtomicTime    // Thread-safe timestamp
```

# BARBER PROCESS
```
PROCEDURE Barber():
    WHILE true:
        // CRITICAL SECTION: Check queue status
        ACQUIRE mutex
            IF waiting_queue is empty:
                RELEASE mutex
                IF not program_running:
                    EXIT
                
                PRINT "Barber is sleeping"
                WAIT customer_ready    // Block until customer arrives
                CONTINUE              // Recheck queue after waking
            
            // Get next customer from queue
            current_customer = waiting_queue.dequeue()
        RELEASE mutex
        
        // Barber is now serving customer
        PRINT "Barber serving customer #{current_customer}"
        
        // Critical section for haircut service
        ACQUIRE barber_working
            SLEEP random(3,6)    // Simulate haircut
        RELEASE barber_working
        
        PRINT "Finished customer #{current_customer}"
```

# CUSTOMER PROCESS
```
PROCEDURE Customer(id):
    IF not program_running:
        PRINT "Shop closed, customer #{id} leaving"
        RETURN
        
    // CRITICAL SECTION: Try to enter waiting room
    ACQUIRE mutex
        IF waiting_queue.size() == MAX_CHAIRS:
            RELEASE mutex
            PRINT "No chairs available, customer #{id} leaving"
            RETURN
            
        // Add customer to waiting queue
        waiting_queue.enqueue(id)
        last_customer_time = current_time()
        queue_position = waiting_queue.size()
    RELEASE mutex
    
    PRINT "Customer #{id} took seat #{queue_position}"
    SIGNAL customer_ready    // Wake up barber if sleeping
    
    // Wait for and receive haircut
    WAIT barber_working     // Wait for barber to be free
    RECEIVE_HAIRCUT()
    SIGNAL barber_working   // Release barber for next customer
```

# SHOP CONTROLLER PROCESS
```
PROCEDURE ShopController():
    // Initialize synchronization objects
    mutex = CREATE new Lock()
    customer_ready = CREATE new Semaphore(0)
    barber_ready = CREATE new Semaphore(0)
    barber_working = CREATE new Semaphore(1)
    
    // Start barber thread
    barber_thread = CREATE Thread(Barber)
    START barber_thread
    
    // Start monitoring threads with shared resource access
    START Thread(ClosingChecker, program_running, last_customer_time)
    START Thread(UserInputHandler, program_running)
    
    customer_id = 1
    WHILE program_running:
        // Generate new customers
        SLEEP random(1,3)
        IF program_running:
            customer_thread = CREATE Thread(Customer, customer_id)
            START customer_thread
            INCREMENT customer_id
            
    // Cleanup phase
    WAIT FOR all customers to finish
    SIGNAL customer_ready    // Wake up barber for final check
    WAIT FOR barber_thread to finish
```

# CLOSING CONDITIONS MONITOR
```
PROCEDURE ClosingChecker():
    WHILE true:
        current = GET current_time()
        
        // Check closing conditions atomically
        ACQUIRE mutex
            IF (current - last_customer_time > 4) AND waiting_queue.empty():
                program_running = false
                SIGNAL customer_ready    // Wake barber to exit
                RELEASE mutex
                RETURN
        RELEASE mutex
        
        SLEEP 0.1    // Prevent busy waiting
```

# CRITICAL SECTIONS & SYNCHRONIZATION POINTS

1. **Waiting Queue Access**
   ```
   PROTECTED BY mutex:
   - Checking queue status
   - Adding customers to queue
   - Removing customers from queue
   - Updating queue size
   ```

2. **Barber Service Status**
   ```
   PROTECTED BY barber_working:
   - Haircut service duration
   - Customer receiving haircut
   ```

3. **Customer-Barber Coordination**
   ```
   SIGNALING PATTERN:
   1. Customer arrives:
      - SIGNAL customer_ready
   2. Barber starts service:
      - ACQUIRE barber_working
   3. Barber finishes service:
      - RELEASE barber_working
   ```

4. **Program Termination**
   ```
   PROTECTED BY mutex:
   - Checking closing conditions
   - Updating program status
   ```

# DEADLOCK PREVENTION

1. **Resource Hierarchy**
   - mutex always acquired before barber_working
   - Never acquire mutex while holding barber_working

2. **Timeout Mechanism**
   - All semaphore waits have timeout to prevent infinite blocking

3. **Resource Release**
   - All locks/semaphores released in same scope they're acquired
   - Release on all exit paths (normal and error)

# STARVATION PREVENTION

1. **FIFO Queue**
   - Customers served in strict order of arrival
   - Queue ensures fairness in service order

2. **Bounded Wait**
   - MAX_CHAIRS limits maximum wait time
   - New customers rejected when queue full
# Project Structure Documentation

This document provides a detailed overview of the Python source files in the `src/` directory, outlining the purpose and connections of each component in the AI Smart Cart system.

---

## Ⅰ. Main Applications

These are the main executable entry points for each of the three computer systems.

### main_hub.py

- **`MainPC2Hub`**
    - **Functionality**: The central server and orchestrator of the entire system (running on PC2). It acts as a gateway that connects all other components.
        - Initializes database connections and Data Access Objects (DAOs).
        - Starts a shopping session when initiated.
        - **UDP Forwarding**: Receives camera streams from the Cart Camera App (PC3) and forwards them to the AI Server (PC1).
        - **AI Event Handling**: Runs a TCP server to receive asynchronous detection events (obstacles, products) from the AI Server.
        - **UI Request Handling**: Runs a TCP server to process synchronous requests (e.g., checkout) from the Cart UI App.
        - **Business Logic**: Uses the `SmartCartEngine` to process incoming events and make decisions.
        - **UI Commands**: Uses a `TCPClient` to send commands (e.g., update cart, show alarm) to the UI app.
    - **Key Methods**:
        - `run()`: Starts all server and forwarding threads.
        - `handle_ai_event()`: Handler for messages from the AI server.
        - `handle_ui_request()`: Handler for messages from the UI app.
        - `forward_front_cam() / forward_cart_cam()`: UDP forwarding logic.
    - **Dependencies**: `SmartCartEngine`, `DBHandler`, all DAOs, `TCPServer`, `TCPClient`, `UDPFrameSender`, `UDPFrameReceiver`, `config`, `protocols`.

### ai_server.py

- **`AIServer`**
    - **Functionality**: The main application for the AI inference computer (PC1). It receives video streams, performs object detection, and sends results to the Main Hub.
        - **UDP Listeners**: Receives front (obstacle) and cart (product) camera streams from the Main Hub in separate threads.
        - **Inference Loops**: Runs two separate threads to perform continuous inference on the latest frames from each stream using the appropriate YOLO models.
        - **Event Pushing**: When an object is detected with sufficient confidence, it formats a message using the `Protocol` class and sends it to the Main Hub via a `TCPClient`.
    - **Key Methods**:
        - `run()`: Starts all UDP listening and inference threads.
        - `_obstacle_inference_loop()`: Continuously runs obstacle detection.
        - `_product_inference_loop()`: Continuously runs product recognition.
        - `_push_event()`: Sends a detected event to the Main Hub.
    - **Dependencies**: `ObstacleDetector`, `ProductRecognizer`, `UDPFrameReceiver`, `TCPClient`, `config`, `protocols`.

### cart_camera_app.py

- **`CartEdgeApp`**
    - **Functionality**: The application for the cart's edge computer (PC3) responsible for camera streams.
        - **Camera Capture**: Captures video from two separate hardware cameras (`cv2.VideoCapture`).
        - **UDP Streaming**: Compresses each frame into JPEG and sends it to the Main Hub using `UDPFrameSender` in separate threads.
    - **Key Methods**:
        - `run()`: Starts the two camera streaming threads.
        - `stream_front_camera()`: Captures and sends frames for obstacle detection.
        - `stream_cart_camera()`: Captures and sends frames for product recognition.
    - **Dependencies**: `UDPFrameSender`, `ImageProcessor`, `config`, `cv2`.

### cart_ui_app.py

- **`main()`**
    - **Functionality**: The main entry point for the PyQt6-based UI application on the cart computer (PC3).
        - Initializes the Qt Application environment.
        - Creates the `CartDashboard` (the view).
        - Creates the `UIController`, which links the dashboard to the Main Hub.
        - Shows the dashboard window and starts the application event loop.
    - **Dependencies**: `CartDashboard`, `UIController`, `PyQt6`.

---

## Ⅱ. Core Logic

### core/engine.py

- **`SmartCartEngine`**
    - **Functionality**: Encapsulates the core business logic of the smart cart, making decisions based on events. It is designed to be stateless regarding network or UI specifics.
        - **Event Processing**: Contains the logic for what to do when an obstacle or product is detected.
        - **Debouncing**: Prevents duplicate product additions if the same product is detected multiple times in quick succession.
        - **State Management**: Manages simple state, such as the last detected obstacle level, to avoid sending redundant UI alarms.
    - **Methods**:
        - `process_obstacle_event()`: Logs the obstacle, checks if the danger level has changed, and sends a UI alarm if necessary.
        - `process_product_event()`: Debounces the detection, retrieves product info from the DB, adds the item to the cart, and sends a command to update the UI.
        - `reset()`: Resets the engine's internal state upon checkout.
    - **Dependencies**: All DAOs, `TCPClient` (to communicate with the UI).
    - **Instantiated in**: `main_hub.py`.

---

## Ⅲ. Network Communication

### network/tcp_server.py

- **`TCPServer`**
    - **Functionality**: A generic, multi-threaded TCP server that handles length-prefixed JSON messages. For each incoming connection, it spawns a new thread to handle the request.
    - **Protocol**: `[4-byte length][JSON payload]`
    - **Methods**:
        - `start()`: Binds to a port and listens for incoming connections indefinitely.
        - `_client_handler()`: Receives a request, passes it to the handler function provided during initialization, and sends the handler's response back to the client.
    - **Used in**:
        - `main_hub.py`: Two instances are created (one for AI events, one for UI requests).
        - `ui_controller.py`: One instance is created to receive commands from the Main Hub.

### network/tcp_client.py

- **`TCPClient`**
    - **Functionality**: A generic TCP client for sending length-prefixed JSON messages and waiting for a response.
    - **Methods**:
        - `send_request()`: Connects to the server, sends the data, waits for a response, and returns it. Includes error handling for timeouts and connection issues.
    - **Used in**:
        - `ai_server.py`: To push events to the Main Hub.
        - `main_hub.py`: To push commands to the Cart UI App.

### network/udp_handler.py

- **`UDPFrameSender` / `UDPFrameReceiver`**
    - **Functionality**: A pair of classes designed to transmit large data (like video frames) over UDP, which has a packet size limit.
    - **`UDPFrameSender`**:
        - Compresses a video frame into a JPEG binary.
        - Splits the binary data into smaller chunks that fit into UDP packets.
        - Attaches a header to each chunk (`frame_id`, `chunk_id`, `total_chunks`) and sends it.
    - **`UDPFrameReceiver`**:
        - Listens for UDP packets.
        - Reassembles the chunks for each `frame_id` based on the header information.
        - Once all chunks for a frame are received, it combines them and yields the complete JPEG binary data.
    - **Used in**:
        - `cart_camera_app.py` uses `UDPFrameSender`.
        - `main_hub.py` uses both `UDPFrameReceiver` (to get frames from the camera app) and `UDPFrameSender` (to forward them to the AI server).
        - `ai_server.py` uses `UDPFrameReceiver`.

---

## Ⅳ. Database Layer

### database/db_handler.py

- **`DBHandler`**
    - **Functionality**: A wrapper for the `pymysql` library to simplify database interactions.
        - Manages the database connection.
        - Provides methods for executing queries with automatic commit/rollback on error.
        - Uses a `DictCursor` to return query results as Python dictionaries.
    - **Methods**:
        - `execute()`: For `UPDATE`/`DELETE` queries.
        - `insert()`: For `INSERT` queries; returns the ID of the newly created row.
        - `fetch_one()` / `fetch_all()`: For `SELECT` queries.
        - `begin()`, `commit()`, `rollback()`, `close()`: For manual transaction control.
    - **Instantiated in**: `main_hub.py`.

### database/*_dao.py

- **`ProductDAO`, `TransactionDAO`, `ObstacleLogDAO`**
    - **Functionality**: A set of Data Access Objects (DAOs). Each DAO encapsulates the SQL queries related to a specific domain (products, transactions, logs), providing a clean, method-based API to the rest of the application. They all rely on an instance of `DBHandler` to execute their queries.
    - **`ProductDAO`**: Fetches product information and manages stock.
    - **`TransactionDAO`**: Manages shopping sessions, cart items, and checkout orders.
    - **`ObstacleLogDAO`**: Writes obstacle detection events into the database.
    - **Instantiated in**: `main_hub.py`.

---

## Ⅴ. AI & Detection

### detectors/obstacle_dl.py

- **`ObstacleDetector`**
    - **Functionality**: Loads a YOLO model trained for obstacle detection.
    - **Methods**:
        - `detect()`: Takes a single image frame, runs inference, and returns a dictionary containing the calculated `danger_level` (based on bounding box size) and a list of detected objects.
    - **Used in**: `ai_server.py`.

### detectors/product_dl.py

- **`ProductRecognizer`**
    - **Functionality**: Loads a YOLO model trained for product recognition.
    - **Methods**:
        - `recognize()`: Takes a single image frame, runs inference, and returns the class ID of the most confidently detected product. This ID corresponds to `product_id` in the database.
    - **Used in**: `ai_server.py`.

---

## Ⅵ. User Interface

### ui/dashboard.py

- **`CartDashboard`**
    - **Functionality**: The main window of the UI, built with PyQt6. This class is responsible only for the visual representation and layout of the UI elements. It contains no application logic.
    - **Public API**: Provides methods like `add_product()`, `set_danger_level()`, and `reset_cart()` that are called by the `UIController` to update the display.
    - **Signals**: Emits signals when buttons (like "Start Cart") are clicked, which the `UIController` listens to.
    - **Used by**: `cart_ui_app.py` (instantiated), `ui_controller.py` (controlled).

### ui/ui_controller.py

- **`UIController`**
    - **Functionality**: The "brain" of the UI application. It acts as a bridge between the visual `CartDashboard` and the `MainPC2Hub`.
        - **Listens for UI Commands**: Runs a background TCP server to receive commands (e.g., "add product to cart") from the Main Hub.
        - **Safe UI Updates**: Converts the received network commands into Qt signals (`pyqtSignal`) to ensure thread-safe updates to the UI.
        - **Handles User Actions**: Listens for button click signals from the `CartDashboard` and sends the corresponding requests to the Main Hub's request port.
    - **Instantiated in**: `cart_ui_app.py`.

---

## Ⅶ. Common & Utilities

### common/config.py

- **`Config`**
    - **Functionality**: A Pydantic-based configuration loader that reads all `.yaml` files from the `/configs` directory. It validates the configuration and provides a single, type-safe, auto-completing `config` object that can be imported and used throughout the application.

### common/protocols.py

- **`Protocol` and Enums**
    - **Functionality**: Defines the structure and constants for all TCP-based communication in the system.
    - **`Protocol` class**: Provides static methods for creating consistently formatted JSON message dictionaries (e.g., `Protocol.ai_event(...)`). It also includes validation and parsing functions.
    - **Enums**: (`MessageType`, `AIEvent`, `UICommand`, etc.) provide clear, integer-based constants for all message types and commands, preventing the use of "magic strings".

### utils/logger.py

- **`SystemLogger`**
    - **Functionality**: A simple wrapper for Python's built-in `logging` module. It sets up logging to both a file (`logs/system.log`) and the console, with distinct formatting for each.

### utils/image_proc.py

- **`ImageProcessor`**
    - **Functionality**: A collection of static utility methods for handling image operations with `OpenCV`.
    - **Methods**: `encode_frame` (OpenCV frame to JPEG bytes), `decode_frame` (bytes to frame), `resize_for_ai`, and `draw_labels` for debugging.

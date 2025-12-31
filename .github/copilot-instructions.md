# AI Smart Shopping Cart System - Copilot Instructions

## System Architecture

This is a distributed real-time AI system with **3 independent applications** communicating over TCP/UDP:

1. **AI Server (PC1)** - `src/ai_server.py`: Runs YOLO inference (obstacle detection + product recognition)
2. **Main Hub (PC2)** - `src/main_hub.py`: Central orchestrator, handles business logic, DB operations, routes data between components
3. **Edge Device (PC3)** - `src/cart_camera_app.py` + `src/cart_ui_app.py`: Camera streaming + PyQt6 dashboard UI

**Data flow**: Camera (PC3) → UDP frames → Main Hub (PC2) → UDP forward → AI Server (PC1) → TCP events → Main Hub → TCP commands → UI (PC3)

## Critical Architecture Patterns

### Communication Protocol
All inter-component messages use `src/common/protocols.py`:
- **TCP**: Length-prefixed JSON (`[4-byte length][JSON payload]`) for control messages/events
- **UDP**: Chunked JPEG frames via `network/udp_handler.py` (frames split into packets with `frame_id`, `chunk_id`, `total_chunks`)
- Message types are **integer enums** (`MessageType`, `AIEvent`, `UICommand`, `UIRequest`) - never use string literals
- Example: `Protocol.ai_event(AIEvent.PRODUCT_DETECTED, data={"product_id": 123})`

### Business Logic Isolation
`core/engine.py` (`SmartCartEngine`) contains ALL business logic:
- **Debouncing**: Prevents duplicate product additions within configurable time window (see `_is_new_product_detection()`)
- **State management**: Tracks last obstacle danger level to avoid redundant UI alarms
- **DB operations**: Coordinates DAOs for product lookup, cart management, logging
- Never put business logic in network handlers - they only route to/from the engine

### Configuration Management
`src/common/config.py` loads ALL YAML configs from `configs/` using Pydantic for type-safe access:
```python
from common.config import config
ai_ip = config.network.pc1_ai.ip
model_path = config.models.obstacle_detector.weights
```
- Environment variables in `.env` (DB credentials) loaded via `python-dotenv`
- Network IPs use `127.0.0.1` for local testing, update `configs/network_config.yaml` for multi-PC deployment

### Database Layer
Three DAO classes (`database/*_dao.py`) wrap `DBHandler` (PyMySQL):
- `ProductDAO`: Product catalog queries
- `TransactionDAO`: Sessions, cart items, checkout
- `ObstacleLogDAO`: Obstacle detection logging
- All DAOs return dictionaries, use manual transaction control via `db_handler.begin()/commit()/rollback()`
- DB schema in `scripts/init_db.sql`, seed data via `python scripts/seed_data.py`

### Threading Model
All network I/O uses separate threads:
- `ai_server.py`: 4 threads (2 UDP receivers, 2 inference loops)
- `main_hub.py`: 6+ threads (2 UDP receivers, 2 UDP forwarders, 2 TCP servers)
- Thread-safe frame buffers use `threading.Lock()` for shared access (see `AIServer._obstacle_lock`)

## Development Workflows

### Running the System
**Single PC test** (recommended for development):
```bash
python test/run_hybrid_test.py  # Starts all 4 components automatically
```

**Multi-PC deployment** (start in order):
```bash
# PC1 (AI Server)
python src/ai_server.py

# PC2 (Main Hub)  
python src/main_hub.py

# PC3 (UI + Camera - separate terminals)
python src/cart_ui_app.py
python src/cart_camera_app.py
```

### Testing Without Hardware
- **No cameras**: Use `test/optimized_hybrid_camera.py` (video file + webcam fallback)
- **UI testing**: `test/test_ui_update.py` sends mock UPDATE_CART commands to UI
- All network configs use localhost by default for single-PC testing

### Debugging
- Logs: `logs/system.log` (all components), or `test_*.log` files for test runs
- UDP frame flow: Check console output for "Received N frames, latest size: X bytes"
- Protocol issues: Verify JSON structure matches `protocols.py` enums exactly

## Project-Specific Conventions

### YOLO Model Integration
- Models in `models/obstacle_detector/` and `models/product_recognizer/`
- Wrapped in `detectors/obstacle_dl.py` and `detectors/product_dl.py` (ultralytics v8+)
- `ObstacleDetector.detect()` returns `{"danger_level": int, "objects": list}`
- `ProductRecognizer.recognize()` returns `product_id` (maps to DB primary key)

### UI Updates (Main Hub → PyQt6 Dashboard)
UI controller uses **Qt signals for thread-safe updates**:
```python
# In ui_controller.py
self.update_cart_signal.emit(cart_items)  # Never update UI widgets from TCP thread
```
Always emit signals, never call dashboard methods directly from network threads.

### Error Handling
- Network operations: TCP client includes retry/timeout logic
- DB operations: DAOs log errors but don't raise - check return values
- YOLO inference: Catch exceptions in inference loops to prevent thread crashes

## Key Files for Understanding

- [src/common/protocols.py](src/common/protocols.py) - Complete message protocol spec + enums
- [src/core/engine.py](src/core/engine.py) - All business logic in one place
- [PROJECT_STRUCTURE.md](PROJECT_STRUCTURE.md) - Detailed component documentation
- [docs/QUICK_START_GUIDE.md](docs/QUICK_START_GUIDE.md) - Setup steps + configuration examples
- [configs/network_config.yaml](configs/network_config.yaml) - Network topology reference

## Common Pitfalls

1. **Protocol mismatches**: Always use enum values from `protocols.py`, never hardcode integers/strings
2. **Thread safety**: Use Qt signals for UI updates, locks for shared frame buffers
3. **Port conflicts**: Check `network_config.yaml` if components can't connect
4. **Model paths**: Ensure `.pt` files exist in `models/` before running AI server
5. **DB connection**: Create `.env` from `.env.example` and run `scripts/init_db.sql` first

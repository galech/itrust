# Datetime Event Store

**Datetime Event Store** is a modular library that provides a consistent API to store and retrieve events ordered by datetime, with efficient pagination and support for updates.

It includes **three implementations** with the same interface:

- ✅ In-memory (for testing and lightweight scenarios)
- ⚡ Redis (for high-speed use cases)
- 🧱 MongoDB (for persistent and scalable storage)

---

## ✨ Features

- Store events with an associated timestamp and string payload
- All datetimes are stored and returned in UTC
    - If a datetime without timezone is provided, it is assumed to be in local time and automatically converted to UTC
- Query events in chronological order with cursor-based pagination
- Update or delete events by ID
- Filter by start and end datetimes
- Optional support for clearing all events (e.g., in testing)

---

## 🛠️ Engines Overview

The `DatetimeEventStore` interface is implemented with three different storage engines. Each one is designed for specific use cases and has different trade-offs.

---

### ✅ In-Memory Engine

**Class**: `DatetimeEventStore`

**Module**: `datetime_event_store.store`

#### 🔧 Description

This is a lightweight, fully in-memory implementation using Python dictionaries and `SortedDict`. It’s perfect for unit testing, experimentation, or applications where persistence is not needed.

#### 📦 Characteristics

- Fastest setup (no external dependencies)
- Fully synchronous
- Events stored in a `SortedDict` ordered by `(timestamp, id)`
- Data is lost when the process ends

#### ✅ Ideal for

- Unit and integration tests
- Prototyping
- Temporary or short-lived environments

#### ⚠️ Limitations

- Not persistent
- Not suitable for concurrent access across processes

---

### ⚡ Redis Engine

**Class**: `RedisDatetimeEventStore`

**Module**: `datetime_event_store.store`

#### 🔧 Description

This engine uses Redis to store events and their ordering. It leverages Redis Sorted Sets to maintain a globally ordered timeline of events and Redis Hashes to store the payloads.

#### 📦 Characteristics

- Fast read/write performance
- Stores `(timestamp + id)` as a float score for sorting
- Payloads stored as JSON strings in a Redis hash
- Synchronous implementation

#### ✅ Ideal for

- Real-time systems
- Low-latency applications
- Scenarios with ephemeral data or replicated Redis setups

#### ⚠️ Limitations

    # We intentionally discard microseconds from the datetime to reserve the
    # decimal part of the float score in the Redis ZSET.
    # This allows us to encode a unique event identifier (e.g., event_id * 1e-6)
    # into the score, ensuring total ordering even for events with the same second.
    # As a trade-off, microsecond precision is lost.

    # In this implementation, we encode the event ID as a fractional part of the Redis ZSET score
    # using `score = int(dt.timestamp()) + event_id * 1e-6`.
    # This limits the number of events we can generate to 999,999,
    # since only 6 decimal digits are available in the fractional part.
    # Note: this limit applies to the total number of events created (not concurrently),
    # and assumes event_id is an increasing integer less than 1,000,000.

- Requires running Redis server
- No built-in persistence beyond Redis snapshotting or AOF

---

### 🧱 MongoDB Engine (Async)

**Class**: `MongoDBDatetimeEventStore`

**Module**: `datetime_event_store.store`

#### 🔧 Description

This engine uses MongoDB for persistent, durable storage. It stores each event as a MongoDB document and uses compound sorting on `(timestamp, ObjectId)` for pagination.

#### 📦 Characteristics

- Fully persistent
- Supports horizontal scaling with MongoDB clusters
- Uses Motor (async driver)
- Stores full event structure in BSON documents
- Cursor-safe pagination using timestamp + ObjectId

#### ✅ Ideal for

- Applications requiring long-term storage
- Analytics or reporting systems
- Scalable systems using FastAPI or other async frameworks

#### ⚠️ Limitations

    # Note: MongoDB only supports datetime precision up to milliseconds.
    # Any microseconds in the datetime will be truncated or rounded when stored.
    # It's recommended to normalize timestamps to milliseconds before saving,
    # to avoid subtle inconsistencies.

- Requires async/await support
- Needs a running MongoDB instance
- Slightly slower due to network/database latency



# 🚀 FastAPI Application

This project includes a ready-to-use [FastAPI](https://fastapi.tiangolo.com/) backend exposing a RESTful API to interact with the `DatetimeEventStore`. It supports all available engines (MongoDB, Redis, and in-memory), and allows flexible configuration through environment variables.

---

### 🌐 API Features

- `POST /events/` → Create a new event
- `PUT /events/{event_id}` → Update an event
- `GET /events/{event_id}` → Get a single event by ID
- `GET /events/` → List events (with optional pagination, filtering, and sorting)
- `DELETE /events/{event_id}` → Delete an event

All endpoints support async and are compatible with any of the three engines.

---

### ⚙️ Configuration via Environment Variables

| Variable         | Default  | Description                                                                 |
|------------------|----------|-----------------------------------------------------------------------------|
| `ENGINE`         | `mongo`  | Select the backend: `mongo`, `redis`, or `memory`                          |
| `CLEAR_STORE`    | `false`  | If `true`, clears the event store on startup                               |
| `GEN_TEST_DATA`  | `false`  | If `true`, generates synthetic test data on startup                        |

Example usage:

```bash
ENGINE=redis CLEAR_STORE=true GEN_TEST_DATA=true uvicorn api:app --reload
```


# 🖥️ Frontend Application (React)

This project includes a basic frontend built with **React**, designed to demonstrate CRUD operations against the FastAPI backend.

---

### 📋 Features

- 🔍 **List events** using a virtualized table with lazy loading
- ➕ **Create** new events
- ✏️ **Edit** existing events
- ❌ **Delete** events
- 📦 **Pagination** is implemented using **cursor-based pagination**, allowing efficient navigation through large datasets without performance degradation

---

### 🔄 Lazy-Loaded Virtual Table

The events are displayed in a virtual scrolling table that dynamically loads more data as the user scrolls. This is powered by the backend's cursor-based pagination and avoids fetching or rendering all records at once.

**Benefits:**
- ⚡ Fast rendering for large datasets
- 🚀 Low memory usage
- 📜 Smooth user experience when scrolling

---

### ⚙️ Backend Integration

The frontend interacts with the FastAPI backend via HTTP requests to perform all operations. It expects the backend to be available at:

```bash
http://localhost:8000
```

# 🛠️ Setup

### 🔥 Backend Setup

1. (Optional) **Start Redis and MongoDB containers** (or use your existing instances):
   - Run Redis:
     ```bash
     docker run --name redis -p 6379:6379 -d redis
     ```
   - Run MongoDB:
     ```bash
     docker run --name some-mongo -p 27017:27017 -d mongo
     ```

2. **Create and activate a virtual environment**:
   - Create the virtual environment:
     ```bash
     python3 -m venv venv
     ```
   - Activate the virtual environment:
     - On Windows:
       ```bash
       venv\Scripts\activate
       ```
     - On macOS/Linux:
       ```bash
       source venv/bin/activate
       ```

3. **Install required Python dependencies**:
   - Run the following to install the dependencies:
     ```bash
     pip install -r requirements.txt
     ```

4. **Set environment variables**:
   - Set the `ENGINE`, `GEN_TEST_DATA`, and `CLEAR_STORE` environment variables. For example, to use MongoDB and generate test data:
     ```bash
     export ENGINE=mongo (mongo, redis, or memory) 
     export GEN_TEST_DATA=true
     export CLEAR_STORE=true
     ```

5. **Run the FastAPI server**:
   - Start the FastAPI backend:
     ```bash
     uvicorn main:app --reload
     ```

---

### 🖥️ Frontend Setup (React)

1. **Navigate to the frontend directory**:
   - After setting up the backend, navigate to the `frontend` directory:
     ```bash
     cd frontend/
     ```

2. **Install the frontend dependencies**:
   - Install the required packages:
     ```bash
     npm install
     ```

3. **Start the React development server**:
   - Start the React app:
     ```bash
     npm start
     ```

---
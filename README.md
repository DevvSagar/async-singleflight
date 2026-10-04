<div align="center">

# ⚡ async-singleflight

**Production-grade request coalescing & anti-cache-stampede engine for Python asyncio and FastAPI.**

[![Python](https://img.shields.io/badge/Python-3.11+-3776AB?style=for-the-badge&logo=python&logoColor=white)](https://python.org)
[![FastAPI](https://img.shields.io/badge/FastAPI-05998B?style=for-the-badge&logo=fastapi&logoColor=white)](https://fastapi.tiangolo.com)
[![PostgreSQL](https://img.shields.io/badge/PostgreSQL-4169E1?style=for-the-badge&logo=postgresql&logoColor=white)](https://www.postgresql.org/)
[![Docker](https://img.shields.io/badge/Docker-2496ED?style=for-the-badge&logo=docker&logoColor=white)](https://www.docker.com/)
[![License: Apache 2.0](https://img.shields.io/badge/License-Apache_2.0-D22128?style=for-the-badge)](LICENSE)

</div>

---

## 🎯 The Problem

- **The Thundering Herd**: When a hot cache key expires, thousands of requests arrive at the same millisecond.
- **Database Starvation**: All concurrent requests simultaneously fire duplicate heavy queries at PostgreSQL.
- **Cascading Outages**: Database connection pools exhaust immediately, triggering HTTP 500 & 504 gateway timeouts.
- **Wasted Cloud Spend**: Repeating identical expensive calculations thousands of times concurrently wastes compute.

---

## 💡 The Solution

- **Leader Election**: Only **1** request executes the downstream database query.
- **In-Memory Holding**: The other 999 requests wait non-blockingly on an in-memory ticket (`Future`).
- **Multicast Fanout**: Once the leader finishes, the exact result is handed to all waiting callers simultaneously.
- **99.9% Load Reduction**: Turns 1,000 database hits into **1** single query.

---

## 📍 Where It Solves It

- **Flash Sales & E-Commerce**: Heavy traffic spikes on product detail & inventory checks.
- **Trending Feeds & Leaderboards**: High-volume reads on identical ranking calculations.
- **Financial & Crypto Dashboards**: Repetitive queries aggregating market tick data.
- **AI & 3rd-Party APIs**: Prevents duplicate concurrent calls to paid external services.

---

## 🛠️ Tech Stack

| Layer | Technology | Role |
| :--- | :--- | :--- |
| **Concurrency Core** | `Python 3.11+` · `asyncio` | Event-loop request coalescing & cancellation shielding |
| **Web & Routing** | `FastAPI` · `Starlette` | ASGI middleware interception & decorator interface |
| **Data Layer** | `PostgreSQL` · `asyncpg` | Target database & connection pool saturation testing |
| **Testing** | `pytest` · `pytest-asyncio` | Concurrency race condition & error-propagation tests |
| **Benchmarking** | `Locust` · `HTTPX` | Flash-crowd load simulation (1,000+ virtual users) |
| **DevOps** | `Docker Compose` | 1-command reproducible demo environment |

---

## 🚀 How To Use It

- **1. Function Decorator**: Add a protection tag on any slow database query or service method.
- **2. ASGI Middleware**: Plug into FastAPI to auto-deduplicate incoming HTTP GET requests at the route level.
- **3. Direct Coordinator**: Use the low-level coordinator inside background workers and task queues.

---

## 📄 License

Licensed under the [Apache License 2.0](LICENSE).
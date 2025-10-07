# Problem Description

- You will get URLs from 2 different public APIs which will deliver some public hourly and daily data in JSON formats of their own, where we are interested only in a few of parameters
- You will create an API of your own, which would provide this data to clients, who can chose the source and returns a few parameters our clients are interested in
- you will display them in one local page, without any special design requirement
- you might want to provide clients with some aggregates of data, since some of the parameters are numbers
- Details about APIs will be provided

# Expected Results

- use modern and efficient approaches, concepts and patterns
- think about both: simplicity and scalability in more meanings than one
- think about quality of the code and its expandability
- think about efficiency, resources and costs

# Preparations and Tools

- have a local environment for running a single WEB page ready on your laptop
- have access to internet
- use any of the following languages: Golang, Java, Python
- use any kind of tools you want to
- you can prepare all scaffolding for the project you want to and build on top of it

---

### **Key Drivers**

- **Extensibility:** Easy to add new data sources/views.
- **Scalability:** Handle more data sources, traffic, and clients.
- **Maintainability:** Easy to debug, fix, and enhance.
- **Performance:** Low-latency API reads.
- **Ops Efficiency:** Simple to deploy, monitor; low infrastructure cost.

---

### **Architectures**

#### **I: Monolith**

- **Concept:** Single FastAPI app does everything.
- **Flow:** `Scheduler -> Data Fetcher -> PostgreSQL (JSONB) -> API/View Layer (Jinja2)`.
- **Analysis:**
  - **Pros:** **Very Fast** dev speed. **Very Simple** ops.
  - **Cons:** **Low** scalability (single point of failure). **Low** extensibility (tight coupling).

#### **II: Normal App**

- **Concept:** Decoupled Backend API and Frontend SPA.
- **Flow:**
  - **Backend (FastAPI):** Handles data fetching/storage. Exposes a JSON API only.
  - **Frontend (React):** Standalone SPA. Consumes the backend API. Built and served by Nginx.
  - **Proxy (Nginx):** Serves static frontend files, routes `/api/*` to the backend.
- **Analysis:**
  - **Pros:** **High** dev speed (parallel work). **Good** scalability (frontend/backend scale independently). **High** extensibility (clean API contract).
  - **Cons:** Slightly more setup than a monolith.

#### **III: Microservices**

- **Concept:** Decomposed into small, single-responsibility services.
- **Flow:** `Ingestion Service(s) -> Central DB -> Backend API Service -> Frontend`.
- **Analysis:**
  - **Pros:** **Excellent** scalability & extensibility (scale/add services independently).
  - **Cons:** **High** ops complexity (deployment, monitoring, service discovery). Slower initial dev.

#### **IV: CQRS Pattern**

- **Concept:** Separate read/write paths for max performance. Event-driven.
- **Flow:**
  - **Write:** `Command -> Message Bus -> Handler -> Write DB` (publishes `Event`).
  - **Read:** `Event -> Projector -> Read DB` (creates pre-calculated views).
  - **API:** Queries the optimized Read DB.
- **Analysis:**
  - **Pros:** **Exceptional** performance & scalability. **Exceptional** extensibility (add new views via projectors).
  - **Cons:** **Very High** complexity (dev & ops). Requires deep distributed systems knowledge.

---

### **Comparison Matrix**

| Driver              | I: Monolith | II: Normal | III: Microservices | IV: CQRS          |
| :------------------ | :---------- | :------------------------- | :----------------- | :---------------- |
| **Dev Velocity**    | Very High   | High                       | Medium             | Low               |
| **Scalability**     | Low         | Good                       | Excellent          | Exceptional       |
| **Extensibility**   | Low         | High                       | Excellent          | Exceptional       |
| **Maintainability** | Low         | High                       | Medium             | High (if skilled) |
| **Performance**     | Medium      | Medium                     | High               | Exceptional       |
| **Ops Complexity**  | Very Low    | Low                        | High               | Very High         |


# Data Aggregator - Architecture II: Normal App

A **generic, extensible data aggregation system** that fetches data from multiple public APIs and provides a unified interface with automatic aggregations. Built using modern technologies with a focus on simplicity, scalability, and maintainability.

## 🎯 Architecture

This implementation follows **Architecture II: Normal App** - a decoupled backend API and frontend SPA architecture.

```
┌─────────────────────────────────────────────────────┐
│  Frontend (React + Vite)                            │
│  - Generic UI components                            │
│  - TanStack Query for data fetching                 │
│  - Tailwind CSS for styling                         │
└──────────────────┬──────────────────────────────────┘
                   │ HTTP/JSON
┌──────────────────┴──────────────────────────────────┐
│  Nginx (Reverse Proxy)                              │
│  - Serves static frontend                           │
│  - Proxies /api/* to backend                        │
└──────────────────┬──────────────────────────────────┘
                   │
┌──────────────────┴──────────────────────────────────┐
│  Backend (FastAPI)                                  │
│  ┌─────────────────────────────────────────────┐    │
│  │ Generic Adapter System                      │    │
│  │ - DataSourceAdapter (ABC)                   │    │
│  │ - OpenMeteoAdapter                          │    │
│  │ - Easy to add new sources                   │    │
│  └─────────────────────────────────────────────┘    │
│  ┌─────────────────────────────────────────────┐    │
│  │ Generic Aggregator                          │    │
│  │ - Calculates stats for any numeric fields   │    │
│  │ - avg, min, max, sum, count                 │    │
│  └─────────────────────────────────────────────┘    │
│  ┌─────────────────────────────────────────────┐    │
│  │ Scheduler (APScheduler)                     │    │
│  │ - Fetches data on intervals                 │    │
│  │ - Configurable per source                   │    │
│  └─────────────────────────────────────────────┘    │
│  ┌─────────────────────────────────────────────┐    │
│  │ REST API                                    │    │
│  │ - GET /api/sources                          │    │
│  │ - GET /api/data/{source}                    │    │
│  │ - POST /api/fetch/{source}                  │    │
│  └─────────────────────────────────────────────┘    │
└──────────────────┬──────────────────────────────────┘
                   │
┌──────────────────┴──────────────────────────────────┐
│  PostgreSQL 16                                      │
│  - sources table (metadata)                         │
│  - data_points table (JSONB for flexibility)        │
└─────────────────────────────────────────────────────┘
```

## ✨ Key Features

### Generic Design
- **No hardcoded field names** - works with any data structure
- **Configuration-driven** - add new sources without code changes
- **Auto-detecting aggregations** - automatically finds numeric fields
- **Dynamic UI** - table columns adapt to data structure

### Extensibility
Adding a new data source requires:
1. Create a new adapter class (50 lines of code)
2. Add configuration entry
3. Done! No changes to core logic, database, API, or frontend

### Current Data Sources
- **OpenMeteo** - Weather data (temperature, precipitation, wind speed)

## 🛠️ Technology Stack

### Backend
- **FastAPI 0.115+** - Modern Python web framework
- **SQLAlchemy 2.0+** - ORM with async support
- **PostgreSQL 16** - Reliable relational database
- **APScheduler 3.10+** - Background task scheduling
- **httpx 0.27+** - Async HTTP client
- **Pydantic 2.9+** - Data validation

### Frontend
- **React 19** - UI framework
- **Vite 7** - Build tool
- **TanStack Query 5** - Data fetching & caching
- **Axios 1.7+** - HTTP client
- **Tailwind CSS 4** - Utility-first CSS

### DevOps
- **Docker & Docker Compose** - Containerization
- **Nginx 1.27** - Reverse proxy & static file serving

## 🚀 Quick Start

### Prerequisites
- Docker and Docker Compose
- Git

### Installation

1. **Clone the repository**
```bash
git clone https://github.com/szeplakig/data_aggregator.git
cd data_aggregator
```

2. **Start all services**
```bash
docker-compose up -d
```

This will:
- Start PostgreSQL database
- Build and run the backend API
- Build and serve the frontend
- Initialize the database
- Start fetching data from configured sources

3. **Access the application**
- **Frontend**: http://localhost
- **API Documentation**: http://localhost:8000/docs
- **API Endpoints**: http://localhost:8000/api

### Development Mode

**Backend development:**
```bash
cd backend
pip install -e .
uvicorn app.main:app --reload
```

**Frontend development:**
```bash
cd frontend
npm install
npm run dev
```

## 📡 API Endpoints

### `GET /api/sources`
List all configured data sources.

**Response:**
```json
[
  {
    "id": 1,
    "name": "openmeteo",
    "type": "hourly",
    "description": "Open-Meteo Weather API",
    "enabled": true,
    "created_at": "2025-10-04T10:00:00Z"
  }
]
```

### `GET /api/data/{source}`
Get data from a specific source with automatic aggregations.

**Query Parameters:**
- `limit` - Max records to return (default: 100, max: 10000)
- `offset` - Pagination offset (default: 0)
- `hours` - Filter to last N hours (optional)

**Response:**
```json
{
  "source": "openmeteo",
  "type": "hourly",
  "data": [
    {
      "timestamp": "2025-10-04T14:00:00Z",
      "temperature": 22.5,
      "precipitation": 0.0,
      "wind_speed": 12.3
    }
  ],
  "aggregates": {
    "temperature": {
      "avg": 21.3,
      "min": 18.2,
      "max": 24.7,
      "sum": 511.2,
      "count": 24
    }
  },
  "period": {
    "from": "2025-10-03T14:00:00Z",
    "to": "2025-10-04T14:00:00Z"
  },
  "total_count": 168,
  "returned_count": 24
}
```

### `POST /api/fetch/{source}`
Manually trigger immediate data fetch for a specific source.

### `POST /api/fetch-all`
Manually trigger data fetch for all sources.

## 🔧 Adding a New Data Source

### Step 1: Create an Adapter

Create `backend/app/adapters/myapi.py`:

```python
from datetime import datetime, timezone
from typing import Any
import httpx
from app.adapters import DataSourceAdapter

class MyAPIAdapter(DataSourceAdapter):
    """Adapter for My Custom API."""

    async def fetch_data(self) -> list[dict[str, Any]]:
        """Fetch data from the API."""
        base_url = self.config["base_url"]
        
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.get(base_url)
            response.raise_for_status()
            data = response.json()
        
        # Transform to common format
        data_points = []
        for item in data:
            point = {
                "timestamp": datetime.now(timezone.utc),
                "value1": item["field1"],
                "value2": item["field2"],
            }
            data_points.append(point)
        
        return data_points

    def get_source_name(self) -> str:
        return "myapi"

    def get_data_type(self) -> str:
        return "hourly"

    def get_numeric_fields(self) -> list[str]:
        return ["value1", "value2"]
```

### Step 2: Register the Adapter

In `backend/app/adapters/factory.py`:

```python
from app.adapters.myapi import MyAPIAdapter

ADAPTER_REGISTRY: dict[str, Type[DataSourceAdapter]] = {
    "OpenMeteoAdapter": OpenMeteoAdapter,
    "MyAPIAdapter": MyAPIAdapter,  # Add this
}
```

### Step 3: Add Configuration

In `backend/app/config.py`:

```python
DATA_SOURCES_CONFIG: list[dict[str, Any]] = [
    # ... existing sources ...
    {
        "name": "myapi",
        "type": "hourly",
        "description": "My Custom API",
        "adapter_class": "MyAPIAdapter",
        "fetch_interval_minutes": 60,
        "enabled": True,
        "config": {
            "base_url": "https://api.example.com/data",
            "numeric_fields": ["value1", "value2"]
        }
    }
]
```

### Step 4: Restart

```bash
docker-compose restart backend
```

That's it! Your new source will automatically:
- Appear in the frontend source selector
- Fetch data on the specified interval
- Calculate aggregates for numeric fields
- Display in the generic data table

## 🏗️ Project Structure

```
data_aggregator/
├── backend/
│   ├── app/
│   │   ├── __init__.py
│   │   ├── main.py              # FastAPI application
│   │   ├── config.py            # Configuration & source registry
│   │   ├── database.py          # Database connection
│   │   ├── models.py            # SQLAlchemy models
│   │   ├── repository.py        # Generic data repository
│   │   ├── schemas.py           # Pydantic schemas
│   │   ├── aggregator.py        # Generic aggregator
│   │   ├── scheduler.py         # Task scheduler
│   │   ├── api.py               # API endpoints
│   │   └── adapters/
│   │       ├── __init__.py      # DataSourceAdapter interface
│   │       ├── factory.py       # Adapter factory
│   │       └── openmeteo.py     # OpenMeteo adapter
│   ├── pyproject.toml
│   └── Dockerfile
├── frontend/
│   ├── src/
│   │   ├── api/
│   │   │   └── client.ts        # API client
│   │   ├── components/
│   │   │   ├── SourceSelector.tsx
│   │   │   ├── DataTable.tsx
│   │   │   └── AggregatesPanel.tsx
│   │   ├── types/
│   │   │   └── api.ts           # TypeScript types
│   │   ├── App.tsx              # Main application
│   │   └── main.tsx
│   ├── nginx.conf               # Nginx configuration
│   ├── package.json
│   └── Dockerfile
├── docker-compose.yml
└── README.md
```

## 🎨 Design Patterns Used

1. **Adapter Pattern** - Each data source has an adapter implementing a common interface
2. **Repository Pattern** - Abstract database operations from business logic
3. **Factory Pattern** - Create adapters dynamically based on configuration
4. **Strategy Pattern** - Different aggregation strategies for different data types

## 📊 Database Schema

### `sources` Table
Stores metadata about data sources.

| Column      | Type        | Description         |
|-------------|-------------|---------------------|
| id          | INTEGER     | Primary key         |
| name        | VARCHAR(50) | Unique source name  |
| type        | VARCHAR(20) | 'hourly' or 'daily' |
| description | TEXT        | Source description  |
| enabled     | BOOLEAN     | Is source active    |
| created_at  | TIMESTAMP   | Creation time       |

### `data_points` Table
Stores actual data in JSONB format for maximum flexibility.

| Column | Type | Description |
|--------|------|-------------|
| id | INTEGER | Primary key |
| source_id | INTEGER | Foreign key to sources |
| timestamp | TIMESTAMP | Data point timestamp |
| data | JSONB | Arbitrary JSON data |
| created_at | TIMESTAMP | Record creation time |

**Indexes:**
- `idx_source_timestamp` on (source_id, timestamp) for fast queries

## 🔍 Key Design Decisions

### Why JSONB for data storage?
- **Flexibility**: Each data source can have different fields
- **No schema migrations** when adding new sources
- **PostgreSQL JSONB is fast** with proper indexing
- **Easy aggregations** with PostgreSQL's JSON functions

### Why configuration-driven adapters?
- **No code changes** to add new sources
- **Easy to enable/disable** sources
- **Centralized configuration** in one place
- **Testable** - mock configs for testing

### Why calculate aggregates on-the-fly?
- **Always accurate** - matches filtered data
- **Simple implementation** - no cache invalidation
- **Flexible** - different aggregations for different queries
- **Good performance** - calculations are fast

## 🚦 Testing

Run tests:
```bash
cd backend
pytest
```

## 📈 Performance Considerations

- **Database indexing** on (source_id, timestamp) for fast queries
- **Connection pooling** (10 connections, 20 overflow)
- **Pagination** to limit response sizes
- **Query optimization** with SQLAlchemy
- **Frontend caching** with TanStack Query

## 🔐 Security

- CORS configuration for allowed origins
- Input validation with Pydantic
- SQL injection protection with ORM
- Nginx security headers
- Environment variable configuration

## 📝 Future Enhancements

- [ ] WebSocket support for real-time updates
- [ ] Authentication and API keys
- [ ] Data retention policies
- [ ] Export to CSV/JSON
- [ ] Charting with Recharts
- [ ] More data sources (weather, stocks, etc.)
- [ ] Alerting system
- [ ] Admin dashboard

## 📄 License

MIT

## 👤 Author

Gergely Széplaki (szeplakig91@gmail.com)

---

## 🎓 Architecture Comparison

This implementation demonstrates **Architecture II: Normal App** which provides:

| Aspect | Rating | Notes |
|--------|--------|-------|
| **Dev Velocity** | ⭐⭐⭐⭐ | Fast development, clear separation |
| **Scalability** | ⭐⭐⭐⭐ | Frontend/backend scale independently |
| **Extensibility** | ⭐⭐⭐⭐⭐ | Adding sources is trivial |
| **Maintainability** | ⭐⭐⭐⭐⭐ | Clean code, well-organized |
| **Performance** | ⭐⭐⭐ | Good for most use cases |
| **Ops Complexity** | ⭐⭐ | Simple Docker setup |

**Perfect for:** Medium-sized applications that need to scale, teams wanting parallel frontend/backend development, projects requiring frequent additions of new features/sources.

# Fulfillment Ticket System - API Documentation

## Base URL
```
http://localhost:8000
```

## API Endpoints

### Health & Info

#### GET `/`
Root endpoint with API information.

**Response:**
```json
{
  "message": "Fulfillment Ticket System API",
  "version": "1.0.0",
  "status": "operational",
  "endpoints": {
    "marketplaces": "/api/marketplaces",
    "categories": "/api/categories",
    "folders": "/api/folders",
    "tickets": "/api/tickets",
    "labels": "/api/labels"
  }
}
```

#### GET `/health`
Health check endpoint.

**Response:**
```json
{
  "status": "healthy",
  "timestamp": "2024-01-15T10:30:00Z"
}
```

### Marketplaces

#### GET `/api/marketplaces`
Get all marketplaces.

**Response:**
```json
[
  {
    "id": 1,
    "name": "Amazon",
    "code": "AMZN",
    "description": "Amazon marketplace",
    "is_active": true
  }
]
```

#### GET `/api/marketplaces/{marketplace_id}`
Get a specific marketplace by ID.

**Response:**
```json
{
  "id": 1,
  "name": "Amazon",
  "code": "AMZN",
  "description": "Amazon marketplace",
  "is_active": true
}
```

### Categories

#### GET `/api/categories`
Get all categories.

**Query Parameters:**
- `marketplace_id` (optional): Filter by marketplace

**Response:**
```json
[
  {
    "id": 1,
    "marketplace_id": 1,
    "name": "Orders",
    "code": "ORD",
    "description": "Order-related tickets",
    "is_active": true,
    "display_order": 1
  }
]
```

#### GET `/api/categories/{category_id}`
Get a specific category by ID.

### Folders

#### GET `/api/folders`
Get all folders.

**Query Parameters:**
- `category_id` (optional): Filter by category
- `parent_id` (optional): Filter by parent folder

**Response:**
```json
[
  {
    "id": 1,
    "category_id": 1,
    "parent_id": null,
    "name": "Pending Orders",
    "path": "/Pending Orders",
    "description": "Orders awaiting processing",
    "is_active": true,
    "display_order": 1
  }
]
```

#### GET `/api/folders/{folder_id}`
Get a specific folder by ID.

### Tickets

#### GET `/api/tickets`
Get all tickets with summary information.

**Query Parameters:**
- `folder_id` (optional): Filter by folder
- `status` (optional): Filter by status
- `limit` (optional): Maximum results (default: 100, max: 1000)

**Response:**
```json
[
  {
    "id": 1,
    "ticket_number": "TKT-2024-001",
    "subject": "Order not received",
    "from_address": "customer@example.com",
    "status": "new",
    "fulfillment_state": "processing",
    "priority": 2,
    "created_at": "2024-01-15T10:30:00",
    "folder_id": 1,
    "labels": ["urgent", "order-issue"]
  }
]
```

#### GET `/api/tickets/{ticket_id}`
Get detailed information about a specific ticket.

**Response:**
```json
{
  "id": 1,
  "ticket_number": "TKT-2024-001",
  "subject": "Order not received",
  "from_address": "customer@example.com",
  "from_name": "John Doe",
  "body_text": "I haven't received my order #12345 yet.",
  "status": "new",
  "fulfillment_state": "processing",
  "priority": 2,
  "created_at": "2024-01-15T10:30:00",
  "updated_at": "2024-01-15T10:30:00",
  "folder_id": 1,
  "assigned_to_id": null,
  "labels": ["urgent"],
  "claims": [],
  "actions": [
    {
      "id": 1,
      "ticket_id": 1,
      "action_type": "created",
      "description": "Ticket created",
      "created_at": "2024-01-15T10:30:00",
      "user_id": null
    }
  ]
}
```

### Labels

#### GET `/api/labels`
Get all labels.

**Response:**
```json
[
  {
    "id": 1,
    "name": "urgent",
    "color": "#FF0000",
    "description": "Urgent tickets"
  }
]
```

### Claims

#### GET `/api/claims`
Get all claims.

**Query Parameters:**
- `ticket_id` (optional): Filter by ticket

**Response:**
```json
[
  {
    "id": 1,
    "ticket_id": 2,
    "claim_number": "CLM-001",
    "claim_type": "damaged_item",
    "status": "investigating",
    "description": "Item damaged in transit",
    "claim_amount": 49.99,
    "created_at": "2024-01-16T15:00:00"
  }
]
```

### Actions

#### GET `/api/actions`
Get all actions/audit logs.

**Query Parameters:**
- `ticket_id` (optional): Filter by ticket

**Response:**
```json
[
  {
    "id": 1,
    "ticket_id": 1,
    "action_type": "created",
    "description": "Ticket created",
    "created_at": "2024-01-15T10:30:00",
    "user_id": null
  }
]
```

## Status Codes

- `200 OK` - Successful request
- `404 Not Found` - Resource not found
- `500 Internal Server Error` - Server error

## CORS

The API includes CORS middleware configured to allow:
- Origins: `http://localhost:3000`, `http://localhost:5173` (React dev servers)
- All HTTP methods
- All headers
- Credentials

## Error Handling

All errors return JSON with a detail message:
```json
{
  "detail": "Error message here"
}
```

## Mock Data

**Note:** The current API implementation uses mock data for demonstration purposes. 
In a production environment, these endpoints would be connected to the PostgreSQL 
database using SQLAlchemy ORM models.

## Running the API

```bash
# Start the API server
cd api
python main.py

# Or use uvicorn directly
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

The API will be available at `http://localhost:8000` with interactive documentation at:
- Swagger UI: `http://localhost:8000/docs`
- ReDoc: `http://localhost:8000/redoc`

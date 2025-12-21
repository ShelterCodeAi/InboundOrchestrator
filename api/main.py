"""
FastAPI application for the fulfillment ticket system.

This API provides endpoints to manage tickets, folders, categories, marketplaces,
claims, and other related entities for the fulfillment ticket operational system.
"""
import os
from typing import List, Optional
from datetime import datetime

from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

# Initialize FastAPI app
app = FastAPI(
    title="Fulfillment Ticket System API",
    description="API for managing fulfillment tickets, claims, and related entities",
    version="1.0.0"
)

# Configure CORS to allow React UI to connect
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://localhost:5173"],  # React dev servers
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Pydantic models for API responses
class MarketplaceResponse(BaseModel):
    id: int
    name: str
    code: str
    description: Optional[str] = None
    is_active: bool


class CategoryResponse(BaseModel):
    id: int
    marketplace_id: int
    name: str
    code: str
    description: Optional[str] = None
    is_active: bool
    display_order: int


class FolderResponse(BaseModel):
    id: int
    category_id: int
    parent_id: Optional[int] = None
    name: str
    path: Optional[str] = None
    description: Optional[str] = None
    is_active: bool
    display_order: int


class LabelResponse(BaseModel):
    id: int
    name: str
    color: Optional[str] = None
    description: Optional[str] = None


class TicketSummaryResponse(BaseModel):
    id: int
    ticket_number: str
    subject: str
    from_address: str
    status: str
    fulfillment_state: str
    priority: int
    created_at: datetime
    folder_id: int
    labels: List[str] = []


class TicketDetailResponse(BaseModel):
    id: int
    ticket_number: str
    subject: str
    from_address: str
    from_name: Optional[str] = None
    body_text: Optional[str] = None
    status: str
    fulfillment_state: str
    priority: int
    created_at: datetime
    updated_at: datetime
    folder_id: int
    assigned_to_id: Optional[int] = None
    labels: List[str] = []
    claims: List[dict] = []
    actions: List[dict] = []


class ClaimResponse(BaseModel):
    id: int
    ticket_id: int
    claim_number: str
    claim_type: str
    status: str
    description: Optional[str] = None
    claim_amount: Optional[float] = None
    created_at: datetime


class ActionResponse(BaseModel):
    id: int
    ticket_id: int
    action_type: str
    description: Optional[str] = None
    created_at: datetime
    user_id: Optional[int] = None


# Mock data for demonstration (replace with actual database queries)
mock_marketplaces = [
    {"id": 1, "name": "Amazon", "code": "AMZN", "description": "Amazon marketplace", "is_active": True},
    {"id": 2, "name": "eBay", "code": "EBAY", "description": "eBay marketplace", "is_active": True},
    {"id": 3, "name": "Walmart", "code": "WMT", "description": "Walmart marketplace", "is_active": True},
]

mock_categories = [
    {"id": 1, "marketplace_id": 1, "name": "Orders", "code": "ORD", "description": "Order-related tickets", "is_active": True, "display_order": 1},
    {"id": 2, "marketplace_id": 1, "name": "Returns", "code": "RET", "description": "Return-related tickets", "is_active": True, "display_order": 2},
    {"id": 3, "marketplace_id": 1, "name": "Claims", "code": "CLM", "description": "Claim-related tickets", "is_active": True, "display_order": 3},
]

mock_folders = [
    {"id": 1, "category_id": 1, "parent_id": None, "name": "Pending Orders", "path": "/Pending Orders", "description": "Orders awaiting processing", "is_active": True, "display_order": 1},
    {"id": 2, "category_id": 1, "parent_id": None, "name": "Shipped Orders", "path": "/Shipped Orders", "description": "Orders that have been shipped", "is_active": True, "display_order": 2},
    {"id": 3, "category_id": 2, "parent_id": None, "name": "Return Requests", "path": "/Return Requests", "description": "Customer return requests", "is_active": True, "display_order": 1},
]

mock_tickets = [
    {
        "id": 1, "ticket_number": "TKT-2024-001", "subject": "Order not received",
        "from_address": "customer1@example.com", "from_name": "John Doe",
        "body_text": "I haven't received my order #12345 yet.", "status": "new",
        "fulfillment_state": "processing", "priority": 2, "folder_id": 1,
        "assigned_to_id": None, "labels": ["urgent", "order-issue"],
        "created_at": datetime(2024, 1, 15, 10, 30), "updated_at": datetime(2024, 1, 15, 10, 30),
        "claims": [], "actions": [
            {"id": 1, "ticket_id": 1, "action_type": "created", "description": "Ticket created", "created_at": datetime(2024, 1, 15, 10, 30), "user_id": None}
        ]
    },
    {
        "id": 2, "ticket_number": "TKT-2024-002", "subject": "Damaged item received",
        "from_address": "customer2@example.com", "from_name": "Jane Smith",
        "body_text": "The item I received was damaged during shipping.", "status": "in_progress",
        "fulfillment_state": "shipped", "priority": 3, "folder_id": 3,
        "assigned_to_id": 1, "labels": ["claim", "damaged"],
        "created_at": datetime(2024, 1, 16, 14, 20), "updated_at": datetime(2024, 1, 16, 15, 45),
        "claims": [
            {"id": 1, "ticket_id": 2, "claim_number": "CLM-001", "claim_type": "damaged_item", "status": "investigating", "description": "Item damaged in transit", "claim_amount": 49.99, "created_at": datetime(2024, 1, 16, 15, 0)}
        ],
        "actions": [
            {"id": 2, "ticket_id": 2, "action_type": "created", "description": "Ticket created", "created_at": datetime(2024, 1, 16, 14, 20), "user_id": None},
            {"id": 3, "ticket_id": 2, "action_type": "assigned", "description": "Assigned to user 1", "created_at": datetime(2024, 1, 16, 15, 45), "user_id": 1}
        ]
    },
    {
        "id": 3, "ticket_number": "TKT-2024-003", "subject": "Wrong item shipped",
        "from_address": "customer3@example.com", "from_name": "Bob Johnson",
        "body_text": "I received the wrong item. I ordered a blue widget but got a red one.", "status": "resolved",
        "fulfillment_state": "delivered", "priority": 1, "folder_id": 2,
        "assigned_to_id": 1, "labels": ["resolved"],
        "created_at": datetime(2024, 1, 14, 9, 15), "updated_at": datetime(2024, 1, 17, 11, 30),
        "claims": [], "actions": [
            {"id": 4, "ticket_id": 3, "action_type": "created", "description": "Ticket created", "created_at": datetime(2024, 1, 14, 9, 15), "user_id": None},
            {"id": 5, "ticket_id": 3, "action_type": "status_changed", "description": "Status changed to resolved", "created_at": datetime(2024, 1, 17, 11, 30), "user_id": 1}
        ]
    },
]


# API Endpoints

@app.get("/")
def read_root():
    """Root endpoint with API information."""
    return {
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


@app.get("/health")
def health_check():
    """Health check endpoint."""
    return {"status": "healthy", "timestamp": datetime.utcnow()}


@app.get("/api/marketplaces", response_model=List[MarketplaceResponse])
def get_marketplaces():
    """Get all marketplaces."""
    return mock_marketplaces


@app.get("/api/marketplaces/{marketplace_id}", response_model=MarketplaceResponse)
def get_marketplace(marketplace_id: int):
    """Get a specific marketplace by ID."""
    marketplace = next((m for m in mock_marketplaces if m["id"] == marketplace_id), None)
    if not marketplace:
        raise HTTPException(status_code=404, detail="Marketplace not found")
    return marketplace


@app.get("/api/categories", response_model=List[CategoryResponse])
def get_categories(marketplace_id: Optional[int] = Query(None)):
    """Get all categories, optionally filtered by marketplace."""
    if marketplace_id:
        return [c for c in mock_categories if c["marketplace_id"] == marketplace_id]
    return mock_categories


@app.get("/api/categories/{category_id}", response_model=CategoryResponse)
def get_category(category_id: int):
    """Get a specific category by ID."""
    category = next((c for c in mock_categories if c["id"] == category_id), None)
    if not category:
        raise HTTPException(status_code=404, detail="Category not found")
    return category


@app.get("/api/folders", response_model=List[FolderResponse])
def get_folders(category_id: Optional[int] = Query(None), parent_id: Optional[int] = Query(None)):
    """Get all folders, optionally filtered by category or parent folder."""
    folders = mock_folders
    if category_id:
        folders = [f for f in folders if f["category_id"] == category_id]
    if parent_id is not None:
        folders = [f for f in folders if f.get("parent_id") == parent_id]
    return folders


@app.get("/api/folders/{folder_id}", response_model=FolderResponse)
def get_folder(folder_id: int):
    """Get a specific folder by ID."""
    folder = next((f for f in mock_folders if f["id"] == folder_id), None)
    if not folder:
        raise HTTPException(status_code=404, detail="Folder not found")
    return folder


@app.get("/api/tickets", response_model=List[TicketSummaryResponse])
def get_tickets(
    folder_id: Optional[int] = Query(None),
    status: Optional[str] = Query(None),
    limit: int = Query(100, le=1000)
):
    """Get all tickets with summary information, optionally filtered."""
    tickets = mock_tickets
    if folder_id:
        tickets = [t for t in tickets if t["folder_id"] == folder_id]
    if status:
        tickets = [t for t in tickets if t["status"] == status]
    
    # Return summary version
    return [{
        "id": t["id"],
        "ticket_number": t["ticket_number"],
        "subject": t["subject"],
        "from_address": t["from_address"],
        "status": t["status"],
        "fulfillment_state": t["fulfillment_state"],
        "priority": t["priority"],
        "created_at": t["created_at"],
        "folder_id": t["folder_id"],
        "labels": t.get("labels", [])
    } for t in tickets[:limit]]


@app.get("/api/tickets/{ticket_id}", response_model=TicketDetailResponse)
def get_ticket(ticket_id: int):
    """Get detailed information about a specific ticket."""
    ticket = next((t for t in mock_tickets if t["id"] == ticket_id), None)
    if not ticket:
        raise HTTPException(status_code=404, detail="Ticket not found")
    return ticket


@app.get("/api/labels", response_model=List[LabelResponse])
def get_labels():
    """Get all labels."""
    return [
        {"id": 1, "name": "urgent", "color": "#FF0000", "description": "Urgent tickets"},
        {"id": 2, "name": "order-issue", "color": "#FFA500", "description": "Order-related issues"},
        {"id": 3, "name": "claim", "color": "#0000FF", "description": "Claim tickets"},
        {"id": 4, "name": "damaged", "color": "#800080", "description": "Damaged items"},
        {"id": 5, "name": "resolved", "color": "#008000", "description": "Resolved tickets"},
    ]


@app.get("/api/claims", response_model=List[ClaimResponse])
def get_claims(ticket_id: Optional[int] = Query(None)):
    """Get all claims, optionally filtered by ticket."""
    all_claims = []
    for ticket in mock_tickets:
        for claim in ticket.get("claims", []):
            all_claims.append(claim)
    
    if ticket_id:
        all_claims = [c for c in all_claims if c["ticket_id"] == ticket_id]
    
    return all_claims


@app.get("/api/actions", response_model=List[ActionResponse])
def get_actions(ticket_id: Optional[int] = Query(None)):
    """Get all actions/audit logs, optionally filtered by ticket."""
    all_actions = []
    for ticket in mock_tickets:
        for action in ticket.get("actions", []):
            all_actions.append(action)
    
    if ticket_id:
        all_actions = [a for a in all_actions if a["ticket_id"] == ticket_id]
    
    return all_actions


if __name__ == "__main__":
    import uvicorn
    port = int(os.environ.get("PORT", 8000))
    uvicorn.run(app, host="0.0.0.0", port=port)

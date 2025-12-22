"""
SQLAlchemy models for the fulfillment ticket operational database.

This module defines the core data structures for managing fulfillment tickets,
including marketplaces, categories, folders, tickets, claims, users, and more.
"""
from datetime import datetime
from typing import Optional, List
from sqlalchemy import (
    Column, Integer, String, Text, Boolean, DateTime, ForeignKey,
    Table, Numeric, Enum as SQLEnum, UniqueConstraint, Index
)
from sqlalchemy.orm import DeclarativeBase, relationship, Mapped, mapped_column
from sqlalchemy.dialects.postgresql import JSONB
import enum


class Base(DeclarativeBase):
    """Base class for all database models."""
    pass


# Association table for many-to-many relationship between tickets and labels
ticket_labels = Table(
    'ticket_labels',
    Base.metadata,
    Column('ticket_id', Integer, ForeignKey('tickets.id', ondelete='CASCADE'), primary_key=True),
    Column('label_id', Integer, ForeignKey('labels.id', ondelete='CASCADE'), primary_key=True),
    Column('created_at', DateTime, default=datetime.utcnow)
)


class TicketStatus(enum.Enum):
    """Enumeration for ticket status values."""
    NEW = "new"
    IN_PROGRESS = "in_progress"
    PENDING = "pending"
    RESOLVED = "resolved"
    CLOSED = "closed"
    CANCELLED = "cancelled"


class FulfillmentState(enum.Enum):
    """Enumeration for fulfillment state values."""
    NOT_STARTED = "not_started"
    PROCESSING = "processing"
    SHIPPED = "shipped"
    DELIVERED = "delivered"
    FAILED = "failed"
    REFUNDED = "refunded"


class ClaimStatus(enum.Enum):
    """Enumeration for claim status values."""
    OPEN = "open"
    INVESTIGATING = "investigating"
    APPROVED = "approved"
    DENIED = "denied"
    CLOSED = "closed"


class ActionType(enum.Enum):
    """Enumeration for action/audit types."""
    CREATED = "created"
    UPDATED = "updated"
    STATUS_CHANGED = "status_changed"
    ASSIGNED = "assigned"
    COMMENT_ADDED = "comment_added"
    LABEL_ADDED = "label_added"
    LABEL_REMOVED = "label_removed"
    CLAIM_CREATED = "claim_created"
    CLAIM_UPDATED = "claim_updated"
    MOVED = "moved"


class User(Base):
    """User model for authentication and auditing."""
    __tablename__ = 'users'

    id: Mapped[int] = mapped_column(primary_key=True)
    username: Mapped[str] = mapped_column(String(100), unique=True, nullable=False, index=True)
    email: Mapped[str] = mapped_column(String(255), unique=True, nullable=False, index=True)
    full_name: Mapped[Optional[str]] = mapped_column(String(200))
    password_hash: Mapped[Optional[str]] = mapped_column(String(255))
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    is_admin: Mapped[bool] = mapped_column(Boolean, default=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    tickets_created: Mapped[List["Ticket"]] = relationship("Ticket", foreign_keys="Ticket.created_by_id", back_populates="created_by")
    tickets_assigned: Mapped[List["Ticket"]] = relationship("Ticket", foreign_keys="Ticket.assigned_to_id", back_populates="assigned_to")
    actions: Mapped[List["Action"]] = relationship("Action", back_populates="user")
    claims: Mapped[List["Claim"]] = relationship("Claim", foreign_keys="Claim.created_by_id", back_populates="created_by")


class Marketplace(Base):
    """Marketplace model representing different sales channels (e.g., Amazon, eBay)."""
    __tablename__ = 'marketplaces'

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(100), unique=True, nullable=False, index=True)
    code: Mapped[str] = mapped_column(String(50), unique=True, nullable=False)
    description: Mapped[Optional[str]] = mapped_column(Text)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    extra_data: Mapped[Optional[dict]] = mapped_column(JSONB)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    categories: Mapped[List["Category"]] = relationship("Category", back_populates="marketplace")


class Category(Base):
    """Category model for organizing tickets within a marketplace."""
    __tablename__ = 'categories'

    id: Mapped[int] = mapped_column(primary_key=True)
    marketplace_id: Mapped[int] = mapped_column(ForeignKey('marketplaces.id', ondelete='CASCADE'), nullable=False)
    name: Mapped[str] = mapped_column(String(100), nullable=False, index=True)
    code: Mapped[str] = mapped_column(String(50), nullable=False)
    description: Mapped[Optional[str]] = mapped_column(Text)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    display_order: Mapped[int] = mapped_column(Integer, default=0)
    extra_data: Mapped[Optional[dict]] = mapped_column(JSONB)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    marketplace: Mapped["Marketplace"] = relationship("Marketplace", back_populates="categories")
    folders: Mapped[List["Folder"]] = relationship("Folder", back_populates="category")

    __table_args__ = (
        UniqueConstraint('marketplace_id', 'code', name='uq_marketplace_category_code'),
        Index('ix_category_marketplace_id', 'marketplace_id'),
    )


class Folder(Base):
    """Folder model with hierarchical tree structure for organizing tickets."""
    __tablename__ = 'folders'

    id: Mapped[int] = mapped_column(primary_key=True)
    category_id: Mapped[int] = mapped_column(ForeignKey('categories.id', ondelete='CASCADE'), nullable=False)
    parent_id: Mapped[Optional[int]] = mapped_column(ForeignKey('folders.id', ondelete='CASCADE'))
    name: Mapped[str] = mapped_column(String(200), nullable=False, index=True)
    path: Mapped[Optional[str]] = mapped_column(String(1000))  # Full path for easy querying
    description: Mapped[Optional[str]] = mapped_column(Text)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    display_order: Mapped[int] = mapped_column(Integer, default=0)
    extra_data: Mapped[Optional[dict]] = mapped_column(JSONB)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    category: Mapped["Category"] = relationship("Category", back_populates="folders")
    parent: Mapped[Optional["Folder"]] = relationship("Folder", remote_side=[id], back_populates="children")
    children: Mapped[List["Folder"]] = relationship("Folder", back_populates="parent")
    tickets: Mapped[List["Ticket"]] = relationship("Ticket", back_populates="folder")

    __table_args__ = (
        Index('ix_folder_parent_id', 'parent_id'),
        Index('ix_folder_category_id', 'category_id'),
        Index('ix_folder_path', 'path'),
    )


class Label(Base):
    """Label/Tag model for categorizing tickets."""
    __tablename__ = 'labels'

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(100), unique=True, nullable=False, index=True)
    color: Mapped[Optional[str]] = mapped_column(String(7))  # Hex color code
    description: Mapped[Optional[str]] = mapped_column(Text)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    # Relationships
    tickets: Mapped[List["Ticket"]] = relationship(
        "Ticket",
        secondary=ticket_labels,
        back_populates="labels"
    )


class Ticket(Base):
    """Email/Ticket model representing fulfillment tickets."""
    __tablename__ = 'tickets'

    id: Mapped[int] = mapped_column(primary_key=True)
    folder_id: Mapped[int] = mapped_column(ForeignKey('folders.id', ondelete='RESTRICT'), nullable=False)
    ticket_number: Mapped[str] = mapped_column(String(50), unique=True, nullable=False, index=True)
    
    # Email-related fields
    email_message_id: Mapped[Optional[str]] = mapped_column(String(255), index=True)
    subject: Mapped[str] = mapped_column(String(500), nullable=False)
    from_address: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    from_name: Mapped[Optional[str]] = mapped_column(String(255))
    body_text: Mapped[Optional[str]] = mapped_column(Text)
    body_html: Mapped[Optional[str]] = mapped_column(Text)
    headers: Mapped[Optional[dict]] = mapped_column(JSONB)
    
    # Status and state
    status: Mapped[TicketStatus] = mapped_column(SQLEnum(TicketStatus), default=TicketStatus.NEW, nullable=False, index=True)
    fulfillment_state: Mapped[FulfillmentState] = mapped_column(SQLEnum(FulfillmentState), default=FulfillmentState.NOT_STARTED, nullable=False)
    priority: Mapped[int] = mapped_column(Integer, default=0)
    
    # Assignment
    created_by_id: Mapped[Optional[int]] = mapped_column(ForeignKey('users.id', ondelete='SET NULL'))
    assigned_to_id: Mapped[Optional[int]] = mapped_column(ForeignKey('users.id', ondelete='SET NULL'))
    
    # Dates
    received_date: Mapped[Optional[datetime]] = mapped_column(DateTime)
    due_date: Mapped[Optional[datetime]] = mapped_column(DateTime)
    closed_at: Mapped[Optional[datetime]] = mapped_column(DateTime)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Additional extra data
    extra_data: Mapped[Optional[dict]] = mapped_column(JSONB)

    # Relationships
    folder: Mapped["Folder"] = relationship("Folder", back_populates="tickets")
    created_by: Mapped[Optional["User"]] = relationship("User", foreign_keys=[created_by_id], back_populates="tickets_created")
    assigned_to: Mapped[Optional["User"]] = relationship("User", foreign_keys=[assigned_to_id], back_populates="tickets_assigned")
    labels: Mapped[List["Label"]] = relationship(
        "Label",
        secondary=ticket_labels,
        back_populates="tickets"
    )
    claims: Mapped[List["Claim"]] = relationship("Claim", back_populates="ticket")
    sales_orders: Mapped[List["SalesOrder"]] = relationship("SalesOrder", back_populates="ticket")
    actions: Mapped[List["Action"]] = relationship("Action", back_populates="ticket")

    __table_args__ = (
        Index('ix_ticket_folder_id', 'folder_id'),
        Index('ix_ticket_status', 'status'),
        Index('ix_ticket_created_at', 'created_at'),
        Index('ix_ticket_assigned_to_id', 'assigned_to_id'),
    )


class Claim(Base):
    """Claim model for tracking customer claims and disputes."""
    __tablename__ = 'claims'

    id: Mapped[int] = mapped_column(primary_key=True)
    ticket_id: Mapped[int] = mapped_column(ForeignKey('tickets.id', ondelete='CASCADE'), nullable=False)
    claim_number: Mapped[str] = mapped_column(String(50), unique=True, nullable=False, index=True)
    claim_type: Mapped[str] = mapped_column(String(100), nullable=False)  # e.g., 'refund', 'replacement', 'missing_item'
    status: Mapped[ClaimStatus] = mapped_column(SQLEnum(ClaimStatus), default=ClaimStatus.OPEN, nullable=False, index=True)
    
    description: Mapped[Optional[str]] = mapped_column(Text)
    resolution: Mapped[Optional[str]] = mapped_column(Text)
    claim_amount: Mapped[Optional[float]] = mapped_column(Numeric(10, 2))
    approved_amount: Mapped[Optional[float]] = mapped_column(Numeric(10, 2))
    
    created_by_id: Mapped[Optional[int]] = mapped_column(ForeignKey('users.id', ondelete='SET NULL'))
    resolved_by_id: Mapped[Optional[int]] = mapped_column(ForeignKey('users.id', ondelete='SET NULL'))
    
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    resolved_at: Mapped[Optional[datetime]] = mapped_column(DateTime)
    
    extra_data: Mapped[Optional[dict]] = mapped_column(JSONB)

    # Relationships
    ticket: Mapped["Ticket"] = relationship("Ticket", back_populates="claims")
    created_by: Mapped[Optional["User"]] = relationship("User", foreign_keys=[created_by_id], back_populates="claims")
    resolved_by: Mapped[Optional["User"]] = relationship("User", foreign_keys=[resolved_by_id])

    __table_args__ = (
        Index('ix_claim_ticket_id', 'ticket_id'),
        Index('ix_claim_status', 'status'),
    )


class Action(Base):
    """Action/Audit model for tracking all changes to tickets."""
    __tablename__ = 'actions'

    id: Mapped[int] = mapped_column(primary_key=True)
    ticket_id: Mapped[int] = mapped_column(ForeignKey('tickets.id', ondelete='CASCADE'), nullable=False)
    user_id: Mapped[Optional[int]] = mapped_column(ForeignKey('users.id', ondelete='SET NULL'))
    action_type: Mapped[ActionType] = mapped_column(SQLEnum(ActionType), nullable=False, index=True)
    
    description: Mapped[Optional[str]] = mapped_column(Text)
    old_value: Mapped[Optional[dict]] = mapped_column(JSONB)
    new_value: Mapped[Optional[dict]] = mapped_column(JSONB)
    
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, index=True)
    
    extra_data: Mapped[Optional[dict]] = mapped_column(JSONB)

    # Relationships
    ticket: Mapped["Ticket"] = relationship("Ticket", back_populates="actions")
    user: Mapped[Optional["User"]] = relationship("User", back_populates="actions")

    __table_args__ = (
        Index('ix_action_ticket_id', 'ticket_id'),
        Index('ix_action_created_at', 'created_at'),
        Index('ix_action_type', 'action_type'),
    )


class SalesOrder(Base):
    """Sales Order model linking tickets to sales, purchase orders, and payments."""
    __tablename__ = 'sales_orders'

    id: Mapped[int] = mapped_column(primary_key=True)
    ticket_id: Mapped[int] = mapped_column(ForeignKey('tickets.id', ondelete='CASCADE'), nullable=False)
    
    sales_id: Mapped[str] = mapped_column(String(100), nullable=False, index=True)
    purchase_order: Mapped[Optional[str]] = mapped_column(String(100), index=True)
    
    # Order details
    order_number: Mapped[Optional[str]] = mapped_column(String(100), index=True)
    order_date: Mapped[Optional[datetime]] = mapped_column(DateTime)
    ship_date: Mapped[Optional[datetime]] = mapped_column(DateTime)
    delivery_date: Mapped[Optional[datetime]] = mapped_column(DateTime)
    
    # Payment information
    payment_method: Mapped[Optional[str]] = mapped_column(String(50))
    payment_status: Mapped[Optional[str]] = mapped_column(String(50))
    payment_reference: Mapped[Optional[str]] = mapped_column(String(100))
    transaction_id: Mapped[Optional[str]] = mapped_column(String(100), index=True)
    
    # Amounts
    total_amount: Mapped[Optional[float]] = mapped_column(Numeric(10, 2))
    paid_amount: Mapped[Optional[float]] = mapped_column(Numeric(10, 2))
    refund_amount: Mapped[Optional[float]] = mapped_column(Numeric(10, 2))
    
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    extra_data: Mapped[Optional[dict]] = mapped_column(JSONB)

    # Relationships
    ticket: Mapped["Ticket"] = relationship("Ticket", back_populates="sales_orders")

    __table_args__ = (
        Index('ix_sales_order_ticket_id', 'ticket_id'),
        Index('ix_sales_order_sales_id', 'sales_id'),
    )

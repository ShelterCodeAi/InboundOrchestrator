# Fulfillment Ticket System - Database Schema

## Overview

The fulfillment ticket operational database is designed to manage email-based tickets, categorize them hierarchically, track fulfillment states, handle claims, and maintain a complete audit trail of all actions.

## Schema Diagram

```
┌─────────────────┐
│  Marketplaces   │
│─────────────────│
│ id (PK)         │
│ name            │
│ code            │
│ description     │
│ is_active       │
│ extra_data      │
│ created_at      │
│ updated_at      │
└────────┬────────┘
         │
         │ 1:N
         │
┌────────▼────────┐
│   Categories    │
│─────────────────│
│ id (PK)         │
│ marketplace_id  │◄─┐
│ name            │  │
│ code            │  │
│ description     │  │
│ is_active       │  │
│ display_order   │  │
│ extra_data      │  │
│ created_at      │  │
│ updated_at      │  │
└────────┬────────┘  │
         │           │
         │ 1:N       │
         │           │
┌────────▼────────┐  │
│     Folders     │  │
│─────────────────│  │
│ id (PK)         │  │
│ category_id     │──┘
│ parent_id (FK)  │◄─┐ (self-ref for tree)
│ name            │  │
│ path            │  │
│ description     │  │
│ is_active       │  │
│ display_order   │  │
│ extra_data      │  │
│ created_at      │  │
│ updated_at      │  │
└────────┬────────┘  │
         │           │
         │ 1:N       │
         │           │
┌────────▼────────────────┐         ┌─────────────────┐
│       Tickets           │         │     Labels      │
│─────────────────────────│         │─────────────────│
│ id (PK)                 │         │ id (PK)         │
│ folder_id (FK)          │         │ name (UNIQUE)   │
│ ticket_number (UNIQUE)  │         │ color           │
│ email_message_id        │         │ description     │
│ subject                 │         │ is_active       │
│ from_address            │         │ created_at      │
│ from_name               │         └────────┬────────┘
│ body_text               │                  │
│ body_html               │                  │ N:M
│ headers (JSONB)         │         ┌────────▼────────┐
│ status (ENUM)           │         │ Ticket_Labels   │
│ fulfillment_state (ENUM)│         │─────────────────│
│ priority                │◄────────┤ ticket_id (FK)  │
│ created_by_id (FK)      │         │ label_id (FK)   │
│ assigned_to_id (FK)     │         │ created_at      │
│ received_date           │         └─────────────────┘
│ due_date                │
│ closed_at               │
│ created_at              │
│ updated_at              │
│ extra_data (JSONB)      │
└────────┬────────────────┘
         │
         ├──────────────────┐
         │                  │
         │ 1:N              │ 1:N
         │                  │
┌────────▼────────┐  ┌──────▼──────────┐
│     Claims      │  │  Sales_Orders   │
│─────────────────│  │─────────────────│
│ id (PK)         │  │ id (PK)         │
│ ticket_id (FK)  │  │ ticket_id (FK)  │
│ claim_number    │  │ sales_id        │
│ claim_type      │  │ purchase_order  │
│ status (ENUM)   │  │ order_number    │
│ description     │  │ order_date      │
│ resolution      │  │ ship_date       │
│ claim_amount    │  │ delivery_date   │
│ approved_amount │  │ payment_method  │
│ created_by_id   │  │ payment_status  │
│ resolved_by_id  │  │ payment_ref     │
│ created_at      │  │ transaction_id  │
│ updated_at      │  │ total_amount    │
│ resolved_at     │  │ paid_amount     │
│ extra_data      │  │ refund_amount   │
└─────────────────┘  │ created_at      │
                     │ updated_at      │
                     │ extra_data      │
                     └─────────────────┘

┌─────────────────┐         ┌─────────────────┐
│      Users      │         │     Actions     │
│─────────────────│         │─────────────────│
│ id (PK)         │◄────────┤ id (PK)         │
│ username (UQ)   │         │ ticket_id (FK)  │─┐
│ email (UNIQUE)  │         │ user_id (FK)    │ │
│ full_name       │         │ action_type     │ │
│ password_hash   │         │ description     │ │
│ is_active       │         │ old_value       │ │
│ is_admin        │         │ new_value       │ │
│ created_at      │         │ created_at      │ │
│ updated_at      │         │ extra_data      │ │
└─────────────────┘         └─────────────────┘ │
                                                 │
                                                 │
                            (References Tickets)─┘
```

## Entity Descriptions

### Core Entities

#### **Marketplaces**
Top-level entity representing different sales channels (e.g., Amazon, eBay, Walmart).

#### **Categories**
Organizational units within each marketplace (e.g., Orders, Returns, Claims).

#### **Folders**
Hierarchical tree structure for organizing tickets within categories.

#### **Tickets**
Central entity representing email-based fulfillment tickets.

#### **Labels**
Tagging system for categorizing tickets (many-to-many relationship).

### Financial & Claims

#### **Claims**
Customer claims and disputes linked to tickets.

#### **Sales_Orders**
Links tickets to sales, purchase orders, and payment information.

### System Entities

#### **Users**
User accounts for authentication and auditing.

#### **Actions**
Complete audit trail of all ticket modifications.

See full documentation at docs/DATABASE_SCHEMA.md for complete details.

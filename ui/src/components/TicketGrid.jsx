/**
 * TicketGrid Component
 * Display tickets in a card/grid view with summary information
 */
import React, { useState, useEffect } from 'react';
import { api } from '../api/client';
import TicketDetailModal from './TicketDetailModal';
import './TicketGrid.css';

export default function TicketGrid({ folderId }) {
  const [tickets, setTickets] = useState([]);
  const [selectedTicket, setSelectedTicket] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const [statusFilter, setStatusFilter] = useState('');

  useEffect(() => {
    if (folderId) {
      loadTickets();
    } else {
      setTickets([]);
    }
  }, [folderId, statusFilter]);

  const loadTickets = async () => {
    setLoading(true);
    setError(null);
    try {
      const data = await api.getTickets(folderId, statusFilter || null);
      setTickets(data);
    } catch (err) {
      setError('Failed to load tickets');
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  const getStatusClass = (status) => {
    const statusMap = {
      'new': 'status-new',
      'in_progress': 'status-in-progress',
      'pending': 'status-pending',
      'resolved': 'status-resolved',
      'closed': 'status-closed',
      'cancelled': 'status-cancelled',
    };
    return statusMap[status] || 'status-default';
  };

  const getFulfillmentClass = (state) => {
    const stateMap = {
      'not_started': 'fulfillment-not-started',
      'processing': 'fulfillment-processing',
      'shipped': 'fulfillment-shipped',
      'delivered': 'fulfillment-delivered',
      'failed': 'fulfillment-failed',
      'refunded': 'fulfillment-refunded',
    };
    return stateMap[state] || 'fulfillment-default';
  };

  const formatStatus = (status) => {
    return status.replace(/_/g, ' ').replace(/\b\w/g, l => l.toUpperCase());
  };

  const formatDate = (dateString) => {
    const date = new Date(dateString);
    return date.toLocaleString();
  };

  if (!folderId) {
    return (
      <div className="ticket-grid-placeholder">
        <p>Please select a folder to view tickets</p>
      </div>
    );
  }

  return (
    <div className="ticket-grid-container">
      <div className="ticket-grid-header">
        <h2>Tickets</h2>
        <div className="filters">
          <select
            value={statusFilter}
            onChange={(e) => setStatusFilter(e.target.value)}
            className="status-filter"
          >
            <option value="">All Statuses</option>
            <option value="new">New</option>
            <option value="in_progress">In Progress</option>
            <option value="pending">Pending</option>
            <option value="resolved">Resolved</option>
            <option value="closed">Closed</option>
          </select>
        </div>
      </div>

      {error && <div className="error-message">{error}</div>}
      {loading && <div className="loading">Loading tickets...</div>}

      <div className="ticket-grid">
        {tickets.map((ticket) => (
          <div
            key={ticket.id}
            className="ticket-card"
            onClick={() => setSelectedTicket(ticket)}
          >
            <div className="ticket-header">
              <span className="ticket-number">{ticket.ticket_number}</span>
              <span className={`ticket-priority priority-${ticket.priority}`}>
                P{ticket.priority}
              </span>
            </div>
            
            <div className="ticket-subject">{ticket.subject}</div>
            
            <div className="ticket-from">
              From: <strong>{ticket.from_address}</strong>
            </div>
            
            <div className="ticket-badges">
              <span className={`badge ${getStatusClass(ticket.status)}`}>
                {formatStatus(ticket.status)}
              </span>
              <span className={`badge ${getFulfillmentClass(ticket.fulfillment_state)}`}>
                {formatStatus(ticket.fulfillment_state)}
              </span>
            </div>
            
            {ticket.labels && ticket.labels.length > 0 && (
              <div className="ticket-labels">
                {ticket.labels.map((label, idx) => (
                  <span key={idx} className="label">{label}</span>
                ))}
              </div>
            )}
            
            <div className="ticket-date">
              {formatDate(ticket.created_at)}
            </div>
          </div>
        ))}
      </div>

      {tickets.length === 0 && !loading && (
        <div className="no-tickets">
          <p>No tickets found in this folder</p>
        </div>
      )}

      {selectedTicket && (
        <TicketDetailModal
          ticketId={selectedTicket.id}
          onClose={() => setSelectedTicket(null)}
        />
      )}
    </div>
  );
}

/**
 * TicketDetailModal Component
 * Modal popup to view full ticket details, actions, and history
 */
import React, { useState, useEffect } from 'react';
import { api } from '../api/client';
import './TicketDetailModal.css';

export default function TicketDetailModal({ ticketId, onClose }) {
  const [ticket, setTicket] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);

  useEffect(() => {
    if (ticketId) {
      loadTicket();
    }
  }, [ticketId]);

  const loadTicket = async () => {
    setLoading(true);
    setError(null);
    try {
      const data = await api.getTicket(ticketId);
      setTicket(data);
    } catch (err) {
      setError('Failed to load ticket details');
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  const formatStatus = (status) => {
    return status.replace(/_/g, ' ').replace(/\b\w/g, l => l.toUpperCase());
  };

  const formatDate = (dateString) => {
    const date = new Date(dateString);
    return date.toLocaleString();
  };

  const handleBackdropClick = (e) => {
    if (e.target.className === 'modal-backdrop') {
      onClose();
    }
  };

  if (!ticketId) return null;

  return (
    <div className="modal-backdrop" onClick={handleBackdropClick}>
      <div className="modal-content">
        <div className="modal-header">
          <h2>Ticket Details</h2>
          <button className="close-button" onClick={onClose}>×</button>
        </div>

        {loading && <div className="loading">Loading ticket details...</div>}
        {error && <div className="error-message">{error}</div>}

        {ticket && (
          <div className="modal-body">
            <div className="ticket-info">
              <div className="info-row">
                <span className="label">Ticket Number:</span>
                <span className="value ticket-number-value">{ticket.ticket_number}</span>
              </div>
              
              <div className="info-row">
                <span className="label">Subject:</span>
                <span className="value">{ticket.subject}</span>
              </div>
              
              <div className="info-row">
                <span className="label">From:</span>
                <span className="value">
                  {ticket.from_name && `${ticket.from_name} `}
                  &lt;{ticket.from_address}&gt;
                </span>
              </div>
              
              <div className="info-row">
                <span className="label">Status:</span>
                <span className="value">
                  <span className="status-badge">{formatStatus(ticket.status)}</span>
                </span>
              </div>
              
              <div className="info-row">
                <span className="label">Fulfillment State:</span>
                <span className="value">
                  <span className="fulfillment-badge">{formatStatus(ticket.fulfillment_state)}</span>
                </span>
              </div>
              
              <div className="info-row">
                <span className="label">Priority:</span>
                <span className="value">P{ticket.priority}</span>
              </div>
              
              <div className="info-row">
                <span className="label">Created:</span>
                <span className="value">{formatDate(ticket.created_at)}</span>
              </div>
              
              <div className="info-row">
                <span className="label">Last Updated:</span>
                <span className="value">{formatDate(ticket.updated_at)}</span>
              </div>
              
              {ticket.labels && ticket.labels.length > 0 && (
                <div className="info-row">
                  <span className="label">Labels:</span>
                  <div className="labels-list">
                    {ticket.labels.map((label, idx) => (
                      <span key={idx} className="label-tag">{label}</span>
                    ))}
                  </div>
                </div>
              )}
            </div>

            {ticket.body_text && (
              <div className="ticket-body">
                <h3>Message</h3>
                <div className="body-content">{ticket.body_text}</div>
              </div>
            )}

            {ticket.claims && ticket.claims.length > 0 && (
              <div className="claims-section">
                <h3>Claims</h3>
                {ticket.claims.map((claim) => (
                  <div key={claim.id} className="claim-card">
                    <div className="claim-header">
                      <span className="claim-number">{claim.claim_number}</span>
                      <span className="claim-status">{formatStatus(claim.status)}</span>
                    </div>
                    <div className="claim-type">Type: {formatStatus(claim.claim_type)}</div>
                    {claim.description && <p className="claim-desc">{claim.description}</p>}
                    {claim.claim_amount && (
                      <div className="claim-amount">
                        Amount: ${claim.claim_amount.toFixed(2)}
                      </div>
                    )}
                  </div>
                ))}
              </div>
            )}

            {ticket.actions && ticket.actions.length > 0 && (
              <div className="actions-section">
                <h3>History</h3>
                <div className="actions-timeline">
                  {ticket.actions.map((action) => (
                    <div key={action.id} className="action-item">
                      <div className="action-time">{formatDate(action.created_at)}</div>
                      <div className="action-type">{formatStatus(action.action_type)}</div>
                      {action.description && (
                        <div className="action-desc">{action.description}</div>
                      )}
                    </div>
                  ))}
                </div>
              </div>
            )}
          </div>
        )}
      </div>
    </div>
  );
}

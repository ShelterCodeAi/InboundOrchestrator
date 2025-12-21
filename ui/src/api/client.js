/**
 * API client for the Fulfillment Ticket System
 */

const API_BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000';

/**
 * Fetch wrapper with error handling
 */
async function fetchAPI(endpoint, options = {}) {
  try {
    const response = await fetch(`${API_BASE_URL}${endpoint}`, {
      ...options,
      headers: {
        'Content-Type': 'application/json',
        ...options.headers,
      },
    });

    if (!response.ok) {
      throw new Error(`API Error: ${response.statusText}`);
    }

    return await response.json();
  } catch (error) {
    console.error('API call failed:', error);
    throw error;
  }
}

export const api = {
  // Marketplaces
  getMarketplaces: () => fetchAPI('/api/marketplaces'),
  getMarketplace: (id) => fetchAPI(`/api/marketplaces/${id}`),

  // Categories
  getCategories: (marketplaceId) => {
    const params = marketplaceId ? `?marketplace_id=${marketplaceId}` : '';
    return fetchAPI(`/api/categories${params}`);
  },
  getCategory: (id) => fetchAPI(`/api/categories/${id}`),

  // Folders
  getFolders: (categoryId, parentId) => {
    const params = new URLSearchParams();
    if (categoryId) params.append('category_id', categoryId);
    if (parentId !== undefined) params.append('parent_id', parentId);
    const queryString = params.toString() ? `?${params.toString()}` : '';
    return fetchAPI(`/api/folders${queryString}`);
  },
  getFolder: (id) => fetchAPI(`/api/folders/${id}`),

  // Tickets
  getTickets: (folderId, status, limit = 100) => {
    const params = new URLSearchParams();
    if (folderId) params.append('folder_id', folderId);
    if (status) params.append('status', status);
    if (limit) params.append('limit', limit);
    const queryString = params.toString() ? `?${params.toString()}` : '';
    return fetchAPI(`/api/tickets${queryString}`);
  },
  getTicket: (id) => fetchAPI(`/api/tickets/${id}`),

  // Labels
  getLabels: () => fetchAPI('/api/labels'),

  // Claims
  getClaims: (ticketId) => {
    const params = ticketId ? `?ticket_id=${ticketId}` : '';
    return fetchAPI(`/api/claims${params}`);
  },

  // Actions
  getActions: (ticketId) => {
    const params = ticketId ? `?ticket_id=${ticketId}` : '';
    return fetchAPI(`/api/actions${params}`);
  },

  // Health check
  healthCheck: () => fetchAPI('/health'),
};

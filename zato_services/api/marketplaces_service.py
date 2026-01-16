"""
Zato REST API service for marketplaces.

This service migrates the FastAPI /api/marketplaces endpoint to Zato.
"""

from zato.server.service import Service
import json


class MarketplacesAPIService(Service):
    """
    REST API for marketplaces.
    
    GET /api/marketplaces - List all marketplaces
    GET /api/marketplaces/{id} - Get specific marketplace
    """
    
    name = 'api.marketplaces.list'
    
    class SimpleIO:
        output_optional = ('marketplaces', 'marketplace', 'error')
    
    def handle(self):
        # Get marketplace_id from request if provided
        marketplace_id = self.request.payload.get('id') if self.request.payload else None
        
        try:
            # Get PostgreSQL connection for fulfillment database
            with self.outgoing.sql.get('fulfillment_db').session() as session:
                
                if marketplace_id:
                    # Get specific marketplace
                    query = """
                        SELECT id, name, code, description, is_active 
                        FROM marketplaces 
                        WHERE id = :id
                    """
                    result = session.execute(query, {'id': marketplace_id}).fetchone()
                    
                    if not result:
                        self.response.payload.error = 'Marketplace not found'
                        self.response.status_code = 404
                        return
                    
                    self.response.payload.marketplace = {
                        'id': result.id,
                        'name': result.name,
                        'code': result.code,
                        'description': result.description,
                        'is_active': result.is_active
                    }
                else:
                    # Get all marketplaces
                    query = """
                        SELECT id, name, code, description, is_active 
                        FROM marketplaces 
                        ORDER BY name
                    """
                    results = session.execute(query)
                    
                    marketplaces = []
                    for row in results:
                        marketplaces.append({
                            'id': row.id,
                            'name': row.name,
                            'code': row.code,
                            'description': row.description,
                            'is_active': row.is_active
                        })
                    
                    self.response.payload.marketplaces = marketplaces
                    
        except Exception as e:
            self.logger.error(f"Error fetching marketplaces: {e}")
            self.response.payload.error = str(e)
            self.response.status_code = 500

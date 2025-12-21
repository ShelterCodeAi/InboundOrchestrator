# Fulfillment Ticket System - Setup Guide

## Prerequisites

- Python 3.8 or higher
- Node.js 20.x or higher
- PostgreSQL 12 or higher
- Git

## Installation Steps

### 1. Clone the Repository

```bash
git clone https://github.com/ShelterCodeAi/InboundOrchestrator.git
cd InboundOrchestrator
```

### 2. Set Up Python Environment

```bash
# Create virtual environment (recommended)
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install Python dependencies
pip install -r requirements.txt
pip install fastapi uvicorn sqlalchemy alembic psycopg2-binary
```

### 3. Set Up Database

```bash
# Create PostgreSQL database
createdb fulfillment_db

# Or using psql
psql -U postgres
CREATE DATABASE fulfillment_db;
\q

# Set database URL (optional - overrides alembic.ini)
export DATABASE_URL="postgresql://postgres:password@localhost:5432/fulfillment_db"

# Run database migrations
alembic upgrade head
```

**Expected Output:**
```
INFO  [alembic.runtime.migration] Context impl PostgresqlImpl.
INFO  [alembic.runtime.migration] Will assume transactional DDL.
INFO  [alembic.runtime.migration] Running upgrade  -> 48ea33bd6d47, Initial fulfillment ticket schema
```

### 4. Start the API Backend

```bash
# Start with Python directly
cd api
python main.py

# Or use uvicorn
uvicorn api.main:app --reload --host 0.0.0.0 --port 8000
```

**API will be available at:**
- Base URL: http://localhost:8000
- Interactive docs: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc

**Test the API:**
```bash
curl http://localhost:8000/health
curl http://localhost:8000/api/marketplaces
```

### 5. Start the React UI

```bash
# Navigate to UI directory
cd ui

# Install dependencies
npm install

# Start development server
npm run dev
```

**UI will be available at:**
- React app: http://localhost:5173

### 6. Verify Installation

1. Open http://localhost:5173 in your browser
2. You should see the Fulfillment Ticket System welcome page
3. Click on "Amazon" marketplace in the sidebar
4. Click on "Orders" category
5. Click on "Pending Orders" folder
6. You should see a ticket card
7. Click on the ticket to see the detail modal

## Environment Variables

Create a `.env` file in the root directory:

```bash
# Database
DATABASE_URL=postgresql://postgres:password@localhost:5432/fulfillment_db

# API
PORT=8000

# React UI
VITE_API_URL=http://localhost:8000
```

## Production Deployment

### Database

For production, update the database connection in `alembic.ini`:

```ini
sqlalchemy.url = postgresql://user:password@host:5432/fulfillment_db
```

Or use environment variable:
```bash
export DATABASE_URL="postgresql://user:password@host:5432/fulfillment_db"
```

### API Backend

```bash
# Install production server
pip install gunicorn

# Run with gunicorn
gunicorn api.main:app -w 4 -k uvicorn.workers.UvicornWorker --bind 0.0.0.0:8000
```

### React UI

```bash
cd ui

# Build for production
npm run build

# The build output will be in ui/dist
# Serve with any static file server (nginx, Apache, etc.)
```

## Troubleshooting

### Database Connection Issues

If you get "connection refused" errors:

1. Check PostgreSQL is running:
   ```bash
   sudo service postgresql status  # Linux
   brew services list              # macOS
   ```

2. Verify connection parameters:
   ```bash
   psql -U postgres -d fulfillment_db
   ```

3. Check firewall settings allow port 5432

### API Won't Start

1. Check port 8000 is available:
   ```bash
   lsof -i :8000  # Check what's using the port
   ```

2. Verify all dependencies are installed:
   ```bash
   pip list | grep -E "(fastapi|uvicorn|sqlalchemy|alembic)"
   ```

### UI Won't Start

1. Check Node.js version:
   ```bash
   node --version  # Should be 20.x or higher
   ```

2. Clear node_modules and reinstall:
   ```bash
   rm -rf node_modules package-lock.json
   npm install
   ```

3. Check port 5173 is available:
   ```bash
   lsof -i :5173
   ```

### Migration Errors

If migrations fail:

1. Check database exists:
   ```bash
   psql -U postgres -l | grep fulfillment_db
   ```

2. Reset migrations (development only):
   ```bash
   alembic downgrade base
   alembic upgrade head
   ```

## Development Workflow

### Making Database Changes

1. Modify `database/models.py`
2. Generate migration:
   ```bash
   alembic revision --autogenerate -m "Description of changes"
   ```
3. Review generated migration in `migrations/versions/`
4. Apply migration:
   ```bash
   alembic upgrade head
   ```

### Updating API

1. Modify `api/main.py`
2. Server auto-reloads with `--reload` flag
3. Test with curl or browser

### Updating UI

1. Modify React components in `ui/src/components/`
2. Vite hot-reloads changes automatically
3. View in browser

## Next Steps

- Replace mock data in `api/main.py` with real database queries
- Implement authentication and authorization
- Add ticket creation/editing functionality
- Implement advanced search and filtering
- Add email integration
- Set up CI/CD pipeline

## Support

For issues or questions:
- Check the [Database Schema Documentation](DATABASE_SCHEMA.md)
- Review the [API Documentation](API_ENDPOINTS.md)
- Create an issue in the GitHub repository

# Docker Skill - Build and Start Application

Build and run the NovaWrite AI application using Docker Compose.

## Services

The application consists of 5 services:
- **postgres** - PostgreSQL database with pgvector (port 5432)
- **ai-service** - AI service for LLM operations (port 8001)
- **neo4j** - Graph database for knowledge graphs (port 7474, 7687)
- **backend** - FastAPI backend server (port 8000)
- **frontend** - React frontend (port 3000)

## Commands

### Start All Services
```bash
docker-compose up -d
```

### Start with Build (rebuild images)
```bash
docker-compose up -d --build
```

### Start Specific Services
```bash
# Start only database and backend
docker-compose up -d postgres backend

# Start without neo4j
docker-compose up -d postgres ai-service backend frontend
```

### View Logs
```bash
# All services
docker-compose logs -f

# Specific service
docker-compose logs -f backend
```

### Stop All Services
```bash
docker-compose down
```

### Stop and Remove Volumes (clean reset)
```bash
docker-compose down -v
```

### Rebuild Single Service
```bash
docker-compose build backend
docker-compose up -d backend
```

## Environment Variables

Required environment variables (set in `.env` file or export):
- `GEMINI_API_KEY` - Google Gemini API key
- `GEMINI_PROXY` - Proxy for Gemini API (optional)
- `DEEPSEEK_API_KEY` - DeepSeek API key (for agent)
- `NEO4J_PASSWORD` - Neo4j password (default: neo4j)
- `SECRET_KEY` - JWT secret key

## Usage Examples

User input:
- `/docker` - Start all services
- `/docker build` - Rebuild and start all services
- `/docker stop` - Stop all services
- `/docker logs` - View logs
- `/docker restart backend` - Restart backend service

## Execution Flow

1. Check if Docker is running
2. Check if `.env` file exists with required variables
3. Execute the appropriate docker-compose command
4. Monitor startup and report service status
5. Show access URLs when ready:
   - Frontend: http://localhost:3000
   - Backend API: http://localhost:8000
   - Neo4j Browser: http://localhost:7474

## Health Checks

After starting, verify services are healthy:
```bash
docker-compose ps
```

All services should show "Up" or "Up (healthy)" status.

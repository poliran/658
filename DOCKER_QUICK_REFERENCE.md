# Quick Reference - Docker Commands

## Production

```bash
# Build image
docker build -t lottery-predictor:latest .

# List images
docker images lottery-predictor

# Run with compose
docker compose up
docker compose up -d                    # Detached

# View logs
docker compose logs -f                  # Follow logs
docker compose logs -f lottery-predictor

# Run commands
docker compose run --rm report-runner python cli.py report
docker compose run --rm report-runner python cli.py optimize
docker compose run --rm report-runner python cli.py evaluate

# Stop
docker compose down
docker compose down -v                  # Include volumes

# Status
docker compose ps
docker compose exec lottery-predictor env
docker compose exec lottery-predictor bash

# Scale (run multiple instances)
docker compose up -d --scale lottery-predictor=3
```

## Development

```bash
# Start with hot reload
docker compose -f docker-compose.dev.yml up

# Run tests
docker compose -f docker-compose.dev.yml run --rm test-runner

# Execute in running container
docker compose -f docker-compose.dev.yml exec lottery-predictor-dev python cli.py predict
docker compose -f docker-compose.dev.yml exec lottery-predictor-dev python cli.py optimize
docker compose -f docker-compose.dev.yml exec lottery-predictor-dev bash

# Run specific tests
docker compose -f docker-compose.dev.yml exec lottery-predictor-dev pytest tests/test_file.py -v

# Format code
docker compose -f docker-compose.dev.yml exec lottery-predictor-dev black src/

# Lint code
docker compose -f docker-compose.dev.yml exec lottery-predictor-dev flake8 src/
```

## Debugging

```bash
# View image layers
docker history lottery-predictor:latest

# Inspect running container
docker compose ps
docker inspect $(docker compose ps -q lottery-predictor)

# Check resource usage
docker stats lottery-predictor

# View full logs
docker compose logs lottery-predictor

# Access container shell
docker compose exec lottery-predictor bash

# Run manual command
docker run --rm lottery-predictor:latest python -c "import sys; print(sys.version)"

# Check health
docker compose exec lottery-predictor python -c "from src.predictor.constants import RiskLevel; print('OK')"
```

## Build Optimization

```bash
# View build context
du -sh .

# Build with no cache
docker build --no-cache -t lottery-predictor:latest .

# Check image size
docker images lottery-predictor --format "table {{.Size}}"

# View image details
docker inspect lottery-predictor:latest

# Prune unused layers
docker builder prune

# Save image to file
docker save lottery-predictor:latest > lottery-predictor.tar

# Load image from file
docker load < lottery-predictor.tar
```

## Volume and Network

```bash
# List volumes
docker volume ls

# Inspect volume
docker volume inspect <volume-name>

# List networks
docker network ls

# Inspect network
docker network inspect lottery-net

# Cleanup unused volumes
docker volume prune

# Mount volume into running container
docker compose exec -v /path/host:/path/container lottery-predictor bash
```

## Registry and Deployment

```bash
# Tag for registry
docker tag lottery-predictor:latest myregistry/lottery-predictor:v1.0.0

# Push to registry
docker push myregistry/lottery-predictor:v1.0.0

# Pull from registry
docker pull myregistry/lottery-predictor:v1.0.0

# Login to registry
docker login myregistry

# Logout from registry
docker logout myregistry
```

## System Cleanup

```bash
# Remove unused images
docker rmi <image-id>

# Remove unused containers
docker container prune

# Remove unused volumes
docker volume prune

# Remove unused networks
docker network prune

# Complete cleanup (WARNING: removes everything unused)
docker system prune -a

# Show disk usage
docker system df
```

## Files Reference

| File | Purpose |
|------|---------|
| `Dockerfile` | Production image build |
| `docker-compose.yml` | Production orchestration |
| `docker-compose.dev.yml` | Development with hot reload |
| `.dockerignore` | Build context optimization |
| `DOCKER_SETUP.md` | Complete guide |
| `CODE_REVIEW_BUGS.md` | Bug analysis |
| `FIXES_APPLIED.md` | All fixes summary |
| `PROJECT_COMPLETION_SUMMARY.md` | Overall summary |

## Environment Variables

**Production:**
- `PYTHONUNBUFFERED=1`
- `PYTHONDONTWRITEBYTECODE=1`
- `PYTHONHASHSEED=random`
- `LOG_LEVEL=INFO`

**Development:**
- `LOG_LEVEL=DEBUG`
- `ENV=development`

## Port Mapping

Currently: **No exposed ports** (internal only)

To expose port 8000:
```yaml
ports:
  - "8000:8000"
```

## Health Check

```bash
# Check health status
docker compose ps

# Manual health check
docker compose exec lottery-predictor python -c "from src.predictor.constants import RiskLevel; sys.exit(0)"
```

## Key Paths Inside Container

| Path | Purpose |
|------|---------|
| `/app/src` | Source code |
| `/app/config` | Configuration (read-only) |
| `/app/data` | Input data (read-only) |
| `/app/models` | Saved models (writable) |
| `/app/outputs` | Results (writable) |
| `/app/logs` | Logs (writable) |
| `/app/cli.py` | Main CLI script |

## Troubleshooting

| Issue | Solution |
|-------|----------|
| Build fails | Check logs: `docker build -t test .` (verbose output) |
| Container exits | Check logs: `docker compose logs lottery-predictor` |
| Health check fails | `docker compose exec lottery-predictor python -c "import src"` |
| Out of memory | Increase in docker-compose.yml `memory:` limit |
| Slow builds | Clear cache: `docker builder prune` |
| Port conflict | Change port in docker-compose.yml |

---

**For detailed help:** See `DOCKER_SETUP.md`

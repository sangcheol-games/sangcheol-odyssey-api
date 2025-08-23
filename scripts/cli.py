import asyncio
import sys
import alembic.config
import uvicorn

def start_dev_server() -> None:
    uvicorn.run("app.main:app", host="0.0.0.0", port=8000, reload=True)

def start_prod_server() -> None:
    uvicorn.run("app.main:app", host="0.0.0.0", port=8000)

def run_migrations() -> None:
    alembic.config.main(argv=["upgrade", "head"])

def rollback_migration() -> None:
    alembic.config.main(argv=["downgrade", "-1"])

def create_migration() -> None:
    if len(sys.argv) < 2:
        print("Error: Migration message is required")
        print('Usage: migrate-create "your migration message"')
        sys.exit(1)
    message = sys.argv[1]
    alembic.config.main(argv=["revision", "--autogenerate", "-m", message])

async def init_db() -> None:
    alembic.config.main(argv=["upgrade", "head"])

def initialize_db() -> None:
    asyncio.run(init_db())

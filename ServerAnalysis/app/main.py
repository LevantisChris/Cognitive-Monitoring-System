from contextlib import asynccontextmanager

import sys
import os


from fastapi.middleware.cors import CORSMiddleware
from fastapi import FastAPI
from app.api.routes import router as api_router
import logging

from app.local_database.connection import create_tables, drop_tables

# Configure logging with colors
class ColoredFormatter(logging.Formatter):
    """Custom formatter to add colors to log levels."""
    
    # ANSI color codes
    COLORS = {
        'DEBUG': '\033[36m',    # Cyan
        'INFO': '\033[37m',     # White
        'WARNING': '\033[33m',  # Yellow
        'ERROR': '\033[91m',    # Red
        'CRITICAL': '\033[95m', # Magenta
    }
    RESET = '\033[0m'  # Reset to default color
    
    def format(self, record):
        # Get the original formatted message
        original_format = super().format(record)
        
        # Add color based on log level
        level_name = record.levelname
        if level_name in self.COLORS:
            colored_message = f"{self.COLORS[level_name]}{original_format}{self.RESET}"
            return colored_message
        return original_format

# Create colored formatter
formatter = ColoredFormatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')

# Configure root logger
root_logger = logging.getLogger()
root_logger.setLevel(logging.INFO)

# Remove default handlers
for handler in root_logger.handlers[:]:
    root_logger.removeHandler(handler)

console_handler = logging.StreamHandler()

if sys.stdout.isatty() or os.getenv('FORCE_COLOR'):
    console_handler.setFormatter(formatter)
else:
    plain_formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    console_handler.setFormatter(plain_formatter)

root_logger.addHandler(console_handler)

logger = logging.getLogger(__name__)

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Startup event to initialize services."""
    try:
        create_tables()
        pass
    except Exception as e:
        logger.error(f"Error creating database tables: {e}")
    yield
    logger.info("Shutting down application...")
    drop_tables()

app = FastAPI(
    title="LogMyself & LogBoard API",
    description="Analysis API for LogMyself & LogBoard",
    version="0.1.0",
    lifespan=lifespan
)

# TODO: In production, this should be limited to the allowed origins
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include API routes
app.include_router(api_router, prefix="/api")

@app.get("/")
def health_check():
    return {"message": "I am alive", "status": "healthy"}
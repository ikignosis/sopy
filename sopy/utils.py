import logging
from pathlib import Path

def setup_logging():
    """Set up logging configuration."""
    # Create logs directory if it doesn't exist
    logs_dir = Path("logs")
    logs_dir.mkdir(exist_ok=True)
    
    # Configure logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler(logs_dir / "server.log"),
            logging.StreamHandler()  # Also log to console
        ]
    )
    
    return logging.getLogger(__name__)
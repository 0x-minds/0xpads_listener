"""
📝 Logger Configuration
Loguru configuration
"""
import sys
from loguru import logger
from ..config.settings import get_settings

def setup_logging():
    """Setup loguru logging"""
    settings = get_settings().logging
    
    # Remove default logger
    logger.remove()
    
    # Add console logger
    logger.add(
        sys.stdout,
        format=settings.format,
        level=settings.level,
        colorize=True
    )
    
    # Add file logger
    logger.add(
        settings.file_path,
        format=settings.format,
        level=settings.level,
        rotation=settings.max_file_size,
        retention=settings.backup_count
    )
    
    logger.info("📝 Logging configured")

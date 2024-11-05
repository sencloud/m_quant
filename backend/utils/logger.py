import logging
import sys
from pathlib import Path
from datetime import datetime

def setup_logging(log_dir='logs'):
    """Setup logging configuration"""
    log_dir = Path(log_dir)
    log_dir.mkdir(exist_ok=True)
    
    # Create log filename with timestamp
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    log_file = log_dir / f'backtesting_{timestamp}.log'
    
    # Configure logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s [%(levelname)s] %(name)s: %(message)s',
        handlers=[
            logging.FileHandler(log_file),
            logging.StreamHandler(sys.stdout)
        ]
    )
    
    # Add custom logging levels for strategy events
    logging.addLevelName(25, 'STRATEGY')
    logging.Logger.strategy = lambda self, message, *args, **kwargs: \
        self.log(25, message, *args, **kwargs)
    
    return logging.getLogger(__name__)
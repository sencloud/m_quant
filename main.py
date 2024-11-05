from backend.web.app import create_app
from backend.utils.logger import setup_logging
from backend.database.schema import init_db
import logging

if __name__ == '__main__':
    # Setup logging
    logger = setup_logging()
    logger.info("Starting Stock Backtesting System")
    
    try:
        # Initialize database
        init_db()
        logger.info("Database initialized successfully")
        
        # Create and run Flask application
        app = create_app()
        app.run(debug=False)
        
    except Exception as e:
        logger.error(f"Application startup failed: {str(e)}")
        raise

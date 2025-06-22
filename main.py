import os
import logging
from app import create_app, db
from app.email_service import EmailService

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

logger = logging.getLogger(__name__)

# Create Flask app
app = create_app()

# Initialize email service
email_service = None

def initialize_services(app):
    """Initialize services for the application"""
    global email_service
    
    try:
        # Create database tables
        db.create_all()
        logger.info("Database tables created")
        
        # Initialize email service
        email_service = EmailService()
        
        # Start monitoring emails automatically
        email_service.start_monitoring()
        logger.info("Email monitoring started automatically")
        
    except Exception as e:
        logger.error(f"Error initializing services: {str(e)}")
        raise

if __name__ == '__main__':
    with app.app_context():
        initialize_services(app)
    app.run(host='0.0.0.0', port=5000, debug=True)

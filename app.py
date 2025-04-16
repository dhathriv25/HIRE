from flask import Flask, render_template, request, redirect, url_for
from db_setup import db
import os
import logging
from logging.handlers import RotatingFileHandler
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Initialize Flask app
app = Flask(__name__)
app.config['SECRET_KEY'] = os.getenv('SECRET_KEY', 'hire-platform-secret-key')
app.config['SQLALCHEMY_DATABASE_URI'] = os.getenv('DATABASE_URI', 'sqlite:///hire.db')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# Add to existing app.py after initializing the app

# Initialize SQLAlchemy with the app
db.init_app(app)

# Add context processor to make environment variables available to templates
@app.context_processor
def inject_env_variables():
    return dict(
        GOOGLE_MAPS_API_KEY=os.getenv('GOOGLE_MAPS_API_KEY')
    )

# Configure logging
if not os.path.exists('logs'):
    os.mkdir('logs')

file_handler = RotatingFileHandler('logs/hire_platform.log', maxBytes=10240, backupCount=10)
file_handler.setFormatter(logging.Formatter(
    '%(asctime)s %(levelname)s: %(message)s [in %(pathname)s:%(lineno)d]'
))
file_handler.setLevel(logging.INFO)

app.logger.addHandler(file_handler)
app.logger.setLevel(logging.INFO)
app.logger.info('HIRE Platform startup')

# Import models after initializing db
from models import (
    Customer, Provider, ServiceCategory, 
    ProviderCategory, Address, Booking, 
    Payment, OTPVerification
)

# Function to initialize database
def init_db():
    """Create database tables and add initial data"""
    app.logger.info('Creating database tables')
    
    # Add initial service categories if none exist
    if ServiceCategory.query.count() == 0:
        app.logger.info('Adding initial service categories')
        categories = [
            ServiceCategory(name="Plumbing", description="All plumbing services including repairs, installations, and maintenance"),
            ServiceCategory(name="Electrical", description="Electrical repairs, installations, and maintenance services"),
            ServiceCategory(name="Cleaning", description="Professional home cleaning services including regular cleaning, deep cleaning, and specialized cleaning"),
            ServiceCategory(name="Carpentry", description="Woodwork, furniture repairs, and custom woodworking services"),
            ServiceCategory(name="Painting", description="Interior and exterior painting services for homes and businesses"),
            ServiceCategory(name="Landscaping", description="Garden maintenance, lawn care, and landscaping design services"),
            ServiceCategory(name="HVAC", description="Heating, ventilation, and air conditioning installation and repairs")
        ]
        db.session.add_all(categories)
        db.session.commit()
        app.logger.info(f'Added {len(categories)} initial service categories')

# Initialize database
with app.app_context():
    db.create_all()
    init_db()



# Register blueprints
from routes import (
    main_bp, customer_bp, provider_bp, 
    service_bp, booking_bp, payment_bp
)

# Register blueprints with their prefixes
app.register_blueprint(main_bp)
app.register_blueprint(customer_bp, url_prefix='/customer')
app.register_blueprint(provider_bp, url_prefix='/provider')
app.register_blueprint(service_bp, url_prefix='/services')
app.register_blueprint(booking_bp, url_prefix='/booking')
app.register_blueprint(payment_bp, url_prefix='/payment')

# Error handlers
@app.errorhandler(404)
def not_found_error(error):
    app.logger.info(f'404 error: {request.url}')
    return render_template('errors/404.html'), 404

@app.errorhandler(500)
def internal_error(error):
    app.logger.error(f'500 error: {str(error)}')
    db.session.rollback()  # Roll back session in case of database error
    return render_template('errors/500.html'), 500

@app.errorhandler(403)
def forbidden_error(error):
    app.logger.info(f'403 error: {request.url}')
    return render_template('errors/403.html'), 403

@app.context_processor
def utility_processor():
    """Add utility functions to Jinja templates"""
    def format_datetime(value, format='%d %b, %Y %H:%M'):
        """Format a datetime object to string"""
        if value is None:
            return ""
        return value.strftime(format)
    
    def format_currency(value):
        """Format a number as currency"""
        if value is None:
            return "€0.00"
        return f"€{value:.2f}"
    
    return dict(
        format_datetime=format_datetime,
        format_currency=format_currency
    )

if __name__ == '__main__':
    app.run(debug=os.getenv('FLASK_DEBUG', 'False').lower() == 'true', host='0.0.0.0', port=int(os.getenv('PORT', 5000)))
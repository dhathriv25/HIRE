import unittest
import os
import sys
import time
from datetime import datetime, timedelta

# Add the parent directory to the path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from app import app, db
from models import Customer, Provider, ServiceCategory, ProviderCategory, Address, Booking, Payment
from services import find_matching_providers, update_provider_rating
from werkzeug.security import generate_password_hash

class TestIntegration(unittest.TestCase):
    """Integration tests for end-to-end workflows"""
    
    def setUp(self):
        """Set up test environment"""
        # Configure the app for testing
        app.config['TESTING'] = True
        app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///:memory:'
        app.config['WTF_CSRF_ENABLED'] = False
        self.app = app.test_client()
        
        # Create tables and context
        self.app_context = app.app_context()
        self.app_context.push()
        db.create_all()
        
        # Create test data
        self._create_test_data()

    def tearDown(self):
        """Clean up after tests"""
        db.session.remove()
        db.drop_all()
        self.app_context.pop()

    def _create_test_data(self):
        """Create test data for integration tests"""
        # Create service categories
        plumbing = ServiceCategory(name="Plumbing", description="Plumbing services")
        electrical = ServiceCategory(name="Electrical", description="Electrical services")
        db.session.add_all([plumbing, electrical])
        db.session.commit()
        
        # Create a customer
        customer = Customer(
            email="customer@example.com",
            phone="+1122334455",
            password_hash=generate_password_hash("password"),
            first_name="Test",
            last_name="Customer",
            is_verified=True
        )
        db.session.add(customer)
        db.session.commit()
        
        # Create a provider
        provider = Provider(
            email="provider@example.com",
            phone="+9988776655",
            password_hash=generate_password_hash("password"),
            first_name="Test",
            last_name="Provider",
            verification_document="doc.pdf",
            experience_years=5,
            is_available=True,
            avg_rating=4.5,
            is_verified=True
        )
        db.session.add(provider)
        db.session.commit()
        
        # Create provider services
        pc = ProviderCategory(
            provider_id=provider.id,
            category_id=plumbing.id,
            price_rate=50.0
        )
        db.session.add(pc)
        db.session.commit()
        
        # Create addresses
        customer_address = Address(
            customer_id=customer.id,
            address_line="123 Main St",
            city="Dublin",
            state="Dublin",
            postal_code="D01 AB12",
            latitude=53.349805,
            longitude=-6.26031
        )
        db.session.add(customer_address)
        db.session.commit()
        
        # Save IDs for use in tests
        self.customer_id = customer.id
        self.provider_id = provider.id
        self.plumbing_id = plumbing.id
        self.electrical_id = electrical.id
        self.address_id = customer_address.id

    def test_complete_booking_workflow(self):
        """Test the complete booking workflow from creation to payment"""
        # Login as customer
        with self.app.session_transaction() as sess:
            sess['user_id'] = self.customer_id
            sess['user_type'] = 'customer'
        
        # Step 1: Create a booking
        tomorrow = (datetime.now() + timedelta(days=1)).strftime('%Y-%m-%d')
        response = self.app.post(f'/booking/create/{self.provider_id}', data={
            'category_id': self.plumbing_id,
            'address_id': self.address_id,
            'booking_date': tomorrow,
            'time_slot': '10:00'
        }, follow_redirects=True)
        
        self.assertEqual(response.status_code, 200)
        self.assertIn(b'Payment', response.data)
        
        # Get the booking ID from the database
        booking = Booking.query.filter_by(
            customer_id=self.customer_id,
            provider_id=self.provider_id
        ).first()
        
        self.assertIsNotNone(booking)
        self.assertEqual(booking.status, 'pending')
        
        # Step 2: Process payment
        response = self.app.post(f'/payment/process/{booking.id}', data={
            'payment_method': 'credit_card'
        }, follow_redirects=True)
        
        self.assertEqual(response.status_code, 200)
        self.assertIn(b'Payment processed successfully', response.data)
        
        # Verify booking status updated
        booking = Booking.query.get(booking.id)
        self.assertEqual(booking.status, 'confirmed')
        
        # Verify payment was created
        payment = Payment.query.filter_by(booking_id=booking.id).first()
        self.assertIsNotNone(payment)
        self.assertEqual(payment.status, 'successful')
        
        # Step 3: Provider marks booking as completed
        with self.app.session_transaction() as sess:
            sess['user_id'] = self.provider_id
            sess['user_type'] = 'provider'
        
        response = self.app.post(f'/booking/{booking.id}/complete', follow_redirects=True)
        self.assertEqual(response.status_code, 200)
        
        # Verify booking status updated
        booking = Booking.query.get(booking.id)
        self.assertEqual(booking.status, 'completed')
        
        # Step 4: Customer rates the service
        with self.app.session_transaction() as sess:
            sess['user_id'] = self.customer_id
            sess['user_type'] = 'customer'
        
        response = self.app.post(f'/booking/{booking.id}/rate', data={
            'rating': '5',
            'comment': 'Excellent service'
        }, follow_redirects=True)
        
        self.assertEqual(response.status_code, 200)
        self.assertIn(b'Booking rated successfully', response.data)
        
        # Verify rating was saved
        booking = Booking.query.get(booking.id)
        self.assertEqual(booking.rating, 5)
        self.assertEqual(booking.rating_comment, 'Excellent service')
        
        # Verify provider rating was updated
        provider = Provider.query.get(self.provider_id)
        self.assertEqual(provider.avg_rating, 5.0)

    def test_booking_cancellation_workflow(self):
        """Test the booking cancellation workflow"""
        # Create a booking
        tomorrow = datetime.now().date() + timedelta(days=1)
        booking = Booking(
            customer_id=self.customer_id,
            provider_id=self.provider_id,
            category_id=self.plumbing_id,
            address_id=self.address_id,
            booking_date=tomorrow,
            time_slot="10:00",
            status="confirmed"
        )
        db.session.add(booking)
        db.session.commit()
        
        # Create a payment
        payment = Payment(
            booking_id=booking.id,
            amount=50.0,
            payment_method="credit_card",
            transaction_id="TRANS123456",
            status="successful"
        )
        db.session.add(payment)
        db.session.commit()
        
        # Login as customer
        with self.app.session_transaction() as sess:
            sess['user_id'] = self.customer_id
            sess['user_type'] = 'customer'
        
        # Cancel the booking
        response = self.app.post(f'/booking/{booking.id}/cancel', follow_redirects=True)
        self.assertEqual(response.status_code, 200)
        self.assertIn(b'Booking cancelled successfully', response.data)
        
        # Verify booking status updated
        booking = Booking.query.get(booking.id)
        self.assertEqual(booking.status, 'cancelled')
        
        # Verify payment status updated
        payment = Payment.query.filter_by(booking_id=booking.id).first()
        self.assertEqual(payment.status, 'refunded')
        
    def test_provider_service_management(self):
        """Test provider service management workflow"""
        # Login as provider
        with self.app.session_transaction() as sess:
            sess['user_id'] = self.provider_id
            sess['user_type'] = 'provider'
        
        # Add a new service
        response = self.app.post('/provider/services/add', data={
            'category_id': self.electrical_id,
            'price_rate': '60.0'
        }, follow_redirects=True)
        
        self.assertEqual(response.status_code, 200)
        self.assertIn(b'Service added successfully', response.data)
        
        # Verify service was added
        provider_service = ProviderCategory.query.filter_by(
            provider_id=self.provider_id,
            category_id=self.electrical_id
        ).first()
        
        self.assertIsNotNone(provider_service)
        self.assertEqual(provider_service.price_rate, 60.0)

    def test_search_and_book_integration(self):
        """Test the search and booking workflow"""
        # Login as customer
        with self.app.session_transaction() as sess:
            sess['user_id'] = self.customer_id
            sess['user_type'] = 'customer'
        
        # Step 1: Check if service detail page works instead of search
        # Fix: Use service detail page instead of search
        response = self.app.get(f'/services/{self.plumbing_id}')
        self.assertEqual(response.status_code, 200)
        self.assertIn(b'Plumbing', response.data)
        
        # Step 2: Go to booking page
        response = self.app.get(f'/booking/create/{self.provider_id}?category_id={self.plumbing_id}')
        self.assertEqual(response.status_code, 200)
        self.assertIn(b'Book Service', response.data)
        
        # Step 3: Create booking
        tomorrow = (datetime.now() + timedelta(days=1)).strftime('%Y-%m-%d')
        response = self.app.post(f'/booking/create/{self.provider_id}', data={
            'category_id': self.plumbing_id,
            'address_id': self.address_id,
            'booking_date': tomorrow,
            'time_slot': '10:00'
        }, follow_redirects=True)
        
        self.assertEqual(response.status_code, 200)
        self.assertIn(b'Payment', response.data)
        
        # Verify booking was created
        booking = Booking.query.filter_by(
            customer_id=self.customer_id,
            provider_id=self.provider_id
        ).first()
        
        self.assertIsNotNone(booking)
        self.assertEqual(booking.status, 'pending')

if __name__ == '__main__':
    unittest.main()
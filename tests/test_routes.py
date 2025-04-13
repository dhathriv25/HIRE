import unittest
import os
import sys
import json
from datetime import datetime, timedelta

# Add the parent directory to the path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from app import app, db
from models import Customer, Provider, ServiceCategory, ProviderCategory, Address, Booking, Payment, OTPVerification
from werkzeug.security import generate_password_hash

class TestRoutes(unittest.TestCase):
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
        """Create test data for the routes tests"""
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

    def test_index_route(self):
        """Test the index route"""
        response = self.app.get('/')
        self.assertEqual(response.status_code, 200)
        self.assertIn(b'Welcome to HIRE', response.data)
        
    def test_customer_login_route(self):
        """Test the customer login route"""
        # Test GET request
        response = self.app.get('/customer/login')
        self.assertEqual(response.status_code, 200)
        self.assertIn(b'Customer Login', response.data)
        
        # Test POST request with valid credentials
        response = self.app.post('/customer/login', data={
            'email': 'customer@example.com',
            'password': 'password'
        }, follow_redirects=True)
        self.assertEqual(response.status_code, 200)
        self.assertIn(b'You are now logged in', response.data)
        
        # Test POST request with invalid credentials
        response = self.app.post('/customer/login', data={
            'email': 'customer@example.com',
            'password': 'wrongpassword'
        }, follow_redirects=True)
        self.assertEqual(response.status_code, 200)
        self.assertIn(b'Invalid email or password', response.data)

    def test_provider_login_route(self):
        """Test the provider login route"""
        # Test GET request
        response = self.app.get('/provider/login')
        self.assertEqual(response.status_code, 200)
        self.assertIn(b'Provider Login', response.data)
        
        # Test POST request with valid credentials
        response = self.app.post('/provider/login', data={
            'email': 'provider@example.com',
            'password': 'password'
        }, follow_redirects=True)
        self.assertEqual(response.status_code, 200)
        self.assertIn(b'You are now logged in', response.data)
        
        # Test POST request with invalid credentials
        response = self.app.post('/provider/login', data={
            'email': 'provider@example.com',
            'password': 'wrongpassword'
        }, follow_redirects=True)
        self.assertEqual(response.status_code, 200)
        self.assertIn(b'Invalid email or password', response.data)

    def test_logout_route(self):
        """Test the logout route"""
        # Login first
        with self.app.session_transaction() as sess:
            sess['user_id'] = self.customer_id
            sess['user_type'] = 'customer'
        
        # Test logout
        response = self.app.get('/logout', follow_redirects=True)
        self.assertEqual(response.status_code, 200)
        self.assertIn(b'You have been logged out', response.data)

    def test_service_list_route(self):
        """Test the service list route"""
        response = self.app.get('/services/')
        self.assertEqual(response.status_code, 200)
        self.assertIn(b'Our Services', response.data)
        self.assertIn(b'Plumbing', response.data)
        self.assertIn(b'Electrical', response.data)

    def test_service_detail_route(self):
        """Test the service detail route"""
        response = self.app.get(f'/services/{self.plumbing_id}')
        self.assertEqual(response.status_code, 200)
        self.assertIn(b'Plumbing', response.data)
        
        # Test with non-existent service
        response = self.app.get('/services/9999')
        self.assertEqual(response.status_code, 404)

    def test_customer_dashboard_route(self):
        """Test the customer dashboard route"""
        # Login first
        with self.app.session_transaction() as sess:
            sess['user_id'] = self.customer_id
            sess['user_type'] = 'customer'
        
        response = self.app.get('/customer/dashboard')
        self.assertEqual(response.status_code, 200)
        self.assertIn(b'Welcome', response.data)
        self.assertIn(b'My Bookings', response.data)
        
        # Test unauthorized access
        with self.app.session_transaction() as sess:
            sess.clear()
        
        response = self.app.get('/customer/dashboard', follow_redirects=True)
        self.assertEqual(response.status_code, 200)
        self.assertIn(b'Please log in as a customer', response.data)

    def test_provider_dashboard_route(self):
        """Test the provider dashboard route"""
        # Login first
        with self.app.session_transaction() as sess:
            sess['user_id'] = self.provider_id
            sess['user_type'] = 'provider'
        
        response = self.app.get('/provider/dashboard')
        self.assertEqual(response.status_code, 200)
        self.assertIn(b'Welcome', response.data)
        self.assertIn(b'My Bookings', response.data)
        
        # Test unauthorized access
        with self.app.session_transaction() as sess:
            sess.clear()
        
        response = self.app.get('/provider/dashboard', follow_redirects=True)
        self.assertEqual(response.status_code, 200)
        self.assertIn(b'Please log in as a provider', response.data)

    def test_add_address_route(self):
        """Test the add address route"""
        # Login first
        with self.app.session_transaction() as sess:
            sess['user_id'] = self.customer_id
            sess['user_type'] = 'customer'
        
        # Test GET request
        response = self.app.get('/customer/address/add')
        self.assertEqual(response.status_code, 200)
        self.assertIn(b'Add New Address', response.data)
        
        # Test POST request
        response = self.app.post('/customer/address/add', data={
            'address_line': '456 New St',
            'city': 'Dublin',
            'state': 'Dublin',
            'postal_code': 'D02 CD34',
            'latitude': '53.350140',
            'longitude': '-6.266155'
        }, follow_redirects=True)
        self.assertEqual(response.status_code, 200)
        self.assertIn(b'Address added successfully', response.data)
        
        # Verify address was added
        address = Address.query.filter_by(address_line='456 New St').first()
        self.assertIsNotNone(address)
        self.assertEqual(address.customer_id, self.customer_id)

    def test_create_booking_route(self):
        """Test the create booking route"""
        # Login first
        with self.app.session_transaction() as sess:
            sess['user_id'] = self.customer_id
            sess['user_type'] = 'customer'
        
        # Test GET request
        response = self.app.get(f'/booking/create/{self.provider_id}')
        self.assertEqual(response.status_code, 200)
        self.assertIn(b'Book Service', response.data)
        
        # Test POST request
        tomorrow = (datetime.now() + timedelta(days=1)).strftime('%Y-%m-%d')
        response = self.app.post(f'/booking/create/{self.provider_id}', data={
            'category_id': self.plumbing_id,
            'address_id': self.address_id,
            'booking_date': tomorrow,
            'time_slot': '10:00'
        }, follow_redirects=True)
        self.assertEqual(response.status_code, 200)
        self.assertIn(b'Payment', response.data)  # Should redirect to payment page
        
        # Verify booking was created
        booking = Booking.query.filter_by(
            customer_id=self.customer_id,
            provider_id=self.provider_id,
            category_id=self.plumbing_id
        ).first()
        self.assertIsNotNone(booking)
        self.assertEqual(booking.status, 'pending')

    def test_payment_process_route(self):
        """Test the payment process route"""
        # Create a booking first
        booking = Booking(
            customer_id=self.customer_id,
            provider_id=self.provider_id,
            category_id=self.plumbing_id,
            address_id=self.address_id,
            booking_date=datetime.now().date() + timedelta(days=1),
            time_slot="10:00",
            status="pending"
        )
        db.session.add(booking)
        db.session.commit()
        
        # Login
        with self.app.session_transaction() as sess:
            sess['user_id'] = self.customer_id
            sess['user_type'] = 'customer'
        
        # Test GET request
        response = self.app.get(f'/payment/process/{booking.id}')
        self.assertEqual(response.status_code, 200)
        self.assertIn(b'Payment', response.data)
        
        # Test POST request
        response = self.app.post(f'/payment/process/{booking.id}', data={
            'payment_method': 'credit_card'
        }, follow_redirects=True)
        self.assertEqual(response.status_code, 200)
        self.assertIn(b'Payment processed successfully', response.data)
        
        # Verify payment was created and booking status updated
        payment = Payment.query.filter_by(booking_id=booking.id).first()
        self.assertIsNotNone(payment)
        self.assertEqual(payment.status, 'successful')
        
        booking = Booking.query.get(booking.id)
        self.assertEqual(booking.status, 'confirmed')

    def test_booking_detail_route(self):
        """Test the booking detail route"""
        # Create a booking
        booking = Booking(
            customer_id=self.customer_id,
            provider_id=self.provider_id,
            category_id=self.plumbing_id,
            address_id=self.address_id,
            booking_date=datetime.now().date() + timedelta(days=1),
            time_slot="10:00",
            status="confirmed"
        )
        db.session.add(booking)
        db.session.commit()
        
        # Login as customer
        with self.app.session_transaction() as sess:
            sess['user_id'] = self.customer_id
            sess['user_type'] = 'customer'
        
        # Test detail view
        response = self.app.get(f'/booking/{booking.id}')
        self.assertEqual(response.status_code, 200)
        self.assertIn(b'Booking Details', response.data)
        self.assertIn(b'Confirmed', response.data)
        
        # Test unauthorized access (different customer)
        new_customer = Customer(
            email="other@example.com",
            phone="+5544332211",
            password_hash=generate_password_hash("password"),
            first_name="Other",
            last_name="Customer",
            is_verified=True
        )
        db.session.add(new_customer)
        db.session.commit()
        
        with self.app.session_transaction() as sess:
            sess['user_id'] = new_customer.id
            sess['user_type'] = 'customer'
        
        response = self.app.get(f'/booking/{booking.id}', follow_redirects=True)
        self.assertEqual(response.status_code, 200)
        self.assertIn(b'You are not authorized to view this booking', response.data)

    def test_add_service_route(self):
        """Test the add service route for providers"""
        # Login as provider
        with self.app.session_transaction() as sess:
            sess['user_id'] = self.provider_id
            sess['user_type'] = 'provider'
        
        # Test GET request
        response = self.app.get('/provider/services/add')
        self.assertEqual(response.status_code, 200)
        self.assertIn(b'Add New Service', response.data)
        
        # Test POST request to add electrical service
        response = self.app.post('/provider/services/add', data={
            'category_id': self.electrical_id,
            'price_rate': '60.0'
        }, follow_redirects=True)
        self.assertEqual(response.status_code, 200)
        self.assertIn(b'Service added successfully', response.data)
        
        # Verify service was added
        provider_category = ProviderCategory.query.filter_by(
            provider_id=self.provider_id,
            category_id=self.electrical_id
        ).first()
        self.assertIsNotNone(provider_category)
        self.assertEqual(provider_category.price_rate, 60.0)

    def test_customer_registration_route(self):
        """Test customer registration route"""
        # Test GET request
        response = self.app.get('/customer/register')
        self.assertEqual(response.status_code, 200)
        self.assertIn(b'Customer Registration', response.data)
        
        # Test POST request with valid data
        # Using email with test domain to avoid actual OTP sending
        response = self.app.post('/customer/register', data={
            'first_name': 'New',
            'last_name': 'Customer',
            'email': 'new.customer@test.com',
            'phone': '+1234567890',
            'password': 'password',
            'confirm_password': 'password',
            'terms': 'on'
        }, follow_redirects=True)
        
        # We should be redirected to OTP verification page
        self.assertEqual(response.status_code, 200)
        self.assertIn(b'Verification', response.data)
        
        # Verify customer was created
        customer = Customer.query.filter_by(email='new.customer@test.com').first()
        self.assertIsNotNone(customer)
        self.assertEqual(customer.first_name, 'New')
        self.assertEqual(customer.last_name, 'Customer')
        
        # Test with existing email
        response = self.app.post('/customer/register', data={
            'first_name': 'Duplicate',
            'last_name': 'Customer',
            'email': 'customer@example.com',  # Existing email
            'phone': '+9876543210',
            'password': 'password',
            'confirm_password': 'password',
            'terms': 'on'
        }, follow_redirects=True)
        
        self.assertEqual(response.status_code, 200)
        self.assertIn(b'Email already registered', response.data)

if __name__ == '__main__':
    unittest.main()
import unittest
import os
import sys
from datetime import datetime, timedelta

# Add the parent directory to the path .......
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from app import app, db
from models import Customer, Provider, ServiceCategory, ProviderCategory, Address, Booking, Payment, OTPVerification

class TestModels(unittest.TestCase):
    def setUp(self):
        """Set up test environment"""
        # Configure the app for testing
        app.config['TESTING'] = True
        app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///:memory:'
        app.config['WTF_CSRF_ENABLED'] = False

        # Create tables and context
        self.app_context = app.app_context()
        self.app_context.push()
        db.create_all()

    def tearDown(self):
        """Clean up after tests"""
        db.session.remove()
        db.drop_all()
        self.app_context.pop()

    def test_customer_model(self):
        """Test Customer model"""
        # Create a customer
        customer = Customer(
            email="test@example.com",
            phone="+1234567890",
            password_hash="hashvalue",
            first_name="Test",
            last_name="User",
            is_verified=True
        )
        db.session.add(customer)
        db.session.commit()

        # Test retrieval
        retrieved_customer = Customer.query.filter_by(email="test@example.com").first()
        self.assertIsNotNone(retrieved_customer)
        self.assertEqual(retrieved_customer.email, "test@example.com")
        self.assertEqual(retrieved_customer.phone, "+1234567890")
        self.assertEqual(retrieved_customer.first_name, "Test")
        self.assertEqual(retrieved_customer.last_name, "User")
        self.assertTrue(retrieved_customer.is_verified)

        # Test get_full_name method
        self.assertEqual(retrieved_customer.get_full_name(), "Test User")

    def test_provider_model(self):
        """Test Provider model"""
        # Create a provider
        provider = Provider(
            email="provider@example.com",
            phone="+9876543210",
            password_hash="hashvalue",
            first_name="Provider",
            last_name="Test",
            verification_document="doc.pdf",
            experience_years=5,
            is_available=True,
            avg_rating=4.5,
            is_verified=True
        )
        db.session.add(provider)
        db.session.commit()

        # Test retrieval
        retrieved_provider = Provider.query.filter_by(email="provider@example.com").first()
        self.assertIsNotNone(retrieved_provider)
        self.assertEqual(retrieved_provider.email, "provider@example.com")
        self.assertEqual(retrieved_provider.experience_years, 5)
        self.assertEqual(retrieved_provider.avg_rating, 4.5)

        # Test get_full_name method
        self.assertEqual(retrieved_provider.get_full_name(), "Provider Test")

    def test_service_category_model(self):
        """Test ServiceCategory model"""
        # Create a service category
        category = ServiceCategory(
            name="Plumbing",
            description="Plumbing services"
        )
        db.session.add(category)
        db.session.commit()

        # Test retrieval
        retrieved_category = ServiceCategory.query.filter_by(name="Plumbing").first()
        self.assertIsNotNone(retrieved_category)
        self.assertEqual(retrieved_category.name, "Plumbing")
        self.assertEqual(retrieved_category.description, "Plumbing services")

    def test_provider_category_relationship(self):
        """Test ProviderCategory relationship"""
        # Create a provider
        provider = Provider(
            email="provider@example.com",
            phone="+9876543210",
            password_hash="hashvalue",
            first_name="Provider",
            last_name="Test",
            verification_document="doc.pdf",
            experience_years=5,
            is_available=True,
            is_verified=True
        )
        
        # Create a service category
        category = ServiceCategory(
            name="Plumbing",
            description="Plumbing services"
        )
        
        db.session.add_all([provider, category])
        db.session.commit()
        
        # Create a provider-category relationship
        provider_category = ProviderCategory(
            provider_id=provider.id,
            category_id=category.id,
            price_rate=50.0
        )
        db.session.add(provider_category)
        db.session.commit()
        
        # Test retrieval and relationships
        retrieved_pc = ProviderCategory.query.filter_by(provider_id=provider.id, category_id=category.id).first()
        self.assertIsNotNone(retrieved_pc)
        self.assertEqual(retrieved_pc.price_rate, 50.0)
        
        # Test bidirectional relationship
        self.assertEqual(retrieved_pc.provider, provider)
        self.assertEqual(retrieved_pc.category, category)
        self.assertIn(retrieved_pc, provider.services)
        self.assertIn(retrieved_pc, category.provider_categories)

    def test_address_model(self):
        """Test Address model"""
        # Create a customer
        customer = Customer(
            email="test@example.com",
            phone="+1234567890",
            password_hash="hashvalue",
            first_name="Test",
            last_name="User",
            is_verified=True
        )
        db.session.add(customer)
        db.session.commit()
        
        # Create an address
        address = Address(
            customer_id=customer.id,
            address_line="123 Main St",
            city="Dublin",
            state="Dublin",
            postal_code="D01 AB12",
            latitude=53.349805,
            longitude=-6.26031
        )
        db.session.add(address)
        db.session.commit()
        
        # Test retrieval
        retrieved_address = Address.query.filter_by(customer_id=customer.id).first()
        self.assertIsNotNone(retrieved_address)
        self.assertEqual(retrieved_address.address_line, "123 Main St")
        self.assertEqual(retrieved_address.city, "Dublin")
        
        # Test relationship
        self.assertEqual(retrieved_address.customer, customer)
        self.assertIn(retrieved_address, customer.addresses)
        
        # Test get_full_address method
        expected_full_address = "123 Main St, Dublin, Dublin D01 AB12"
        self.assertEqual(retrieved_address.get_full_address(), expected_full_address)

    def test_booking_model(self):
        """Test Booking model"""
        # Create a customer
        customer = Customer(
            email="test@example.com",
            phone="+1234567890",
            password_hash="hashvalue",
            first_name="Test",
            last_name="User",
            is_verified=True
        )
        
        # Create a provider
        provider = Provider(
            email="provider@example.com",
            phone="+9876543210",
            password_hash="hashvalue",
            first_name="Provider",
            last_name="Test",
            verification_document="doc.pdf",
            experience_years=5,
            is_available=True,
            is_verified=True
        )
        
        # Create a service category
        category = ServiceCategory(
            name="Plumbing",
            description="Plumbing services"
        )
        
        db.session.add_all([customer, provider, category])
        db.session.commit()
        
        # Create an address
        address = Address(
            customer_id=customer.id,
            address_line="123 Main St",
            city="Dublin",
            state="Dublin",
            postal_code="D01 AB12"
        )
        db.session.add(address)
        db.session.commit()
        
        # Create a booking
        booking_date = datetime.now().date() + timedelta(days=1)
        booking = Booking(
            customer_id=customer.id,
            provider_id=provider.id,
            category_id=category.id,
            address_id=address.id,
            booking_date=booking_date,
            time_slot="10:00",
            status="pending"
        )
        db.session.add(booking)
        db.session.commit()
        
        # Test retrieval
        retrieved_booking = Booking.query.filter_by(
            customer_id=customer.id, 
            provider_id=provider.id
        ).first()
        
        self.assertIsNotNone(retrieved_booking)
        self.assertEqual(retrieved_booking.status, "pending")
        self.assertEqual(retrieved_booking.time_slot, "10:00")
        
        # Test relationships
        self.assertEqual(retrieved_booking.customer, customer)
        self.assertEqual(retrieved_booking.provider, provider)
        self.assertEqual(retrieved_booking.category, category)
        self.assertEqual(retrieved_booking.address, address)
        
        self.assertIn(retrieved_booking, customer.bookings)
        self.assertIn(retrieved_booking, provider.bookings)

    def test_payment_model(self):
        """Test Payment model"""
        # Create necessary related models
        customer = Customer(
            email="test@example.com",
            phone="+1234567890",
            password_hash="hashvalue",
            first_name="Test",
            last_name="User",
            is_verified=True
        )
        
        provider = Provider(
            email="provider@example.com",
            phone="+9876543210",
            password_hash="hashvalue",
            first_name="Provider",
            last_name="Test",
            verification_document="doc.pdf",
            experience_years=5,
            is_available=True,
            is_verified=True
        )
        
        category = ServiceCategory(
            name="Plumbing",
            description="Plumbing services"
        )
        
        db.session.add_all([customer, provider, category])
        db.session.commit()
        
        address = Address(
            customer_id=customer.id,
            address_line="123 Main St",
            city="Dublin",
            state="Dublin",
            postal_code="D01 AB12"
        )
        db.session.add(address)
        db.session.commit()
        
        booking_date = datetime.now().date() + timedelta(days=1)
        booking = Booking(
            customer_id=customer.id,
            provider_id=provider.id,
            category_id=category.id,
            address_id=address.id,
            booking_date=booking_date,
            time_slot="10:00",
            status="pending"
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
        
        # Test retrieval
        retrieved_payment = Payment.query.filter_by(booking_id=booking.id).first()
        self.assertIsNotNone(retrieved_payment)
        self.assertEqual(retrieved_payment.amount, 50.0)
        self.assertEqual(retrieved_payment.payment_method, "credit_card")
        self.assertEqual(retrieved_payment.transaction_id, "TRANS123456")
        self.assertEqual(retrieved_payment.status, "successful")
        
        # Test relationship
        self.assertEqual(retrieved_payment.booking, booking)
        self.assertEqual(booking.payment, retrieved_payment)

    def test_otp_verification_model(self):
        """Test OTPVerification model"""
        # Create a customer
        customer = Customer(
            email="test@example.com",
            phone="+1234567890",
            password_hash="hashvalue",
            first_name="Test",
            last_name="User",
            is_verified=False
        )
        db.session.add(customer)
        db.session.commit()
        
        # Create an OTP verification
        otp_expiry = datetime.utcnow() + timedelta(minutes=10)
        otp = OTPVerification(
            user_id=customer.id,
            user_type="customer",
            otp_code="123456",
            expires_at=otp_expiry
        )
        db.session.add(otp)
        db.session.commit()
        
        # Test retrieval
        retrieved_otp = OTPVerification.query.filter_by(
            user_id=customer.id, 
            user_type="customer"
        ).first()
        
        self.assertIsNotNone(retrieved_otp)
        self.assertEqual(retrieved_otp.otp_code, "123456")
        self.assertFalse(retrieved_otp.is_used)
        
        # Test expiry check
        self.assertTrue(retrieved_otp.expires_at > datetime.utcnow())

if __name__ == '__main__':
    unittest.main()

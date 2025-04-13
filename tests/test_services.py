import unittest
import os
import sys
from datetime import datetime, timedelta

# Add the parent directory to the path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from app import app, db
from models import Customer, Provider, ServiceCategory, ProviderCategory, Address, Booking, Payment, OTPVerification
from services import (
    find_matching_providers, generate_otp, verify_otp, update_provider_rating,
    check_booking_conflicts, cancel_booking, validate_booking_data, get_available_time_slots
)

class TestServices(unittest.TestCase):
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

        # Create test data
        self._create_test_data()

    def tearDown(self):
        """Clean up after tests"""
        db.session.remove()
        db.drop_all()
        self.app_context.pop()

    def _create_test_data(self):
        """Create test data for the tests"""
        # Create service categories
        plumbing = ServiceCategory(name="Plumbing", description="Plumbing services")
        electrical = ServiceCategory(name="Electrical", description="Electrical services")
        db.session.add_all([plumbing, electrical])
        db.session.commit()

        # Create providers
        provider1 = Provider(
            email="provider1@example.com",
            phone="+1234567890",
            password_hash="hash1",
            first_name="John",
            last_name="Smith",
            verification_document="doc1.pdf",
            experience_years=5,
            is_available=True,
            avg_rating=4.5,
            is_verified=True
        )
        provider2 = Provider(
            email="provider2@example.com",
            phone="+0987654321",
            password_hash="hash2",
            first_name="Jane",
            last_name="Doe",
            verification_document="doc2.pdf",
            experience_years=3,
            is_available=True,
            avg_rating=4.0,
            is_verified=True
        )
        db.session.add_all([provider1, provider2])
        db.session.commit()

        # Create provider categories (services offered by providers)
        pc1 = ProviderCategory(provider_id=provider1.id, category_id=plumbing.id, price_rate=50.0)
        pc2 = ProviderCategory(provider_id=provider2.id, category_id=plumbing.id, price_rate=45.0)
        pc3 = ProviderCategory(provider_id=provider1.id, category_id=electrical.id, price_rate=60.0)
        db.session.add_all([pc1, pc2, pc3])
        db.session.commit()

        # Create customer
        customer = Customer(
            email="customer@example.com",
            phone="+1122334455",
            password_hash="hash3",
            first_name="Alice",
            last_name="Johnson",
            is_verified=True
        )
        db.session.add(customer)
        db.session.commit()

        # Create addresses with geocoding
        customer_address = Address(
            customer_id=customer.id,
            address_line="123 Main St",
            city="Dublin",
            state="Dublin",
            postal_code="D01 AB12",
            latitude=53.349805,
            longitude=-6.26031
        )
        provider1_address = Address(
            provider_id=provider1.id,
            address_line="456 Oak Ave",
            city="Dublin",
            state="Dublin",
            postal_code="D02 CD34",
            latitude=53.350140,
            longitude=-6.266155
        )
        provider2_address = Address(
            provider_id=provider2.id,
            address_line="789 Pine St",
            city="Dublin",
            state="Dublin",
            postal_code="D03 EF56",
            latitude=53.348750,
            longitude=-6.270000
        )
        db.session.add_all([customer_address, provider1_address, provider2_address])
        db.session.commit()

        # Save IDs for use in tests
        self.plumbing_id = plumbing.id
        self.electrical_id = electrical.id
        self.provider1_id = provider1.id
        self.provider2_id = provider2.id
        self.customer_id = customer.id
        self.customer_address_id = customer_address.id

    def test_find_matching_providers(self):
        """Test the provider matching algorithm"""
        customer_address = Address.query.get(self.customer_address_id)
        
        # Find matching providers for plumbing
        plumbing_providers = find_matching_providers(customer_address, self.plumbing_id)
        
        # Should return both providers as they both offer plumbing
        self.assertEqual(len(plumbing_providers), 2)
        
        # Provider IDs should be in order of rating (higher rating first)
        # Provider 1 has rating 4.5, Provider 2 has rating 4.0
        self.assertEqual(plumbing_providers[0].id, self.provider1_id)
        self.assertEqual(plumbing_providers[1].id, self.provider2_id)
        
        # Find matching providers for electrical
        electrical_providers = find_matching_providers(customer_address, self.electrical_id)
        
        # Should return only provider 1 as provider 2 doesn't offer electrical services
        self.assertEqual(len(electrical_providers), 1)
        self.assertEqual(electrical_providers[0].id, self.provider1_id)

    def test_generate_otp(self):
        """Test OTP generation"""
        # Set OTP_TEST_MODE for testing
        os.environ['OTP_TEST_MODE'] = 'True'
        
        # Generate OTP
        otp_code, error = generate_otp("+1122334455")
        
        # Check that an OTP was generated
        self.assertIsNotNone(otp_code)
        self.assertIsNone(error)
        self.assertEqual(len(otp_code), 6)
        self.assertTrue(otp_code.isdigit())
        
        # Remove test mode setting
        os.environ.pop('OTP_TEST_MODE')

    def test_verify_otp(self):
        """Test OTP verification"""
        # Create an OTP record
        otp_expiry = datetime.utcnow() + timedelta(minutes=10)
        otp_verification = OTPVerification(
            user_id=self.customer_id,
            user_type='customer',
            otp_code='123456',
            expires_at=otp_expiry
        )
        db.session.add(otp_verification)
        db.session.commit()
        
        # Test valid OTP
        self.assertTrue(verify_otp(self.customer_id, '123456', 'customer'))
        
        # Test invalid OTP
        self.assertFalse(verify_otp(self.customer_id, '654321', 'customer'))
        
        # Test expired OTP
        expired_otp = OTPVerification(
            user_id=self.customer_id,
            user_type='customer',
            otp_code='789012',
            expires_at=datetime.utcnow() - timedelta(minutes=1)
        )
        db.session.add(expired_otp)
        db.session.commit()
        self.assertFalse(verify_otp(self.customer_id, '789012', 'customer'))
        
        # Test OTP already used
        used_otp = OTPVerification(
            user_id=self.customer_id,
            user_type='customer',
            otp_code='345678',
            expires_at=otp_expiry,
            is_used=True
        )
        db.session.add(used_otp)
        db.session.commit()
        self.assertFalse(verify_otp(self.customer_id, '345678', 'customer'))

    def test_update_provider_rating(self):
        """Test updating a provider's average rating"""
        # Create bookings with different ratings
        # Create a customer
        customer = Customer.query.get(self.customer_id)
        provider = Provider.query.get(self.provider1_id)
        
        # Create a service category
        category = ServiceCategory.query.get(self.plumbing_id)
        
        # Create an address
        address = Address.query.filter_by(customer_id=self.customer_id).first()
        
        # Create bookings with different ratings
        booking1 = Booking(
            customer_id=customer.id,
            provider_id=provider.id,
            category_id=category.id,
            address_id=address.id,
            booking_date=datetime.utcnow().date(),
            time_slot="10:00",
            status="completed",
            rating=5
        )
        
        booking2 = Booking(
            customer_id=customer.id,
            provider_id=provider.id,
            category_id=category.id,
            address_id=address.id,
            booking_date=datetime.utcnow().date(),
            time_slot="11:00",
            status="completed",
            rating=4
        )
        
        booking3 = Booking(
            customer_id=customer.id,
            provider_id=provider.id,
            category_id=category.id,
            address_id=address.id,
            booking_date=datetime.utcnow().date(),
            time_slot="12:00",
            status="completed",
            rating=3
        )
        
        db.session.add_all([booking1, booking2, booking3])
        db.session.commit()
        
        # Update the provider rating
        avg_rating, count = update_provider_rating(provider.id)
        
        # Check the result
        self.assertEqual(count, 3)
        self.assertEqual(avg_rating, 4.0)  # (5 + 4 + 3) / 3 = 4.0
        
        # Verify the provider's average rating was updated
        provider = Provider.query.get(provider.id)
        self.assertEqual(provider.avg_rating, 4.0)

    def test_check_booking_conflicts(self):
        """Test checking for booking conflicts"""
        # Create a booking
        provider = Provider.query.get(self.provider1_id)
        customer = Customer.query.get(self.customer_id)
        category = ServiceCategory.query.get(self.plumbing_id)
        address = Address.query.filter_by(customer_id=self.customer_id).first()
        
        tomorrow = datetime.utcnow().date() + timedelta(days=1)
        booking = Booking(
            customer_id=customer.id,
            provider_id=provider.id,
            category_id=category.id,
            address_id=address.id,
            booking_date=tomorrow,
            time_slot="10:00-11:00",
            status="confirmed"
        )
        db.session.add(booking)
        db.session.commit()
        
        # Check for conflict at the same time
        conflict = check_booking_conflicts(provider.id, tomorrow, "10:00-11:00")
        self.assertTrue(conflict)
        
        # Check for no conflict at a different time
        no_conflict = check_booking_conflicts(provider.id, tomorrow, "11:00-12:00")
        self.assertFalse(no_conflict)
        
        # Check for no conflict on a different day
        day_after = tomorrow + timedelta(days=1)
        no_conflict_day = check_booking_conflicts(provider.id, day_after, "10:00-11:00")
        self.assertFalse(no_conflict_day)

    def test_cancel_booking(self):
        """Test cancelling a booking"""
        # Create a booking
        provider = Provider.query.get(self.provider1_id)
        customer = Customer.query.get(self.customer_id)
        category = ServiceCategory.query.get(self.plumbing_id)
        address = Address.query.filter_by(customer_id=self.customer_id).first()
        
        # Create a confirmed booking
        booking = Booking(
            customer_id=customer.id,
            provider_id=provider.id,
            category_id=category.id,
            address_id=address.id,
            booking_date=datetime.utcnow().date() + timedelta(days=1),
            time_slot="10:00-11:00",
            status="confirmed"
        )
        db.session.add(booking)
        db.session.commit()
        
        # Create a payment for the booking
        payment = Payment(
            booking_id=booking.id,
            amount=50.0,
            payment_method="credit_card",
            transaction_id="TRANS123456",
            status="successful"
        )
        db.session.add(payment)
        db.session.commit()
        
        # Cancel the booking
        success, error = cancel_booking(booking.id, "Customer requested cancellation")
        
        # Check that cancellation was successful
        self.assertTrue(success)
        self.assertIsNone(error)
        
        # Verify booking status was updated
        booking = Booking.query.get(booking.id)
        self.assertEqual(booking.status, "cancelled")
        
        # Verify payment status was updated to refunded
        payment = Payment.query.filter_by(booking_id=booking.id).first()
        self.assertEqual(payment.status, "refunded")
        
        # Test cancelling a booking that's already completed
        completed_booking = Booking(
            customer_id=customer.id,
            provider_id=provider.id,
            category_id=category.id,
            address_id=address.id,
            booking_date=datetime.utcnow().date() - timedelta(days=1),
            time_slot="10:00-11:00",
            status="completed"
        )
        db.session.add(completed_booking)
        db.session.commit()
        
        # Try to cancel a completed booking
        success, error = cancel_booking(completed_booking.id)
        
        # Check that cancellation was not successful
        self.assertFalse(success)
        self.assertIsNotNone(error)
        
        # Verify booking status was not changed
        completed_booking = Booking.query.get(completed_booking.id)
        self.assertEqual(completed_booking.status, "completed")

    def test_validate_booking_data(self):
        """Test validation of booking data"""
        # Define a tomorrow date for tests
        tomorrow = datetime.utcnow().date() + timedelta(days=1)
        
        # Test valid data
        valid_data = {
            'customer_id': self.customer_id,
            'provider_id': self.provider1_id,
            'category_id': self.plumbing_id,
            'address_id': self.customer_address_id,
            'booking_date': tomorrow,
            'time_slot': '10:00-11:00'
        }
        
        is_valid, errors = validate_booking_data(valid_data)
        self.assertTrue(is_valid)
        self.assertEqual(len(errors), 0)
        
        # Test missing required field
        invalid_data = valid_data.copy()
        invalid_data.pop('time_slot')
        
        is_valid, errors = validate_booking_data(invalid_data)
        self.assertFalse(is_valid)
        self.assertIn('time_slot', errors)
        
        # Test invalid date format
        invalid_date_data = valid_data.copy()
        invalid_date_data['booking_date'] = '2023-13-40'  # Invalid date
        
        is_valid, errors = validate_booking_data(invalid_date_data)
        self.assertFalse(is_valid)
        self.assertIn('booking_date', errors)
        
        # Test past date
        past_date_data = valid_data.copy()
        past_date_data['booking_date'] = datetime.utcnow().date() - timedelta(days=1)
        
        is_valid, errors = validate_booking_data(past_date_data)
        self.assertFalse(is_valid)
        self.assertIn('booking_date', errors)
        
        # Test invalid time slot format
        invalid_time_data = valid_data.copy()
        invalid_time_data['time_slot'] = 'invalid format'
        
        is_valid, errors = validate_booking_data(invalid_time_data)
        self.assertFalse(is_valid)
        self.assertIn('time_slot', errors)

    def test_get_available_time_slots(self):
        """Test getting available time slots for a provider"""
        provider = Provider.query.get(self.provider1_id)
        customer = Customer.query.get(self.customer_id)
        category = ServiceCategory.query.get(self.plumbing_id)
        address = Address.query.filter_by(customer_id=self.customer_id).first()
        
        # Create a booking for tomorrow at 10:00
        tomorrow = datetime.utcnow().date() + timedelta(days=1)
        booking = Booking(
            customer_id=customer.id,
            provider_id=provider.id,
            category_id=category.id,
            address_id=address.id,
            booking_date=tomorrow,
            time_slot="10:00-11:00",
            status="confirmed"
        )
        db.session.add(booking)
        db.session.commit()
        
        # Get available time slots
        available_slots = get_available_time_slots(provider.id, tomorrow)
        
        # Check that the booked slot is not available
        self.assertNotIn("10:00-11:00", available_slots)
        
        # Test when provider is not available
        provider.is_available = False
        db.session.commit()
        
        no_slots = get_available_time_slots(provider.id, tomorrow)
        self.assertEqual(len(no_slots), 0)

if __name__ == '__main__':
    unittest.main()
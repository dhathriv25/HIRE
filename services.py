
from datetime import datetime, timedelta
import os
import random
import requests
from flask import current_app
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Distance calculation and provider scoring functions have been removed as they were non-functional
# and not being used in the application

def find_matching_providers(customer_address, service_category_id, limit=5):
    """
    Find providers for a service request based on availability and rating
    
    Args:
        customer_address: Address object for the customer location (not used)
        service_category_id: ID of the requested service category
        limit: Maximum number of providers to return
        
    Returns:
        List of Provider objects, sorted by rating
    """
    from models import Provider, ProviderCategory
    
    logger.info(f"Finding matching providers for service category {service_category_id}")
    
    # Get all providers for this service category who are verified and available
    provider_categories = ProviderCategory.query.filter_by(category_id=service_category_id).all()
    if not provider_categories:
        logger.info(f"No providers found for service category {service_category_id}")
        return []
    
    # Get provider IDs
    provider_ids = [pc.provider_id for pc in provider_categories]
    
    # Get providers
    providers = Provider.query.filter(
        Provider.id.in_(provider_ids),
        Provider.is_available == True,
        Provider.is_verified == True
    ).all()
    
    if not providers:
        logger.info("No available and verified providers found")
        return []
    
    logger.info(f"Found {len(providers)} potentially matching providers")
    
    # Simply sort providers by rating (highest first)
    sorted_providers = sorted(
        providers,
        key=lambda p: p.avg_rating if p.avg_rating is not None else 0,
        reverse=True
    )
    
    # Return the top matching providers
    top_providers = sorted_providers[:limit]
    logger.info(f"Returning top {len(top_providers)} matching providers")
    
    return top_providers

def generate_otp(phone_number):
    """
    Generate and send OTP via Twilio API with enhanced error handling and fallback options
    
    Args:
        phone_number: User's phone number
        
    Returns:
        (otp_code, error) tuple
        otp_code: Generated OTP code if successful, None otherwise
        error: Error message if OTP sending failed, None otherwise
    """
    import os
    import random
    import logging
    from datetime import datetime
    
    logger = logging.getLogger(__name__)
    logger.info(f"Generating OTP for phone number {phone_number}")
    
    # Generate 6-digit OTP
    otp_code = ''.join(random.choices('0123456789', k=6))
    
    # Check if we're in test/demo mode
    if os.environ.get('OTP_TEST_MODE') == 'True':
        logger.info(f"Test mode enabled. OTP code: {otp_code}")
        # Just return the OTP without sending (for demo/testing)
        return otp_code, None
    
    # Try to import Twilio
    try:
        from twilio.rest import Client
        from twilio.base.exceptions import TwilioRestException, TwilioException
    except ImportError:
        logger.warning("Twilio package not installed. Using test mode.")
        # If Twilio package is not installed, use test mode
        return otp_code, None
    
    # Get Twilio credentials from environment variables
    account_sid = os.environ.get('TWILIO_ACCOUNT_SID')
    auth_token = os.environ.get('TWILIO_AUTH_TOKEN')
    twilio_number = os.environ.get('TWILIO_PHONE_NUMBER')
    
    if not account_sid or not auth_token or not twilio_number:
        logger.error("Twilio credentials not properly configured")
        # Instead of failing, use test mode and inform the user
        logger.info(f"Using test mode instead. OTP code: {otp_code}")
        return otp_code, "Twilio credentials not properly configured. Using test mode instead."
    
    try:
        # Normalize phone number format (E.164 format)
        # E.164 format is +[country code][number], e.g., +353861234567
        if not phone_number.startswith('+'):
            # Add + if missing
            phone_number = '+' + phone_number
            
        # Remove any spaces, dashes, or parentheses
        phone_number = ''.join(c for c in phone_number if c.isdigit() or c == '+')
            
        # Initialize Twilio client
        client = Client(account_sid, auth_token)
        
        # Send OTP via SMS
        message = client.messages.create(
            body=f"Your HIRE Platform verification code is: {otp_code}",
            from_=twilio_number,
            to=phone_number
        )
        
        logger.info(f"OTP sent successfully. SID: {message.sid}")
        return otp_code, None
    
    except TwilioRestException as e:
        error_code = e.code
        error_message = e.msg
        
        # Handle specific Twilio error codes
        if error_code == 21211:  # Invalid 'To' Phone Number
            logger.error(f"Invalid phone number format: {phone_number}")
            return None, "The phone number format is invalid. Please use international format with country code."
        elif error_code == 21214:  # 'To' phone number cannot be reached
            logger.error(f"Phone number cannot be reached: {phone_number}")
            return None, "This phone number cannot receive SMS messages. Please try a different number."
        elif error_code == 21608:  # Authentication Error
            logger.error("Twilio authentication error")
            # Fallback to test mode for development
            logger.info(f"Using test mode instead. OTP code: {otp_code}")
            return otp_code, "SMS service authentication failed. Using test mode."
        else:
            logger.error(f"Twilio error: {error_code} - {error_message}")
            # Fallback to test mode
            logger.info(f"Using test mode instead. OTP code: {otp_code}")
            return otp_code, f"SMS service error ({error_code}). Using test mode."
    
    except TwilioException as e:
        logger.error(f"Twilio general exception: {str(e)}")
        # Fallback to test mode
        logger.info(f"Using test mode instead. OTP code: {otp_code}")
        return otp_code, f"SMS service exception. Using test mode."
    
    except Exception as e:
        logger.error(f"Unexpected error: {str(e)}")
        # Fallback to test mode
        logger.info(f"Using test mode instead. OTP code: {otp_code}")
        return otp_code, f"Unexpected error: {str(e)}. Using test mode."

def verify_otp(user_id, entered_otp, user_type='customer'):
    """
    Verify OTP code from database
    
    Args:
        user_id: User ID
        entered_otp: OTP entered by user
        user_type: Type of user ('customer' or 'provider')
        
    Returns:
        True if OTP is valid, False otherwise
    """
    from models import OTPVerification
    from datetime import datetime
    
    logger.info(f"Verifying OTP for {user_type} {user_id}")
    
    if not entered_otp or not user_id:
        logger.warning("Missing OTP or user ID")
        return False
    
    # Get the latest OTP for this user
    otp_record = OTPVerification.query.filter_by(
        user_id=user_id,
        user_type=user_type,
        is_used=False
    ).order_by(OTPVerification.created_at.desc()).first()
    
    if not otp_record:
        logger.warning(f"No active OTP found for {user_type} {user_id}")
        return False
    
    # Check if OTP matches
    if entered_otp != otp_record.otp_code:
        logger.warning(f"Invalid OTP entered for {user_type} {user_id}")
        return False
    
    # Check if OTP is expired
    if datetime.utcnow() > otp_record.expires_at:
        logger.warning(f"Expired OTP for {user_type} {user_id}")
        return False
    
    # Mark OTP as used
    otp_record.is_used = True
    from db_setup import db
    db.session.commit()
    
    logger.info(f"OTP verified successfully for {user_type} {user_id}")
    return True



def update_provider_rating(provider_id):
    """
    Simplified function to update a provider's average rating based on completed bookings
    
    Args:
        provider_id: ID of the provider
        
    Returns:
        (avg_rating, count) tuple
        avg_rating: New average rating (0-5)
        count: Number of ratings used to calculate average
    """
    from models import Provider, Booking
    from db_setup import db
    
    logger.info(f"Updating average rating for provider {provider_id}")
    
    provider = Provider.query.get(provider_id)
    if not provider:
        logger.error(f"Provider {provider_id} not found")
        return None, 0
    
    # Get all completed bookings with ratings
    rated_bookings = Booking.query.filter_by(
        provider_id=provider_id,
        status='completed'
    ).filter(Booking.rating.isnot(None)).all()
    
    if not rated_bookings:
        logger.info(f"No ratings found for provider {provider_id}")
        provider.avg_rating = None
        db.session.commit()
        return None, 0
    
    # Simple average calculation
    total_rating = sum(booking.rating for booking in rated_bookings)
    avg_rating = round(total_rating / len(rated_bookings), 2)
    
    # Update provider's average rating
    provider.avg_rating = avg_rating
    db.session.commit()
    
    logger.info(f"Updated provider {provider_id} rating to {avg_rating} based on {len(rated_bookings)} reviews")
    return avg_rating, len(rated_bookings)

def get_available_time_slots(provider_id, date):
    """
    Get available time slots for a provider on a specific date
    
    Args:
        provider_id: ID of the provider
        date: Date object for availability check
        
    Returns:
        List of available time slots
    """
    from models import Booking, Provider
    
    logger.info(f"Getting available time slots for provider {provider_id} on {date}")
    
    # Default time slots (9 AM to 6 PM in 1-hour increments)
    all_time_slots = [
        '09:00-10:00', '10:00-11:00', '11:00-12:00',
        '13:00-14:00', '14:00-15:00', '15:00-16:00',
        '16:00-17:00', '17:00-18:00'
    ]
    
    # Check if provider is available on this date
    provider = Provider.query.get(provider_id)
    if not provider or not provider.is_available:
        logger.warning(f"Provider {provider_id} is not available")
        return []
    
    # Get bookings for this provider on this date
    bookings = Booking.query.filter_by(
        provider_id=provider_id,
        booking_date=date
    ).filter(Booking.status.in_(['pending', 'confirmed'])).all()
    
    # Get time slots that are already booked
    booked_slots = [booking.time_slot for booking in bookings]
    
    # Return available time slots
    available_slots = [slot for slot in all_time_slots if slot not in booked_slots]
    
    logger.info(f"Found {len(available_slots)} available time slots for provider {provider_id} on {date}")
    return available_slots

def find_top_rated_providers(limit=5):
    """
    Find the top-rated providers on the platform
    
    Args:
        limit: Maximum number of providers to return
        
    Returns:
        List of Provider objects, sorted by rating
    """
    from models import Provider
    
    logger.info(f"Finding top {limit} rated providers")
    
    # Get providers that have ratings and are verified
    top_providers = Provider.query.filter(
        Provider.avg_rating.isnot(None),
        Provider.is_verified == True
    ).order_by(Provider.avg_rating.desc()).limit(limit).all()
    
    logger.info(f"Found {len(top_providers)} top-rated providers")
    return top_providers

def check_booking_conflicts(provider_id, date, time_slot):
    """
    Check if a provider already has a booking at the specified date and time
    
    Args:
        provider_id: ID of the provider
        date: Date of the booking
        time_slot: Time slot for the booking
        
    Returns:
        Boolean indicating whether there is a conflict
    """
    from models import Booking
    
    logger.info(f"Checking booking conflicts for provider {provider_id} on {date} at {time_slot}")
    
    # Check for existing bookings at the same time
    existing_booking = Booking.query.filter_by(
        provider_id=provider_id,
        booking_date=date,
        time_slot=time_slot
    ).filter(Booking.status.in_(['pending', 'confirmed'])).first()
    
    conflict = existing_booking is not None
    logger.info(f"Booking conflict: {conflict}")
    
    return conflict

def cancel_booking(booking_id, cancel_reason=None):
    """
    Cancel a booking and handle related operations
    
    Args:
        booking_id: ID of the booking to cancel
        cancel_reason: Reason for cancellation (optional)
        
    Returns:
        (success, error) tuple
        success: True if cancellation was successful, False otherwise
        error: Error message if cancellation failed, None otherwise
    """
    from models import Booking, Payment
    from db_setup import db
    
    logger.info(f"Cancelling booking {booking_id}")
    
    booking = Booking.query.get(booking_id)
    if not booking:
        logger.error(f"Booking {booking_id} not found")
        return False, "Booking not found"
    
    # Check if booking can be cancelled
    if booking.status not in ['pending', 'confirmed']:
        logger.warning(f"Booking {booking_id} cannot be cancelled (status: {booking.status})")
        return False, f"Booking cannot be cancelled (status: {booking.status})"
    
    # Update booking status
    booking.status = 'cancelled'
    if cancel_reason:
        booking.cancellation_reason = cancel_reason
    
    # Handle payment refund if needed
    payment = Payment.query.filter_by(booking_id=booking_id).first()
    if payment and payment.status == 'successful':
        # In a real system, this would initiate a refund through the payment gateway
        payment.status = 'refunded'
        logger.info(f"Marked payment for booking {booking_id} as refunded")
    
    db.session.commit()
    logger.info(f"Booking {booking_id} cancelled successfully")
    
    return True, None

def validate_booking_data(data):
    """
    Validate booking data before creating a booking
    
    Args:
        data: Dictionary containing booking data
        
    Returns:
        (is_valid, errors) tuple
        is_valid: Boolean indicating whether the data is valid
        errors: Dictionary of validation errors, empty if valid
    """
    from datetime import datetime
    
    logger.info("Validating booking data")
    errors = {}
    
    # Required fields
    required_fields = ['customer_id', 'provider_id', 'category_id', 
                      'address_id', 'booking_date', 'time_slot']
    
    for field in required_fields:
        if field not in data or not data[field]:
            errors[field] = f"{field} is required"
    
    # If missing required fields, return early
    if errors:
        logger.warning(f"Booking validation failed: missing required fields {errors}")
        return False, errors
    
    # Validate date format
    try:
        if isinstance(data['booking_date'], str):
            booking_date = datetime.strptime(data['booking_date'], '%Y-%m-%d').date()
        else:
            booking_date = data['booking_date']
        
        # Booking date should be in the future
        if booking_date < datetime.now().date():
            errors['booking_date'] = "Booking date must be in the future"
    except ValueError:
        errors['booking_date'] = "Invalid date format (use YYYY-MM-DD)"
    
    # Validate time slot format
    time_slot_pattern = r'^\d{2}:\d{2}-\d{2}:\d{2}'
    import re
    if not re.match(time_slot_pattern, data['time_slot']):
        errors['time_slot'] = "Invalid time slot format (use HH:MM-HH:MM)"
    
    # Check for booking conflicts
    if 'provider_id' in data and 'booking_date' in data and 'time_slot' in data:
        try:
            if check_booking_conflicts(data['provider_id'], booking_date, data['time_slot']):
                errors['time_slot'] = "This time slot is already booked"
        except Exception as e:
            logger.error(f"Error checking booking conflicts: {str(e)}")
            errors['time_slot'] = "Error checking availability"
    
    is_valid = len(errors) == 0
    if not is_valid:
        logger.warning(f"Booking validation failed: {errors}")
    else:
        logger.info("Booking validation successful")
    
    return is_valid, errors
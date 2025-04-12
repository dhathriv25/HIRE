"""Script to generate dummy data for the HIRE platform.

This script creates:
- 5 customer users with verified OTP status
- 30 service providers with verified OTP status
- All addresses are in Dublin, Ireland
"""

import os
import random
import string
import sqlite3
from datetime import datetime, timedelta
from werkzeug.security import generate_password_hash
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Define potential database paths
root_db_path = 'hire.db'
instance_db_path = os.path.join('instance', 'hire.db')

# Choose the first database that exists, prioritizing root path
if os.path.exists(root_db_path):
    db_path = root_db_path
    print(f"Using database at root: {root_db_path}")
elif os.path.exists(instance_db_path):
    db_path = instance_db_path
    print(f"Using database in instance folder: {instance_db_path}")
else:
    print("Error: No database file found. Please run 'python -m flask run' first to create the database.")
    print(f"Checked locations: {root_db_path}, {instance_db_path}")
    exit(1)

# Dublin postal codes (Eircodes)
dublin_postcodes = [
    'D01', 'D02', 'D03', 'D04', 'D05', 'D06', 'D07', 'D08', 'D09', 'D10',
    'D11', 'D12', 'D13', 'D14', 'D15', 'D16', 'D17', 'D18', 'D20', 'D22', 'D24'
]

# Dublin street names
dublin_streets = [
    'O\'Connell Street', 'Grafton Street', 'Dame Street', 'Henry Street', 'Talbot Street',
    'Parnell Street', 'Baggot Street', 'Leeson Street', 'Pearse Street', 'Merrion Square',
    'Fitzwilliam Square', 'St. Stephen\'s Green', 'Temple Bar', 'Dawson Street', 'Nassau Street',
    'Capel Street', 'Abbey Street', 'Gardiner Street', 'Mountjoy Square', 'North Circular Road',
    'South Circular Road', 'Rathmines Road', 'Ranelagh Road', 'Sandymount Avenue', 'Clontarf Road',
    'Howth Road', 'Malahide Road', 'Swords Road', 'Drumcondra Road', 'Dorset Street'
]

# Service categories with descriptions
service_categories = [
    ('Plumbing', 'All plumbing services including repairs, installations, and maintenance'),
    ('Electrical', 'Electrical repairs, installations, and maintenance services'),
    ('Cleaning', 'Professional home cleaning services including regular cleaning, deep cleaning, and specialized cleaning'),
    ('Carpentry', 'Woodwork, furniture repairs, and custom woodworking services'),
    ('Painting', 'Interior and exterior painting services for homes and businesses'),
    ('Landscaping', 'Garden maintenance, lawn care, and landscaping design services'),
    ('HVAC', 'Heating, ventilation, and air conditioning installation and repairs')
]

def generate_phone():
    """Generate a random Irish phone number"""
    return f"+353{random.randint(20, 99)}{random.randint(1000000, 9999999)}"

def generate_email(first_name, last_name):
    """Generate an email based on name"""
    domains = ['gmail.com', 'outlook.com', 'yahoo.com', 'hotmail.com', 'icloud.com']
    return f"{first_name.lower()}.{last_name.lower()}@{random.choice(domains)}"

def generate_address():
    """Generate a random Dublin address"""
    house_number = random.randint(1, 200)
    street = random.choice(dublin_streets)
    postcode = f"{random.choice(dublin_postcodes)} {random.choice(string.ascii_uppercase)}{random.randint(1, 9)}{random.choice(string.ascii_uppercase)}{random.choice(string.ascii_uppercase)}"
    
    return {
        'address_line': f"{house_number} {street}",
        'city': 'Dublin',
        'state': 'Dublin',
        'postal_code': postcode,
        'latitude': 53.3498 + random.uniform(-0.1, 0.1),  # Dublin latitude with small variation
        'longitude': -6.2603 + random.uniform(-0.1, 0.1)  # Dublin longitude with small variation
    }

def generate_dummy_data():
    """Generate and insert dummy data into the database"""
    
    # Connect to database
    print(f"Connecting to database at: {db_path}")
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    # Drop existing data from tables
    print("Dropping existing data from tables...")
    tables = [
        'provider_categories', 'otp_verifications', 'addresses', 
        'customers', 'providers', 'service_categories'
    ]
    
    for table in tables:
        try:
            cursor.execute(f"DELETE FROM {table}")
            print(f"- Dropped data from {table}")
        except sqlite3.Error as e:
            print(f"Error dropping data from {table}: {e}")
    
    conn.commit()
    
    try:
        # Insert service categories if they don't exist
        cursor.execute("SELECT COUNT(*) FROM service_categories")
        category_count = cursor.fetchone()[0]
        
        if category_count == 0:
            print("Adding service categories...")
            cursor.executemany(
                "INSERT INTO service_categories (name, description) VALUES (?, ?)",
                service_categories
            )
        
        # Get service category IDs
        cursor.execute("SELECT id, name FROM service_categories")
        categories = {name: id for id, name in cursor.fetchall()}
        
        # Generate customer data
        print("Generating 5 customers with verified OTP status...")
        
        # First names and last names for generating realistic user data
        first_names = ['Emma', 'Jack', 'Sophie', 'James', 'Olivia', 'Daniel', 'Emily', 'Sean', 'Ava', 'Conor']
        last_names = ['Murphy', 'Kelly', 'O\'Sullivan', 'Walsh', 'Smith', 'O\'Brien', 'Byrne', 'Ryan', 'O\'Connor', 'Doyle']
        
        # Generate 5 customers
        for i in range(5):
            # Generate customer details
            first_name = random.choice(first_names)
            last_name = random.choice(last_names)
            email = generate_email(first_name, last_name)
            phone = generate_phone()
            password_hash = generate_password_hash('password')
            
            # Insert customer
            cursor.execute(
                """INSERT INTO customers 
                   (email, phone, password_hash, first_name, last_name, is_verified, created_at) 
                   VALUES (?, ?, ?, ?, ?, ?, ?)""",
                (email, phone, password_hash, first_name, last_name, True, datetime.utcnow())
            )
            
            customer_id = cursor.lastrowid
            
            # Add address for customer
            address = generate_address()
            cursor.execute(
                """INSERT INTO addresses 
                   (customer_id, address_line, city, state, postal_code, latitude, longitude) 
                   VALUES (?, ?, ?, ?, ?, ?, ?)""",
                (customer_id, address['address_line'], address['city'], address['state'], 
                 address['postal_code'], address['latitude'], address['longitude'])
            )
            
            # Add OTP verification record (already verified)
            otp_code = ''.join(random.choices('0123456789', k=6))
            cursor.execute(
                """INSERT INTO otp_verifications 
                   (user_id, user_type, otp_code, created_at, expires_at, is_used) 
                   VALUES (?, ?, ?, ?, ?, ?)""",
                (customer_id, 'customer', otp_code, 
                 datetime.utcnow() - timedelta(days=1),  # Created yesterday 
                 datetime.utcnow() - timedelta(hours=23),  # Expired 1 hour after creation
                 True)  # OTP has been used (verified)
            )
        
        # Generate provider data
        print("Generating 30 service providers with verified OTP status...")
        
        # Additional names for more variety
        more_first_names = ['Liam', 'Aoife', 'Niamh', 'Cian', 'Saoirse', 'Finn', 'Ciara', 'Oisin', 'Eoin', 'Roisin',
                           'Eoghan', 'Caoimhe', 'Darragh', 'Siobhan', 'Padraig', 'Grainne', 'Cathal', 'Sinead', 'Fionn', 'Maire']
        more_last_names = ['McCarthy', 'O\'Neill', 'Reilly', 'Doherty', 'Kennedy', 'Lynch', 'Murray', 'Quinn', 'Moore', 'McLoughlin',
                          'O\'Leary', 'Dunne', 'Fitzgerald', 'Gallagher', 'Clarke', 'Brennan', 'Collins', 'Campbell', 'Johnston', 'Hughes']
        
        all_first_names = first_names + more_first_names
        all_last_names = last_names + more_last_names
        
        # Generate 30 providers
        for i in range(30):
            # Generate provider details
            first_name = random.choice(all_first_names)
            last_name = random.choice(all_last_names)
            email = generate_email(first_name, last_name)
            phone = generate_phone()
            password_hash = generate_password_hash('password')
            verification_document = f"ID_{first_name}_{last_name}_{random.randint(1000, 9999)}.pdf"
            experience_years = random.randint(1, 20)
            
            # Insert provider
            cursor.execute(
                """INSERT INTO providers 
                   (email, phone, password_hash, first_name, last_name, verification_document, 
                    experience_years, is_available, avg_rating, is_verified, created_at) 
                   VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                (email, phone, password_hash, first_name, last_name, verification_document, 
                 experience_years, True, random.uniform(3.5, 5.0), True, datetime.utcnow())
            )
            
            provider_id = cursor.lastrowid
            
            # Add address for provider
            address = generate_address()
            cursor.execute(
                """INSERT INTO addresses 
                   (provider_id, address_line, city, state, postal_code, latitude, longitude) 
                   VALUES (?, ?, ?, ?, ?, ?, ?)""",
                (provider_id, address['address_line'], address['city'], address['state'], 
                 address['postal_code'], address['latitude'], address['longitude'])
            )
            
            # Add OTP verification record (already verified)
            otp_code = ''.join(random.choices('0123456789', k=6))
            cursor.execute(
                """INSERT INTO otp_verifications 
                   (user_id, user_type, otp_code, created_at, expires_at, is_used) 
                   VALUES (?, ?, ?, ?, ?, ?)""",
                (provider_id, 'provider', otp_code, 
                 datetime.utcnow() - timedelta(days=1),  # Created yesterday 
                 datetime.utcnow() - timedelta(hours=23),  # Expired 1 hour after creation
                 True)  # OTP has been used (verified)
            )
            
            # Assign 1-3 service categories to each provider
            num_categories = random.randint(1, 3)
            selected_categories = random.sample(list(categories.items()), num_categories)
            
            for category_name, category_id in selected_categories:
                # Generate a reasonable price rate based on the service type
                base_rates = {
                    'Plumbing': 60,
                    'Electrical': 65,
                    'Cleaning': 30,
                    'Carpentry': 55,
                    'Painting': 45,
                    'Landscaping': 40,
                    'HVAC': 70
                }
                
                base_rate = base_rates.get(category_name, 50)  # Default to 50 if category not found
                price_rate = base_rate + random.randint(-10, 20)  # Add some variation
                
                cursor.execute(
                    """INSERT INTO provider_categories 
                       (provider_id, category_id, price_rate) 
                       VALUES (?, ?, ?)""",
                    (provider_id, category_id, price_rate)
                )
        
        # Commit all changes
        conn.commit()
        print("Successfully generated dummy data!")
        print("- 5 customers with verified OTP status")
        print("- 30 service providers with verified OTP status")
        print("- All addresses in Dublin, Ireland")
        
        # Print credentials for easy access
        print("\n=== DUMMY CREDENTIALS ===\n")
        
        # Print customer credentials
        print("CUSTOMER CREDENTIALS:")
        cursor.execute("SELECT email FROM customers")
        customer_emails = cursor.fetchall()
        for email in customer_emails:
            print(f"Email: {email[0]}, Password: password")
        
        # Print provider credentials
        print("\nPROVIDER CREDENTIALS:")
        cursor.execute("SELECT email FROM providers")
        provider_emails = cursor.fetchall()
        for email in provider_emails:
            print(f"Email: {email[0]}, Password: password")
        
    except sqlite3.Error as e:
        conn.rollback()
        print(f"Error generating dummy data: {e}")
    finally:
        conn.close()

if __name__ == "__main__":
    generate_dummy_data()
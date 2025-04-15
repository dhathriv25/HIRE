"""Script to drop the HIRE platform database.
This will completely remove the database files.
"""

import os
import shutil

def drop_database():
    print("Dropping HIRE database...")
    
    # Database files to remove
    db_files = ["hire.db"]
    dropped = False
    
    # Remove each database file if it exists
    for db_file in db_files:
        if os.path.exists(db_file):
            try:
                os.remove(db_file)
                print(f"Dropped database: {db_file}")
                dropped = True
            except PermissionError:
                print(f"Error: Could not remove {db_file} - file may be in use")
            except Exception as e:
                print(f"Error removing {db_file}: {str(e)}")
    
    # Report results
    if dropped:
        print("Database successfully dropped!")
    else:
        print("No database files found to drop.")
    
    print("\nTo recreate the database with fresh data, run:")
    print("  python -m flask run")
    print("  python generate_dummy_data.py")

if __name__ == "__main__":
    drop_database()
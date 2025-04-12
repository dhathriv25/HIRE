import sqlite3
import os
db_path = os.path.join('instance', 'hire.db')

conn = sqlite3.connect(db_path)
cursor = conn.cursor()

cursor.execute("SELECT * FROM customers")
users = cursor.fetchall()

print('\nUsers in database:')
for user in users:
    print(user)

cursor.execute("SELECT * FROM providers")
providers = cursor.fetchall()

print('\nProviders in database:')
for provider in providers:
    print(provider)
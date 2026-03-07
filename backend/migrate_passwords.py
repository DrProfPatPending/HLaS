#!/usr/bin/env python
"""
Script to migrate existing plain-text passwords to hashed passwords
Run this once to update all existing databases
"""

import os
from sqlalchemy import create_engine, text
from werkzeug.security import generate_password_hash

def migrate_database_passwords(db_path):
    """Migrate plain-text passwords to hashed passwords in a database."""
    database_url = f"sqlite:///{db_path}"
    engine = create_engine(database_url, future=True)
    
    with engine.begin() as connection:
        # Get all members with passwords
        result = connection.execute(text('SELECT * FROM members WHERE password IS NOT NULL'))
        rows = result.fetchall()
        columns = result.keys()
        
        # Find password column index
        password_idx = list(columns).index('password')
        id_idx = list(columns).index('ID') if 'ID' in columns else None
        
        if id_idx is None:
            print(f"Warning: No ID column found in {db_path}, skipping migration")
            return 0
        
        migrated_count = 0
        for row in rows:
            current_password = row[password_idx]
            member_id = row[id_idx]
            
            # Check if password is already hashed (Werkzeug hashes start with method identifier)
            if current_password and not current_password.startswith(('scrypt:', 'pbkdf2:', 'bcrypt:')):
                # Hash the plain-text password
                hashed_password = generate_password_hash(current_password)
                
                # Update the database
                connection.execute(
                    text('UPDATE members SET password = :hashed WHERE ID = :id'),
                    {'hashed': hashed_password, 'id': member_id}
                )
                migrated_count += 1
        
        print(f"✓ Migrated {migrated_count} passwords in {db_path}")
        return migrated_count

if __name__ == '__main__':
    backend_dir = os.path.dirname(__file__)
    databases = ['members.db', 'GAAFFS.db', 'CTC.db']
    
    total_migrated = 0
    print("Starting password migration...\n")
    
    for db_name in databases:
        db_path = os.path.join(backend_dir, db_name)
        if os.path.exists(db_path):
            print(f"Processing {db_name}...")
            count = migrate_database_passwords(db_path)
            total_migrated += count
        else:
            print(f"⚠ Skipping {db_name} (file not found)")
    
    print(f"\n✓ Migration complete! Total passwords migrated: {total_migrated}")
    print("All passwords are now securely hashed using Werkzeug's scrypt algorithm.")

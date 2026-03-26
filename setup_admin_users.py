#!/usr/bin/env python3
"""
Setup admin users in the HLaS database.
Creates rob@scoffin.com and admin users with app_admin role.
"""

import os
import sys
from werkzeug.security import generate_password_hash

# Setup environment
os.environ['DATABASE_URL'] = 'postgresql://hlas:hlas@localhost:5432/hlas'
os.environ['DATABASE_URL'] = 'postgresql://hlas:hlas@localhost:5433/hlas'
os.environ['HLAS_USE_POSTGRES_READS'] = '1'

# Add backend to path
sys.path.insert(0, '/opt/HLaS/backend')

from app import create_app
from sqlalchemy import select, text

app = create_app()

with app.app_context():
    from sqlalchemy import select, text
    from sqlalchemy.orm import Session
    
    # Get the engine from app.config or create one
    if 'SQLALCHEMY_ENGINE' in app.config:
        engine = app.config['SQLALCHEMY_ENGINE']
    else:
        from sqlalchemy import create_engine
        db_url = os.environ.get('DATABASE_URL', 'sqlite:///./members.db')
        if 'psycopg' not in db_url and 'postgresql://' in db_url:
            db_url = db_url.replace('postgresql://', 'postgresql+psycopg://')
        engine = create_engine(db_url)
    
    session = Session(engine)
    
    try:
        print("Setting up admin users...")
        
        # Get GAAFFS club
        gaaffs_result = session.execute(text("SELECT id FROM clubs WHERE short_name = 'GAAFFS' LIMIT 1"))
        gaaffs_id = gaaffs_result.scalar()
        if not gaaffs_id:
            print("ERROR: GAAFFS club not found!")
            sys.exit(1)
        print(f"✓ Found GAAFFS club (ID: {gaaffs_id})")
        
        # Get app_admin role
        role_result = session.execute(text("SELECT id FROM roles WHERE code = 'app_admin' LIMIT 1"))
        app_admin_role_id = role_result.scalar()
        if not app_admin_role_id:
            print("ERROR: app_admin role not found!")
            sys.exit(1)
        print(f"✓ Found app_admin role (ID: {app_admin_role_id})")
        
        # Create/update rob@scoffin.com
        print("\nSetting up user 'rob@scoffin.com'...")
        rob_user = session.execute(
            text("SELECT id FROM members WHERE username = 'rob@scoffin.com' LIMIT 1")
        ).scalar()

        # Always generate the password hash for both tables
        password_hash = generate_password_hash('password', method='pbkdf2')

        if not rob_user:
            session.execute(text("""
                INSERT INTO members (
                    club_id, members_name, first_name, last_name, username, password,
                    created_at, updated_at
                ) VALUES (:club_id, :members_name, :first_name, :last_name, :username, :password,
                    NOW(), NOW())
            """), {
                'club_id': gaaffs_id,
                'members_name': 'Rob Scoffin',
                'first_name': 'Rob',
                'last_name': 'Scoffin',
                'username': 'rob@scoffin.com',
                'password': password_hash
            })
            session.commit()
            rob_user = session.execute(
                text("SELECT id FROM members WHERE username = 'rob@scoffin.com' LIMIT 1")
            ).scalar()
            print(f"✓ Created user rob@scoffin.com (ID: {rob_user})")
        else:
            print(f"✓ User rob@scoffin.com already exists (ID: {rob_user})")
            # Update password
            session.execute(text("""
                UPDATE members SET password = :password WHERE id = :id
            """), {'password': password_hash, 'id': rob_user})
            session.commit()
            print("✓ Updated password for rob@scoffin.com")

        # --- Sync password_hash in app_users table ---
        app_user_id = session.execute(
            text("SELECT id FROM app_users WHERE username = 'rob@scoffin.com' LIMIT 1")
        ).scalar()
        if app_user_id:
            session.execute(text("""
                UPDATE app_users SET password_hash = :password_hash WHERE id = :id
            """), {'password_hash': password_hash, 'id': app_user_id})
            session.commit()
            print("✓ Updated password_hash for rob@scoffin.com in app_users")
        else:
            # Insert if not present (should not happen, but for safety)
            session.execute(text("""
                INSERT INTO app_users (username, email, display_name, password_hash, is_active, created_at, updated_at)
                VALUES (:username, :email, :display_name, :password_hash, TRUE, NOW(), NOW())
            """), {
                'username': 'rob@scoffin.com',
                'email': 'rob@scoffin.com',
                'display_name': 'Rob Scoffin',
                'password_hash': password_hash
            })
            session.commit()
            print("✓ Inserted rob@scoffin.com into app_users with password_hash")
        
        # Create/update admin user
        print("\nSetting up user 'admin'...")
        admin_user = session.execute(
            text("SELECT id FROM members WHERE username = 'admin' LIMIT 1")
        ).scalar()
        
        if not admin_user:
            password_hash = generate_password_hash('admin123', method='pbkdf2')
            session.execute(text("""
                INSERT INTO members (
                    club_id, members_name, first_name, last_name, username, password,
                    created_at, updated_at
                ) VALUES (:club_id, :members_name, :first_name, :last_name, :username, :password,
                    NOW(), NOW())
            """), {
                'club_id': gaaffs_id,
                'members_name': 'Admin User',
                'first_name': 'Admin',
                'last_name': 'User',
                'username': 'admin',
                'password': password_hash
            })
            session.commit()
            admin_user = session.execute(
                text("SELECT id FROM members WHERE username = 'admin' LIMIT 1")
            ).scalar()
            print(f"✓ Created user admin (ID: {admin_user})")
        else:
            print(f"✓ User admin already exists (ID: {admin_user})")
            # Update password
            password_hash = generate_password_hash('admin123', method='pbkdf2')
            session.execute(text("""
                UPDATE members SET password = :password WHERE id = :id
            """), {'password': password_hash, 'id': admin_user})
            session.commit()
            print("✓ Updated password for admin")
        
        # Assign app_admin role to both users
        print("\nAssigning app_admin role...")
        
        # Check existing assignments
        rob_admin_role = session.execute(text("""
            SELECT id FROM member_role_assignments 
            WHERE member_id = :member_id AND role_id = :role_id AND club_id IS NULL
            LIMIT 1
        """), {'member_id': rob_user, 'role_id': app_admin_role_id}).scalar()
        
        if not rob_admin_role:
            session.execute(text("""
                INSERT INTO member_role_assignments (member_id, role_id, club_id, granted_at)
                VALUES (:member_id, :role_id, NULL, NOW())
            """), {'member_id': rob_user, 'role_id': app_admin_role_id})
            session.commit()
            print(f"✓ Assigned app_admin role to rob@scoffin.com")
        else:
            print(f"✓ rob@scoffin.com already has app_admin role")
        
        admin_admin_role = session.execute(text("""
            SELECT id FROM member_role_assignments 
            WHERE member_id = :member_id AND role_id = :role_id AND club_id IS NULL
            LIMIT 1
        """), {'member_id': admin_user, 'role_id': app_admin_role_id}).scalar()
        
        if not admin_admin_role:
            session.execute(text("""
                INSERT INTO member_role_assignments (member_id, role_id, club_id, granted_at)
                VALUES (:member_id, :role_id, NULL, NOW())
            """), {'member_id': admin_user, 'role_id': app_admin_role_id})
            session.commit()
            print(f"✓ Assigned app_admin role to admin")
        else:
            print(f"✓ admin already has app_admin role")
        
        # Verify setup
        print("\n" + "="*60)
        print("VERIFICATION")
        print("="*60)
        
        result = session.execute(text("""
            SELECT m.id, m.username, m.members_name, r.code, r.name
            FROM members m
            LEFT JOIN member_role_assignments mra ON m.id = mra.member_id
            LEFT JOIN roles r ON mra.role_id = r.id
            WHERE m.username IN ('rob@scoffin.com', 'admin')
            ORDER BY m.username, r.code
        """))
        
        for row in result:
            member_id, username, name, role_code, role_name = row
            print(f"{username:20} ({name:20}) -> {role_code or 'N/A':12} {role_name or ''}")
        
        print("="*60)
        print("\n✓ Admin user setup complete!")
        print("\nYou can now login to the admin panel with:")
        print("  Username: rob@scoffin.com")
        print("  Password: password")
        print("\nOr:")
        print("  Username: admin")
        print("  Password: admin123")
        
    except Exception as e:
        print(f"ERROR: {e}", file=sys.stderr)
        import traceback
        traceback.print_exc()
        sys.exit(1)
    finally:
        session.close()

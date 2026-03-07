#!/usr/bin/env python
"""
Script to set up club-specific databases from the original members.db
Creates GAAFFS.db and CTC.db with the same schema and data from members.db
"""

import shutil
import os

# Get the backend directory
backend_dir = os.path.dirname(__file__)
members_db = os.path.join(backend_dir, 'members.db')
gaaffs_db = os.path.join(backend_dir, 'GAAFFS.db')
ctc_db = os.path.join(backend_dir, 'CTC.db')

print(f"Backend directory: {backend_dir}")
print(f"Source database: {members_db}")
print(f"Target GAAFFS database: {gaaffs_db}")
print(f"Target CTC database: {ctc_db}")

if not os.path.exists(members_db):
    print(f"ERROR: {members_db} not found!")
    exit(1)

# Copy members.db to GAAFFS.db
if os.path.exists(gaaffs_db):
    print(f"WARNING: {gaaffs_db} already exists, backing up to {gaaffs_db}.bak")
    shutil.copy(gaaffs_db, f'{gaaffs_db}.bak')
else:
    print(f"Creating {gaaffs_db}...")

shutil.copy(members_db, gaaffs_db)
print(f"✓ Created {gaaffs_db}")

# Copy members.db to CTC.db
if os.path.exists(ctc_db):
    print(f"WARNING: {ctc_db} already exists, backing up to {ctc_db}.bak")
    shutil.copy(ctc_db, f'{ctc_db}.bak')
else:
    print(f"Creating {ctc_db}...")

shutil.copy(members_db, ctc_db)
print(f"✓ Created {ctc_db}")

print("\n✓ Club-specific databases created successfully!")
print(f"  - GAAFFS.db: {gaaffs_db}")
print(f"  - CTC.db: {ctc_db}")
print("\nNote: Both databases currently contain the same data from members.db")
print("You can modify the data in each database independently.")

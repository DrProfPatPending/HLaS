#!/usr/bin/env python3
"""
Sync Club Documents from JSON to PostgreSQL database

This script reads documents from documents.json and upserts them into the
PostgreSQL club_documents table, restoring documents on a fresh deployment.

This is typically run during production server rebuilds to restore uploaded documents.
"""

import json
import os
import sys
import base64
from pathlib import Path
from typing import List, Dict, Any
from sqlalchemy import create_engine, select, delete, insert
from sqlalchemy.exc import SQLAlchemyError


def load_env_vars():
    """Load environment variables"""
    try:
        from dotenv import load_dotenv
        load_dotenv()
    except ImportError:
        pass


def load_documents_from_json(json_path: Path) -> Dict[str, List[Dict[str, Any]]]:
    """Load documents from documents.json
    
    Args:
        json_path: Path to documents.json file
        
    Returns:
        Dictionary mapping club short_name to list of documents
    """
    if not json_path.exists():
        raise FileNotFoundError(f'Documents file not found: {json_path}')
    
    with open(json_path, 'r') as f:
        documents_data = json.load(f)
    
    return documents_data if isinstance(documents_data, dict) else {}


def sync_documents_to_postgres(json_path: str = None, dry_run: bool = False, 
                               verbose: bool = True) -> bool:
    """Sync documents from JSON to PostgreSQL database
    
    Args:
        json_path: Path to documents.json file (default: ./backend/documents.json)
        dry_run: If True, don't write to database
        verbose: If True, print progress messages
    
    Returns:
        True if successful, False otherwise
    """
    load_env_vars()
    
    db_url = os.getenv('DATABASE_URL')
    if not db_url:
        if verbose:
            print('❌ DATABASE_URL not configured')
        return False
    
    try:
        # Setup path and imports
        sys.path.insert(0, os.path.dirname(__file__))
        from db_models import clubs as clubs_table, club_documents as club_documents_table
        
        # Create engine
        engine = create_engine(db_url)
        
        # Load documents from JSON
        json_file = Path(json_path or os.path.dirname(__file__)) / 'documents.json'
        
        if not json_file.exists():
            if verbose:
                print(f'⚠️  Documents file not found: {json_file}')
            return True  # Not an error if no documents exist
        
        documents_by_club = load_documents_from_json(json_file)
        if verbose:
            print(f'📖 Loaded documents from {json_file}')
        
        if not documents_by_club:
            if verbose:
                print('⚠️  No documents in JSON file')
            return True
        
        total_documents_synced = 0
        
        with engine.begin() as connection:
            # Get all active clubs from PostgreSQL
            clubs_result = connection.execute(
                select(clubs_table).where(clubs_table.c.is_active.is_(True))
            )
            clubs_rows = clubs_result.fetchall()
            
            # Create a map of club short_name to club_id
            club_id_map = {club_row.short_name: club_row.id for club_row in clubs_rows}
            
            for club_name, docs in documents_by_club.items():
                if club_name not in club_id_map:
                    if verbose:
                        print(f'⚠️  Club not found in database: {club_name}')
                    continue
                
                club_id = club_id_map[club_name]
                
                if not docs:
                    if verbose:
                        print(f'⚠️  No documents in JSON for {club_name}')
                    continue
                
                if not dry_run:
                    # Delete existing documents for this club (clean slate)
                    connection.execute(
                        delete(club_documents_table).where(
                            club_documents_table.c.club_id == club_id
                        )
                    )
                    if verbose:
                        print(f'🗑️  Cleared existing documents for {club_name}')
                
                # Insert documents from JSON
                for index, doc in enumerate(docs):
                    try:
                        # Decode base64 file content
                        file_b64 = doc.get('fileContent', '')
                        file_data = base64.b64decode(file_b64) if file_b64 else b''
                        
                        doc_insert = {
                            'club_id': club_id,
                            'display_order': int(doc.get('displayOrder') or (index + 1)),
                            'title': doc.get('title', ''),
                            'file_name': doc.get('fileName', ''),
                            'file_ext': doc.get('fileExt', ''),
                            'file_size': doc.get('fileSize', 0),
                            'mime_type': doc.get('mimeType', ''),
                            'file_data': file_data,
                            'uploaded_by_user_id': doc.get('uploadedBy', 'system'),
                            'created_at': doc.get('createdAt', ''),
                        }
                        
                        if not dry_run:
                            connection.execute(
                                insert(club_documents_table).values(**doc_insert)
                            )
                        
                        total_documents_synced += 1
                        
                    except Exception as e:
                        if verbose:
                            print(f'⚠️  Error syncing document "{doc.get("fileName")}": {e}')
                        continue
                
                if verbose:
                    docs_count = len(docs)
                    print(f'✅ Synced {docs_count} document(s) to {club_name}')
        
        if verbose:
            action = 'Would sync' if dry_run else 'Synced'
            print(f'✅ {action} {total_documents_synced} document(s) total')
        
        return True
        
    except FileNotFoundError as e:
        if verbose:
            print(f'❌ File not found: {e}')
        return False
    except SQLAlchemyError as e:
        if verbose:
            print(f'❌ Database error: {e}')
        return False
    except Exception as e:
        if verbose:
            print(f'❌ Error: {e}')
        return False


if __name__ == '__main__':
    import argparse
    
    parser = argparse.ArgumentParser(description='Sync club documents from JSON to PostgreSQL')
    parser.add_argument('-f', '--file', help='Path to documents.json (default: ./documents.json)')
    parser.add_argument('-u', '--database-url', help='PostgreSQL connection URL (defaults to DATABASE_URL env if set)')
    parser.add_argument('-d', '--dry-run', action='store_true', help='Run without making changes')
    parser.add_argument('-v', '--verbose', action='store_true', default=True, help='Verbose output')
    parser.add_argument('-q', '--quiet', action='store_true', help='Suppress output')
    
    args = parser.parse_args()
    
    # If database URL provided via CLI, set it as environment variable
    if args.database_url:
        os.environ['DATABASE_URL'] = args.database_url
    
    success = sync_documents_to_postgres(
        json_path=args.file,
        dry_run=args.dry_run,
        verbose=not args.quiet
    )
    
    sys.exit(0 if success else 1)

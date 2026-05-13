#!/usr/bin/env python3
"""
Sync Club Documents from PostgreSQL database to JSON files

This script reads documents from the PostgreSQL club_documents table and writes them
to a JSON structure, preserving document metadata and base64-encoded binary content.
Useful for persisting uploaded documents back to the config files for production rebuilds.

Documents are stored in: backend/documents.json per club
"""

import json
import os
import sys
import base64
from pathlib import Path
from typing import List, Dict, Any
from sqlalchemy import create_engine, select
from sqlalchemy.exc import SQLAlchemyError


def load_env_vars():
    """Load environment variables"""
    try:
        from dotenv import load_dotenv
        load_dotenv()
    except ImportError:
        pass


def load_documents_from_postgres(db_url: str) -> Dict[str, List[Dict[str, Any]]]:
    """Load documents from PostgreSQL database
    
    Args:
        db_url: Database connection string
        
    Returns:
        Dictionary mapping club short_name to list of documents
    """
    sys.path.insert(0, os.path.dirname(__file__))
    from db_models import clubs as clubs_table, club_documents as club_documents_table
    
    engine = create_engine(db_url)
    documents_by_club = {}
    
    with engine.begin() as connection:
        # Get all active clubs from PostgreSQL
        clubs_result = connection.execute(
            select(clubs_table).where(clubs_table.c.is_active.is_(True))
        )
        clubs_rows = clubs_result.fetchall()
        
        for club_row in clubs_rows:
            club_id = club_row.id
            short_name = club_row.short_name
            
            # Get documents for this club from PostgreSQL
            documents_result = connection.execute(
                select(club_documents_table)
                .where(club_documents_table.c.club_id == club_id)
                .order_by(club_documents_table.c.created_at.desc())
            )
            documents_rows = documents_result.fetchall()
            
            documents = []
            for doc_row in documents_rows:
                doc_dict = dict(doc_row._mapping)
                
                # Extract binary content and base64 encode it
                file_data = doc_dict.get('file_data', b'')
                if file_data:
                    if isinstance(file_data, bytes):
                        file_b64 = base64.b64encode(file_data).decode('utf-8')
                    else:
                        file_b64 = file_data
                else:
                    file_b64 = ''
                
                # Build document JSON
                doc_json = {
                    'title': doc_dict.get('title', ''),
                    'fileName': doc_dict.get('file_name', ''),
                    'fileExt': doc_dict.get('file_ext', ''),
                    'fileSize': doc_dict.get('file_size', 0),
                    'mimeType': doc_dict.get('mime_type', ''),
                    'uploadedBy': doc_dict.get('uploaded_by_user_id', ''),
                    'createdAt': doc_dict.get('created_at', '').isoformat() if doc_dict.get('created_at') else '',
                    'fileContent': file_b64,  # Base64 encoded binary data
                }
                documents.append(doc_json)
            
            if documents:
                documents_by_club[short_name] = documents
    
    return documents_by_club


def save_documents_to_json(output_dir: Path, documents_by_club: Dict[str, List[Dict[str, Any]]], 
                           verbose: bool = True) -> bool:
    """Save documents to JSON files in the output directory
    
    Args:
        output_dir: Directory to save documents.json files to
        documents_by_club: Dictionary of documents by club short_name
        verbose: If True, print progress messages
        
    Returns:
        True if successful, False otherwise
    """
    output_dir.mkdir(parents=True, exist_ok=True)
    
    documents_data = {}
    for club_name, docs in documents_by_club.items():
        documents_data[club_name] = docs
        if verbose:
            print(f'✅ Prepared {len(docs)} document(s) for {club_name}')
    
    # Write to single documents.json file
    output_file = output_dir / 'documents.json'
    try:
        with open(output_file, 'w') as f:
            json.dump(documents_data, f, indent=2, default=str)
        
        if verbose:
            print(f'✅ Saved {len(documents_data)} club(s) to {output_file}')
        return True
    except Exception as e:
        if verbose:
            print(f'❌ Error saving documents to {output_file}: {e}')
        return False


def sync_documents_to_json(output_path: str = None, verbose: bool = True) -> bool:
    """Sync documents from PostgreSQL to JSON file
    
    Args:
        output_path: Path to save documents.json (default: ./backend/)
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
        # Load documents from PostgreSQL
        if verbose:
            print('📖 Loading documents from PostgreSQL...')
        documents_by_club = load_documents_from_postgres(db_url)
        
        if not documents_by_club:
            if verbose:
                print('⚠️  No documents found in PostgreSQL')
            return True
        
        # Save to JSON
        output_dir = Path(output_path or os.path.dirname(__file__))
        return save_documents_to_json(output_dir, documents_by_club, verbose)
        
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
    
    parser = argparse.ArgumentParser(description='Sync club documents from PostgreSQL to JSON')
    parser.add_argument('-o', '--output', help='Output directory for documents.json (default: ./)')
    parser.add_argument('-u', '--database-url', help='PostgreSQL connection URL (defaults to DATABASE_URL env if set)')
    parser.add_argument('-v', '--verbose', action='store_true', default=True, help='Verbose output')
    parser.add_argument('-q', '--quiet', action='store_true', help='Suppress output')
    
    args = parser.parse_args()
    
    # If database URL provided via CLI, set it as environment variable
    if args.database_url:
        os.environ['DATABASE_URL'] = args.database_url
    
    success = sync_documents_to_json(
        output_path=args.output,
        verbose=not args.quiet
    )
    
    sys.exit(0 if success else 1)

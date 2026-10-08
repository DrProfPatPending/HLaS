# Deployment Changes - May 2026

### Language Convention

- User-facing copy and documentation in this repository should default to British English spelling (for example: recognised, localisation, authorised).
- Keep external API/library identifiers unchanged where spelling is fixed by the platform (for example: `wp_localize_script`).

## Summary of Changes

This document covers three major enhancements to the HLaS Home Page and document management system:

1. **Table Sorting** - Alphanumeric sorting on News/Updates and Documents tables
2. **News Table Restructuring** - Unified layout matching Documents table
3. **Document Sync System** - JSON-based persistence for production rebuilds

---

## 1. Table Sorting Implementation

### Overview
Added interactive sorting to both the **News and Updates** and **Documents** tables on the Home Page. Users can now click column headers to sort data alphanumerically with ascending/descending toggle.

### Features
- ✅ Click any column header to sort by that column
- ✅ Visual indicators (▲/▼) show sort direction
- ✅ Alphanumeric sorting using natural number ordering
- ✅ Actions column excluded from sorting on both tables
- ✅ Responsive to data changes

### Files Modified
- `frontend/src/components/HomeView.vue`

### Technical Details

**Data Properties Added:**
```javascript
data() {
  return {
    // News table sorting
    newsSortedBy: null,              // Current sort column
    newsSortDirection: 'asc',        // Sort direction (asc/desc)
    
    // Documents table sorting
    documentsSortedBy: null,
    documentsSortDirection: 'asc',
  };
}
```

**Computed Properties:**
```javascript
computed: {
  // Sorted news items with property mapping
  sortedNewsItems() {
    // Maps column keys to data properties:
    // 'Date' → 'date', 'Category' → 'category', 'Update' → 'update'
  },
  
  // Sorted documents with property mapping
  sortedDocuments() {
    // Maps column keys to data properties:
    // 'Title' → 'title', 'File' → 'fileName', 
    // 'Uploaded' → 'createdAt', 'Size' → 'fileSize'
  }
}
```

**Methods:**
- `toggleNewsSort(columnKey)` - Toggle sort on News table (excludes Actions column)
- `toggleDocumentsSort(columnKey)` - Toggle sort on Documents table (excludes Actions column)
- `getSortIndicator(tableName, columnKey)` - Returns sort arrow (▲/▼)
- `isSortableColumn(tableName, columnKey)` - Determines if column is sortable

### Usage
Users simply click any column header (except Actions) to sort the table. Click again to reverse direction.

---

## 2. News Table Restructuring

### Overview
Reformatted the **News and Updates** table to match the **Documents** table layout for consistency. Action buttons (Edit/Delete) are now in a separate dedicated Actions column on the right.

### Changes Made

**Before:**
- Action buttons were embedded within the Update content cell
- Buttons would wrap with content

**After:**
- Action buttons in separate Actions column (rightmost)
- Buttons stack vertically in Actions cell
- Matches Documents table layout exactly
- Cleaner, more organized appearance

### Files Modified
- `frontend/src/components/HomeView.vue`

### Technical Changes

**Column Structure Update:**
```javascript
newsColumns() {
  return [
    { key: 'Date', label: 'Date' },
    { key: 'Category', label: 'Category' },
    { key: 'Update', label: 'Update' },
    { key: 'Actions', label: 'Actions' },  // NEW - moved from embedded
  ];
}
```

**Template Changes:**
- Update cell now displays only text content
- Actions cell contains Edit and Delete buttons stacked vertically
- Both tables now share same layout pattern

**CSS Updates:**
- `.news-actions-cell` - Center-aligned Actions column
- `.news-actions-stack` - Vertical button stack with flexbox
- Updated button sizing for consistency

### Column Visibility (Field Order)

**Important:** The Actions column is **always visible** and is NOT controlled by Field Order settings.

```javascript
getVisibleColumns(contextKey, fallbackColumns) {
  // Actions column is automatically appended
  // regardless of Field Order configuration
  // This ensures action buttons are always available
}
```

---

## 3. Document Sync System

### Overview
Implemented a JSON-based document sync system that mirrors the existing beats sync mechanism. This allows documents uploaded via the web interface to be persisted and automatically restored during production server rebuilds.

### Files Created
- `backend/sync_documents_postgres_to_json.py` - Export script
- `backend/sync_documents_json_to_postgres.py` - Import script
- `backend/documents.json` - Generated document manifest

### How It Works

#### Export (Development)
```bash
cd /opt/hlas
source backend-venv/bin/activate

# Export documents from PostgreSQL to JSON
python3 backend/sync_documents_postgres_to_json.py \
  -u "postgresql://user:pass@host:5432/dbname" \
  -o backend/
```

**Output:** `backend/documents.json` containing all documents with:
- Document metadata (title, fileName, fileSize, mimeType, createdAt)
- Base64-encoded binary content
- Upload user information

#### Import (Production)
```bash
cd /opt/hlas/backend
python3 sync_documents_json_to_postgres.py \
  -u "postgresql://user:pass@host:5432/dbname" \
  -f documents.json
```

**Operation:**
1. Reads documents from `documents.json`
2. Deletes existing documents for each club (clean slate)
3. Inserts documents with base64 content decoded back to binary
4. Preserves all metadata and creation timestamps

### Database Schema

Documents are stored in the `club_documents` table:
```sql
CREATE TABLE club_documents (
  id                  BIGSERIAL PRIMARY KEY,
  club_id             BIGINT NOT NULL REFERENCES clubs(id),
  title               VARCHAR(255) NOT NULL DEFAULT '',
  file_name           VARCHAR(512) NOT NULL DEFAULT '',
  file_ext            VARCHAR(16) NOT NULL DEFAULT '',
  mime_type           VARCHAR(128) NOT NULL DEFAULT 'application/octet-stream',
  file_size           BIGINT NOT NULL DEFAULT 0,
  file_data           BYTEA NOT NULL,           -- Binary content
  uploaded_by_user_id BIGINT REFERENCES app_users(id),
  created_at          TIMESTAMPTZ NOT NULL DEFAULT NOW(),
  updated_at          TIMESTAMPTZ NOT NULL DEFAULT NOW()
)
```

### JSON Structure

```json
{
  "CTC": [
    {
      "title": "Catch & Release Guidelines 2026",
      "fileName": "CTC_CR_2026.pdf",
      "fileExt": ".pdf",
      "fileSize": 245559,
      "mimeType": "application/pdf",
      "uploadedBy": 224,
      "createdAt": "2026-05-13T19:49:41.183344+00:00",
      "fileContent": "JVBERi0xLjYNJeLjz9MNC..."  // Base64 encoded binary
    }
  ],
  "GAAFFS": [
    // ... more documents
  ]
}
```

### Command Line Options

**Export Script:**
```bash
python3 sync_documents_postgres_to_json.py [OPTIONS]

Options:
  -u, --database-url URL    PostgreSQL connection URL
  -o, --output DIR          Output directory for documents.json (default: ./)
  -v, --verbose             Verbose output (default: True)
  -q, --quiet               Suppress output
```

**Import Script:**
```bash
python3 sync_documents_json_to_postgres.py [OPTIONS]

Options:
  -u, --database-url URL    PostgreSQL connection URL
  -f, --file PATH           Path to documents.json (default: ./documents.json)
  -d, --dry-run             Preview changes without applying
  -v, --verbose             Verbose output (default: True)
  -q, --quiet               Suppress output
```

### Production Deployment Workflow

1. **Development Environment:**
   ```bash
   # Export documents after uploading new files
   python3 backend/sync_documents_postgres_to_json.py \
     -u "postgresql://hlas:hlas@localhost:5433/hlas" \
     -o backend/
   
   # Verify documents.json was created
   git add backend/documents.json
   git commit -m "Sync documents from PostgreSQL"
   git push
   ```

2. **Production Server (Fresh Build):**
   ```bash
   # After database migrations run
   cd /opt/hlas
   
   # Restore documents from JSON
   python3 backend/sync_documents_json_to_postgres.py \
     -u "postgresql://user:pass@prod-host:5432/hlas" \
     -f backend/documents.json
   ```

3. **Production Server (Dry Run - Recommended First):**
   ```bash
   python3 backend/sync_documents_json_to_postgres.py \
     -u "postgresql://user:pass@prod-host:5432/hlas" \
     -f backend/documents.json \
     --dry-run
   ```

### Safety Features

- **Dry Run Mode** - Test imports without making changes
- **Clean Slate** - Existing documents are cleared before import to avoid conflicts
- **Verbose Logging** - Clear feedback on what's happening
- **Base64 Encoding** - Binary-safe JSON storage with no corruption risk

### Current Documents Synced

The following documents are currently synced for CTC club:
1. ✅ Catch & Release Guidelines 2026 (245KB PDF)
2. ✅ CTC Fishery Map 2026 (548KB PDF)
3. ✅ Membership Application 2026 (405KB DOCX)
4. ✅ C_Beat_Parking_v.2025 (158KB PDF)

All stored in: `backend/documents.json`

---

## Integration with Existing Systems

### Field Order Settings
Both sorting and Actions column visibility follow field order rules:
- Column visibility is controlled by the per-club `club_field_order` record in PostgreSQL (falls back to `field_order.json`)
- Sort arrows only appear when user clicks to sort
- Actions column is **always visible** (not controlled by Field Order)

### Migration Notes

**For Existing Deployments:**
1. No database migrations required - documents already use existing `club_documents` table
2. Sorting is purely frontend JavaScript - no backend changes
3. Table layout changes are CSS/template only

**For New Deployments:**
1. If database doesn't have `club_documents` table, run migrations:
   ```bash
   cd backend
   alembic upgrade head
   ```
2. Restore documents from JSON:
   ```bash
   python3 sync_documents_json_to_postgres.py -f documents.json
   ```

---

## Testing

### Sorting Test Procedure
1. Navigate to Home Page
2. Click column headers (Date, Category, Update, Title, Size)
3. Verify table rows reorder correctly
4. Click again to verify direction reverses
5. Verify Actions column is not clickable for sorting

### Documents Sync Test
```bash
# Test export
python3 backend/sync_documents_postgres_to_json.py \
  -u "postgresql://hlas:hlas@localhost:5433/hlas" \
  -q

# Verify file created
ls -lh backend/documents.json

# Test import (dry run)
python3 backend/sync_documents_json_to_postgres.py \
  -u "postgresql://..." \
  -f backend/documents.json \
  -d

# If dry run looks good, run actual import
python3 backend/sync_documents_json_to_postgres.py \
  -u "postgresql://..." \
  -f backend/documents.json
```

---

## Rollback Instructions

### Sorting & Table Layout
These are frontend-only changes. To rollback:
1. Revert `frontend/src/components/HomeView.vue` to previous version
2. No database changes, no API changes

### Documents Sync System
To remove the sync system:
1. Delete `backend/sync_documents_postgres_to_json.py`
2. Delete `backend/sync_documents_json_to_postgres.py`
3. Delete `backend/documents.json` (or keep for records)
4. Documents remain in PostgreSQL; just won't be synced

---

## Version Information

- **Date:** May 13, 2026
- **Components Updated:** 
  - Frontend: HomeView.vue (sorting, table restructure)
  - Backend: New sync scripts for documents
- **Database Schema:** No changes required
- **API Changes:** None
- **Breaking Changes:** None

---

## Related Documentation

- [Beats Sync System](README.md#beats-sync)
- [Field Order Configuration](README.md#field-order-configuration)
- [Backup System](BACKUP_SYSTEM.md)
- [Database Migrations](DEPLOYMENT.md#database-migrations)

---

## Questions or Issues

For troubleshooting:
1. Check verbose output: Run sync scripts without `-q` flag
2. Verify DATABASE_URL is correct if connection fails
3. Ensure PostgreSQL port is accessible (default: 5433 on hlastest)
4. Check that `alembic upgrade head` was run to create tables

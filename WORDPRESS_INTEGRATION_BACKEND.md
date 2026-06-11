# HLaS WordPress Integration - Backend API Documentation

### Language Convention

- User-facing copy and documentation in this repository should default to British English spelling (for example: recognised, localisation, authorised).
- Keep external API/library identifiers unchanged where spelling is fixed by the platform (for example: `wp_localize_script`).

## Phase 1: Backend Preparation ✓ COMPLETE

### New Headless API Endpoints

The following endpoints are now available for WordPress integration at `/api/headless/`:

#### 1. GET `/api/headless/beat-details/<club_short_name>`

Retrieves beat details for a club in clean, unstyled JSON format. This is a members-only endpoint with authentication required.

**Parameters:**
- `club_short_name` (path): Club abbreviation (e.g., "CTC", "GAAFFS")

**Authentication Required:**
- X-WordPress-API-Key header (recommended for WordPress plugin), OR
- HLaS member token (Authorization: Bearer)

**Authenticated Response Format (200 OK):**
```json
{
  "club": {
    "id": 1,
    "name": "Club Taylor Club",
    "short_name": "CTC",
    "description": "..."
  },
  "beats": [
    {
      "id": 1,
      "name": "Upper Beat",
      "beat_id": "UB001",
      "position": "1",
      "description": "Description here",
      "detailed_description": "Longer description",
      "river": "River Name",
      "coordinates": {
        "upstream": {
          "latitude": 57.123,
          "longitude": -2.456
        },
        "downstream": {
          "latitude": 57.122,
          "longitude": -2.457
        }
      },
      "parking_locations": ["Grid ref here"],
      "waypoints": [{...}]
    }
  ]
}
```

**Non-Authenticated Response Format (403 Forbidden):**
```json
{
  "members_only": true,
  "club": {
    "name": "Club Taylor Club",
    "short_name": "CTC"
  },
  "message": "This information is only available to members of Club Taylor Club. Please contact admin@example.com for any membership enquiries or questions on using the website."
}
```

**Usage Example (with API Key):**
```bash
curl -X GET "https://api.hlas.local/api/headless/beat-details/CTC" \
  -H "X-WordPress-API-Key: your-api-key"
```

**Usage Example (with Bearer Token):**
```bash
curl -X GET "https://api.hlas.local/api/headless/beat-details/CTC" \
  -H "Authorization: Bearer <jwt_token>"
```

---

#### 2. GET `/api/headless/catch-returns/<club_short_name>`

Retrieves catch returns for the authenticated member. This is a members-only endpoint with authentication required.

**Parameters:**
- `club_short_name` (path): Club abbreviation
- `limit` (query, optional): Maximum results (default: 50, max: 200)
- `offset` (query, optional): Pagination offset (default: 0)

**Authentication Required:**
- HLaS member token (Authorization: Bearer), OR
- WordPress API key (X-WordPress-API-Key)

**Authenticated Response Format (200 OK):**
```json
{
  "club": {
    "id": 1,
    "name": "Club Taylor Club",
    "short_name": "CTC"
  },
  "member": {
    "id": 123
  },
  "pagination": {
    "limit": 50,
    "offset": 0,
    "total": 150
  },
  "returns": [
    {
      "id": 456,
      "session_date": "2026-05-14",
      "beat_id": "UB001",
      "fish_count": {
        "small_trout": 2,
        "medium_trout": 1,
        "large_trout": 0,
        "small_grayling": 1,
        "medium_grayling": 0,
        "large_grayling": 0,
        "other_fish": 0
      },
      "notes": {
        "flies_used": "Olive Dun",
        "weather": "Cloudy, wind from west",
        "predator_damage": "None"
      },
      "created_at": "2026-05-14T10:30:00"
    }
  ]
}
```

**Non-Authenticated Response Format (403 Forbidden):**
```json
{
  "members_only": true,
  "club": {
    "name": "Club Taylor Club",
    "short_name": "CTC"
  },
  "message": "This information is accessible only by members of Club Taylor Club, please contact admin@example.com with any issues or enquiries as to how to access the site."
}
```

**Usage Example:**
```bash
curl -X GET "https://api.hlas.local/api/headless/catch-returns/CTC?limit=10" \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Accept: application/json"
```

---

#### 3. POST `/api/headless/catch-returns/<club_short_name>`

Creates a new catch return entry.

**Parameters:**
- `club_short_name` (path): Club abbreviation

**Authentication Required:** Same as GET endpoint

**Request Body:**
```json
{
  "session_date": "2026-05-14",
  "beat_id": "UB001",
  "fish_count": {
    "small_trout": 2,
    "medium_trout": 1,
    "large_trout": 0,
    "small_grayling": 0,
    "medium_grayling": 0,
    "large_grayling": 0,
    "other_fish": 0
  },
  "flies_used": "Olive Dun",
  "weather_conditions": "Cloudy",
  "predator_damage": "None"
}
```

**Response Format:**
```json
{
  "status": "success",
  "catch_return_id": 789,
  "session_date": "2026-05-14"
}
```

**HTTP Status Codes:**
- `201`: Catch return created successfully
- `400`: Invalid request data
- `401`: Unauthorized (missing authentication)
- `403`: User not a member of the club
- `404`: Club not found
- `500`: Server error

---

### Authentication Modes

#### Mode 1: HLaS Member Token (Preferred)
```bash
curl -H "Authorization: Bearer <token>"
```

#### Mode 2: WordPress Nonce + API Key
```bash
curl -H "X-WordPress-Nonce: <nonce>" \
     -H "X-WordPress-API-Key: <api_key>" \
     -H "X-WP-User-ID: <user_id>"
```

### Configuration

#### Required Environment Variables
```bash
# WordPress API key for nonce verification
export WORDPRESS_API_KEY="your-shared-secret-key"

# Database (already configured)
export DATABASE_URL="postgresql://user:pass@host/dbname"
```

#### Optional Environment Variables
```bash
# WordPress domain for CORS (if restricting)
export WORDPRESS_DOMAIN="https://example.com"
```

---

## CORS Configuration

CORS is globally enabled on all routes. The Flask app is configured to accept requests from any origin by default via `flask-cors.CORS(app)`.

### To Restrict CORS to Specific WordPress Domain

Update in `backend/app.py`:
```python
CORS(app_instance, 
     origins=os.getenv('WORDPRESS_DOMAIN', '*'),
     allow_headers=['Authorization', 'Content-Type', 'X-WordPress-Nonce', 'X-WordPress-API-Key'])
```

---

## Testing the API

### 1. Test Beat Details (Public, No Auth)
```bash
curl http://localhost:5000/api/headless/beat-details/CTC
```

### 2. Test Catch Returns (Requires Auth)
First, obtain a member token via the login endpoint, then:
```bash
curl -H "Authorization: Bearer <token>" \
     http://localhost:5000/api/headless/catch-returns/CTC
```

### 3. Test with WordPress API Key
```bash
curl -H "X-WordPress-API-Key: secret-key" \
     -H "X-WP-User-ID: 123" \
     http://localhost:5000/api/headless/catch-returns/CTC
```

---

## Next Steps: WordPress Plugin Development

The backend API is complete and ready for consumption. Next phase:

1. **Create WordPress plugin boilerplate** with:
   - Plugin activation/deactivation hooks
   - Shortcode registration
   - JavaScript API client

2. **Build Beat Details shortcode:**
   - `[hlas-beat-details club="CTC"]`
   - Display beats in a table/grid
   - Allow Elementor to style the output

3. **Build Catch Return features:**
   - `[hlas-catch-return club="CTC"]` - Display recent catches
   - `[hlas-catch-return-form club="CTC"]` - Form to log new catch
   - Authentication integration

See `WORDPRESS_PLUGIN_SETUP.md` for plugin development details.

---

## File Changes Summary

### Backend Files Modified:
- `/opt/hlas/backend/routes/headless_routes.py` - NEW
- `/opt/hlas/backend/routes/__init__.py` - Added headless blueprint import
- `/opt/hlas/backend/app.py` - Registered headless blueprint

### Date: 2026-05-14
### Status: ✓ Phase 1 Complete

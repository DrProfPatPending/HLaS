# Club Mini Sites Feature Guide

## Overview

Club Mini Sites are optional, public-facing marketing websites for individual clubs. Each club can independently enable/disable and customize their mini site, which appears before the login screen and is accessible to anyone without authentication.

**Key Characteristics:**
- **Per-club configuration** - Enabled/disabled on a club-by-club basis
- **Public access** - No authentication required; accessible worldwide
- **Device-responsive** - Desktop: full experience; Mobile/Responsive: placeholder with desktop prompt
- **Customizable** - Clubs can set title, tagline, description, and hero image
- **Future-extensible** - Ready for galleries, event calendars, contact forms
- **API-accessible** - Public endpoint for external integrations

---

## Quick Start

### 1) Enable Mini Site for Your Club

1. Log in as club admin
2. Navigate to **Club Settings**
3. Scroll to **Club Mini Site** section
4. Check **Enable Mini Site**
5. Fill in:
   - **Site Title** - Display name (e.g., "Cambridge Trout Club")
   - **Tagline** - Subtitle (e.g., "Premier fly fishing destination")
   - **Description** - Club overview (max 500 chars recommended)
   - **Hero Image URL** - External URL to banner image (CDN, S3, etc.)
6. Click **Save Settings**

### 2) View Your Mini Site

- **Desktop:** `https://yourdomain.org/club/{CLUB_CODE}/`
- **Mobile:** Same URL shows placeholder with link to desktop
- **Login:** Always available at `https://yourdomain.org/club/{CLUB_CODE}/login/`

### 3) Disable Mini Site

1. Go to **Club Settings** → **Club Mini Site**
2. Uncheck **Enable Mini Site**
3. Click **Save Settings**
4. Users visiting `/club/{CLUB_CODE}/` will be redirected to login

---

## Architecture

### Database Schema

```sql
CREATE TABLE club_mini_sites (
    id            BIGSERIAL PRIMARY KEY,
    club_id       BIGINT NOT NULL UNIQUE REFERENCES clubs(id) ON DELETE CASCADE,
    enabled       BOOLEAN NOT NULL DEFAULT false,
    title         VARCHAR(255) NOT NULL DEFAULT '',
    tagline       VARCHAR(255) NOT NULL DEFAULT '',
    hero_image_url VARCHAR(255) NOT NULL DEFAULT '',
    description   TEXT NOT NULL DEFAULT '',
    pages         JSONB NOT NULL DEFAULT '[]',           -- Reserved for future use
    social_links  JSONB NOT NULL DEFAULT '{}',           -- Facebook, Twitter, Instagram URLs
    created_at    TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at    TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX ix_club_mini_sites_club_id ON club_mini_sites (club_id);
CREATE INDEX ix_club_mini_sites_enabled ON club_mini_sites (enabled);
```

### API Architecture

#### Public Endpoints (No Auth Required)

**GET `/api/club/{club_code}/mini-site`**

Public endpoint to fetch mini site configuration.

**Request:**
```bash
curl -H "Content-Type: application/json" \
  "https://yourdomain.org/api/club/CTC/mini-site"
```

**Response (Enabled):**
```json
{
  "id": 42,
  "club_id": 5,
  "enabled": true,
  "title": "Cambridge Trout Club",
  "tagline": "Premier fly fishing destination",
  "hero_image_url": "https://cdn.example.com/hero.jpg",
  "description": "Established 1925. Fly fishing only on pristine chalk streams.",
  "pages": [],
  "social_links": {
    "twitter": "https://twitter.com/cambridgetrout",
    "facebook": "https://facebook.com/cambridgetrout"
  }
}
```

**Response (Not Enabled/Configured):**
```json
{
  "enabled": false,
  "error": "Mini site not configured for this club"
}
```

#### Authenticated Endpoints (Club Admin+)

**GET `/api/mini-site?club={CLUB_CODE}`**

Fetch mini site configuration for the authenticated user's club.

**Response:** (Same as public endpoint for enabled sites)

**PUT `/api/mini-site?club={CLUB_CODE}`**

Update mini site configuration.

**Request Body:**
```json
{
  "club": "CTC",
  "enabled": true,
  "title": "Cambridge Trout Club",
  "tagline": "Premier fly fishing destination",
  "description": "Established 1925...",
  "hero_image_url": "https://cdn.example.com/hero.jpg"
}
```

**Response:**
```json
{
  "success": true,
  "enabled": true,
  "title": "Cambridge Trout Club",
  ...
}
```

**Permissions:**
- Requires `club.update` (Club Admin+ role)
- Limited to authenticated users' own club (except app admins)

---

## Frontend Components

### Component Hierarchy

```
MiniSiteView.vue (Router/main entry)
├── MiniSiteContainer.vue (Main wrapper)
│   ├── MiniSiteDesktop.vue (Full site, desktop only)
│   │   ├── MiniSiteNavigation (top nav)
│   │   ├── MiniSiteHero (hero section)
│   │   ├── ContentSections (home, about, beats)
│   │   └── MiniSiteFooter (social links, copyright)
│   │
│   └── MiniSitePlaceholder.vue (Mobile/responsive fallback)
│       ├── Responsive nav
│       ├── Mobile-friendly info
│       └── "View on Desktop" prompt
│
└── LoginView (For /login/ route)
```

### Responsive Breakpoint

- **Desktop (768px+):** Full mini site experience
- **Mobile (<768px):** Responsive placeholder with desktop redirect prompt

### Entry Point Detection

`frontend/src/main.js` detects route patterns:
- `/club/{clubCode}/` → Loads `MiniSiteView`
- All other routes → Loads main `App` (authenticated portal)

---

## Admin UI Integration

### Club Settings Page

**Location:** Member UI → Club Settings

**Mini Site Section:**
- **Toggle:** Enable/Disable
- **Title field** - 255 chars max
- **Tagline field** - 255 chars max
- **Description field** - Text area, 500+ chars supported
- **Hero Image URL** - External URL input
- **Device info** - Shows `/club/{CODE}/` URL and access patterns
- **Status** - Displays if enabled or not configured

**Permissions:** Club Admin+ (requires `club.update`)

---

## Styling and Customization

### Desktop Mini Site (`MiniSiteDesktop.vue`)

**Color Scheme:**
- Primary accent: `#2d6a45` (trout-green)
- Hero overlay dark: `rgba(0, 0, 0, 0.3)`
- Header background: gradient from `#1a472a` to `#2d6a45`
- CTA button: `#ff6b6b` (red accent)

**Typography:**
- Sans-serif stack: `-apple-system, BlinkMacSystemFont, Segoe UI, Roboto, ...`
- Navigation links: 0.95rem, white
- Navigation logo: 100px height, auto width (maintains aspect ratio)
- Page headers: 14pt bold, white, centered
- Page subheadings: 10pt, white, 90% opacity
- Content: 1rem, #333

**Layout:**
- Sticky navigation header with prominent club logo
- Compact page header: 100px height (90px mobile) with centered title
- Compact hero section: 100px height with background image overlay
- Background image section: Full-width responsive, 100% width with max-width 1200px
- Content container: max-width 1200px, centered
- Mobile fallback: Responsive CSS at 768px breakpoint

### Mobile & Responsive Design

**Responsive Breakpoints:**
- **Desktop (768px+):** Full mini site with navigation, hero, and content sections
- **Mobile (<768px):** Placeholder with option to view on desktop

**Mobile Color Scheme:**
- Same primary green as desktop
- Light backgrounds for readability
- Soft borders for card-like sections

**Mobile Layout:**
- Full width responsive (100vw)
- Touch-friendly buttons
- Vertical stack layout
- Large readable text
- Compact headers (90px height)
- Responsive tables (2-column at ≤1000px)

---

## Future Enhancements

### Phase 2: Content Management

- Admin UI for adding/editing custom pages
- Rich text editor for page content
- Gallery/media management
- Page publishing workflow (draft/published)

### Phase 3: Advanced Features

- Event calendar integration
- Member testimonials section
- Contact form with club-specific email routing
- Newsletter signup integration
- Member portal shortcut for known members

### Phase 4: Analytics & SEO

- Page view tracking (privacy-respecting)
- SEO metadata configuration (title, description, open graph)
- Sitemap generation
- Meta tag customization per page

---

## Troubleshooting

### Mini Site Not Showing

1. Verify mini site is **enabled** in Club Settings
2. Check URL format: `/club/{clubCode}/` (case-sensitive)
3. Verify `club_mini_sites` table exists (check migrations ran)
4. Check browser console for API fetch errors

### Image Not Loading

1. Verify hero image URL is publicly accessible
2. Test URL directly in browser
3. Check CORS headers if using external CDN
4. Use HTTPS URLs for production

### Mobile Shows Placeholder on Desktop

1. Check CSS media query breakpoint (should be 768px)
2. Test browser responsive mode (press F12 → toggle device mode)
3. Check window.innerWidth in console for actual breakpoint

### Admin Can't Save Mini Site Config

1. Verify user has Club Admin+ role
2. Check API response for error details (F12 → Network tab)
3. Verify `/mini-site` endpoint is registered (check app.py imports)
4. Look for permission errors in logs

---

## Security & Best Practices

### Data Validation

- Title/tagline: Limited to 255 chars, XSS-safe Vue escaping
- Description: Text only, no HTML/Markdown for now
- Hero image URL: Validated as proper URL format
- Social links: Restricted to known platforms

### Permissions

- **Read public config:** No authentication required
- **Update config:** Requires `club.update` (Club Admin+ only)
- **Disable/enable:** Same permission as update

### URL Safety

- All external URLs (hero image, social links) in `href` attributes
- Links open with `target="_blank" rel="noopener noreferrer"`
- Prevents clickjacking and prevents referrer leakage

---

## Database Maintenance

### Backup Considerations

- `club_mini_sites` table is included in full database backups
- Mini site configs export/import safely with club data
- No binary data (images stored externally via URL)

### Indexing

```sql
-- Automatic creation on migration:
CREATE INDEX ix_club_mini_sites_club_id ON club_mini_sites (club_id);
CREATE INDEX ix_club_mini_sites_enabled ON club_mini_sites (enabled);

-- Query optimization:
-- Lookup by club: O(1) via unique club_id index
-- Find enabled sites: O(log n) via enabled index
```

### Cascading Deletes

- If club is deleted, mini site config is automatically deleted (ON DELETE CASCADE)
- No orphaned records will accumulate

---

## Configuration Examples

### Minimal Configuration

```json
{
  "enabled": true,
  "title": "Fishing Club",
  "tagline": "Local fishing community",
  "description": "",
  "hero_image_url": ""
}
```

### Full Configuration

```json
{
  "enabled": true,
  "title": "Cambridge Trout Club",
  "tagline": "Premier fly fishing on chalk streams",
  "description": "Established 1925, CTC offers exclusive access to 15 miles of pristine chalk stream fishing. Members enjoy beat allocation, instruction, and community events.",
  "hero_image_url": "https://cdn.example.com/ctc-hero-2026.jpg",
  "social_links": {
    "facebook": "https://facebook.com/cambridgetroutclub",
    "twitter": "https://twitter.com/cambridgetrout",
    "instagram": "https://instagram.com/cambridgetrout"
  }
}
```

---

## API Integration Examples

### Fetch Mini Site Config (External Service)

```javascript
// Get mini site for public display
async function fetchClubMiniSite(clubCode) {
  try {
    const response = await fetch(
      `https://yourdomain.org/api/club/${clubCode}/mini-site`
    );
    const data = await response.json();
    
    if (data.enabled) {
      console.log(`Club: ${data.title}`);
      console.log(`About: ${data.description}`);
      // Render mini site...
    } else {
      console.log('Mini site not configured');
    }
  } catch (error) {
    console.error('Failed to fetch mini site:', error);
  }
}
```

### Update Mini Site (Admin Dashboard)

```javascript
// Update from authenticated admin panel
async function updateMiniSite(clubCode, config) {
  const response = await fetch(
    `/api/mini-site?club=${clubCode}`,
    {
      method: 'PUT',
      headers: {
        'Content-Type': 'application/json',
        'Authorization': `Bearer ${sessionToken}`
      },
      body: JSON.stringify({
        club: clubCode,
        ...config
      })
    }
  );
  
  if (response.ok) {
    console.log('Mini site updated');
  } else {
    console.error('Update failed:', await response.json());
  }
}
```

---

## See Also

- [DEPLOYMENT.md](DEPLOYMENT.md) - Full deployment guide
- [README.md](README.md) - Project overview
- [frontend/src/components/MiniSite/](frontend/src/components/MiniSite/) - Component source files
- [backend/routes/mini_site_routes.py](backend/routes/mini_site_routes.py) - Backend API implementation

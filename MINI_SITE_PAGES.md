# Mini Site Multi-Page System Implementation

## Overview

The mini site system has been extended to support multiple template-based pages with full admin control. Clubs can now create a comprehensive marketing website with customizable pages while maintaining responsive mobile views.

## Architecture

### Page Templates

Six pre-defined page templates are available:

1. **Home** (Mandatory)
   - Hero image with headline and club name
   - Feature cards highlighting club benefits
   - Welcome section
   - Cannot be disabled
   - Accessed at: `/club/{clubCode}/`

2. **About Us** (Optional)
   - Club history, mission, and values
   - Customizable content section
   - Accessed at: `/club/{clubCode}/about/`

3. **Our Waters** (Optional)
   - Fishing waters and beats information
   - Water details, access information
   - Conservation guidelines
   - Accessed at: `/club/{clubCode}/waters/`

4. **News** (Optional)
   - Club updates, announcements, news feeds
   - Water conditions and reports
   - Upcoming events listing
   - Accessed at: `/club/{clubCode}/news/`

5. **Join** (Optional)
   - Membership benefits and features
   - How to apply process
   - Call-to-action for applications
   - Accessed at: `/club/{clubCode}/join/`

6. **Contact Us** (Optional)
   - Contact information (email, phone, address)
   - Contact form
   - Social media links
   - Accessed at: `/club/{clubCode}/contact/`

## Backend Implementation

### Database

**Table:** `club_mini_sites`

**New/Updated Columns:**
- `pages` (JSONB): Array of page configurations
  ```json
  [
    {
      "id": "home",
      "type": "home",
      "title": "Home",
      "enabled": true,
      "canDisable": false,
      "headline": "Welcome to {Club Name}...",
      "content": ""
    },
    {
      "id": "about",
      "type": "about",
      "title": "About Us",
      "enabled": true,
      "canDisable": true,
      "content": ""
    }
  ]
  ```

### Files Created

#### `backend/mini_site_pages.py`
Centralized page template definitions and utilities:
- `PAGE_TEMPLATES`: Dictionary of template metadata
- `get_default_pages()`: Returns fresh copy of all templates
- `normalize_pages_config(raw_pages, club_name)`: Validates and merges user config with templates
- `get_enabled_pages(pages_config)`: Filters to enabled pages only

**Key Function: `normalize_pages_config()`**
```python
# Input: Array of page IDs from frontend (or page objects)
pages_input = ['home', 'about', 'waters', 'news', 'join', 'contact']

# Or with explicit enable/disable:
pages_input = [
  {'id': 'home', 'enabled': True},
  {'id': 'about', 'enabled': False},
  ...
]

# Output: Normalized full page configuration
normalized_pages = normalize_pages_config(pages_input, 'Cambridge Trout Club')
```

### API Endpoints

#### GET `/api/club/{code}/mini-site` (Public)
Returns mini site configuration with normalized pages.

**Response:**
```json
{
  "id": 1,
  "enabled": true,
  "title": "Cambridge Trout Club",
  "tagline": "Premier fly fishing destination",
  "description": "...",
  "hero_image_url": "https://...",
  "pages": [
    {
      "id": "home",
      "type": "home",
      "title": "Home",
      "enabled": true,
      "canDisable": false
    },
    {
      "id": "about",
      "type": "about",
      "title": "About Us",
      "enabled": true,
      "canDisable": true
    }
  ]
}
```

#### PUT `/api/mini-site?club={code}` (Authenticated)
Updates mini site configuration with page selection.

**Request Body:**
```json
{
  "enabled": true,
  "title": "Cambridge Trout Club",
  "tagline": "Premier fly fishing destination",
  "description": "A leading fly fishing club...",
  "hero_image_url": "https://...",
  "pages": ["home", "about", "waters", "join", "contact"]
}
```

**Processing:**
- Frontend sends array of enabled page IDs
- Backend converts to page objects with enabled flag
- `normalize_pages_config()` validates and normalizes
- Only normalized config stored in database

## Frontend Implementation

### Page Template Components

#### `MiniSiteHome.vue`
- Hero section with image and headline
- Club welcome section
- Feature cards (Exclusive Access, Community, Learning)
- Props: `clubName`, `headline`, `tagline`, `description`, `heroImage`
- Automatic headline generation if not provided

#### `MiniSiteAbout.vue`
- Page header with gradient background
- About content (customizable or default)
- Default values with club values section
- Props: `clubName`, `content`, `subheading`

#### `MiniSiteWaters.vue`
- Fishing waters and beats information
- Beat cards with details (type, access, species)
- Fishing guidelines
- Props: `clubName`, `content`, `subheading`

#### `MiniSiteNews.vue`
- News items with date badges
- Updates and announcements
- Customizable content section
- Props: `clubName`, `content`, `subheading`

#### `MiniSiteJoin.vue`
- Membership benefits in grid layout
- Application steps
- CTA button for applications
- Props: `clubName`, `content`, `subheading`

#### `MiniSiteContact.vue`
- Contact information display (email, phone, address)
- Contact form with name, email, subject, message
- Form submission handler (stub for future API integration)
- Props: `clubName`, `content`, `subheading`, `contactEmail`, `contactPhone`, `contactAddress`

### Main Components

#### `MiniSiteDesktop.vue` (Complete Redesign)
**Header Structure:**
- **Left:** Club logo or name (from `logo_url`)
- **Center:** Dynamic navigation menu from enabled pages
- **Right:** "Log In" button with red styling

**Features:**
- Dynamic page rendering based on `currentPage`
- Component selection via page ID
- Page content passed as props
- Responsive navigation
- Sticky header positioning
- Page-specific content rendering

**Props:**
- `miniSite`: Configuration object with pages array
- `clubCode`: Club code for routing
- `initialPage`: Starting page (default: 'home')

**Data Flow:**
```
enabled pages → nav links → click → currentPage update → component switch
```

#### `MiniSiteContainer.vue` (Updated)
**URL-Based Routing:**
```
/club/CTC/           → home page
/club/CTC/about/     → about page
/club/CTC/waters/    → waters page
/club/CTC/contact/   → contact page
```

**Logic:**
1. Parse current page from URL path
2. Fetch mini site config from API
3. Validate page is enabled
4. Pass initial page to MiniSiteDesktop
5. Redirect to home if page disabled

### Admin UI Enhancement

#### `ClubSettings.vue` (New Section)
**Pages Configuration:**
- Checkboxes for each template page
- Home page checkbox disabled (always enabled badge)
- Pages grid layout (responsive)
- Save with mini site config

**UI Features:**
- Page checkbox grid (repeats auto-fit minmax 150px)
- Disabled state for Home page
- Badge showing "Always enabled" for Home
- Hover states with border highlighting
- Visual distinction between mandatory and optional

**Data Handling:**
- `miniSite.pages`: Array of enabled page IDs
- Loaded from API normalized pages
- Sent to backend as array of IDs
- Converted server-side to page objects

## Routing and URLs

### Desktop Views
```
GET /club/CTC/              → MiniSiteContainer → MiniSiteDesktop (Home)
GET /club/CTC/about/        → MiniSiteContainer → MiniSiteDesktop (About)
GET /club/CTC/waters/       → MiniSiteContainer → MiniSiteDesktop (Waters)
GET /club/CTC/news/         → MiniSiteContainer → MiniSiteDesktop (News)
GET /club/CTC/join/         → MiniSiteContainer → MiniSiteDesktop (Join)
GET /club/CTC/contact/      → MiniSiteContainer → MiniSiteDesktop (Contact)
```

### Mobile Views
```
GET /club/CTC/*             → MiniSiteContainer → MiniSitePlaceholder
```
(All paths show placeholder with login redirect)

### Admin Access
```
/club/{code}/admin/settings → ClubSettings (with pages checkboxes)
```

## Data Flow

### Admin Updates Pages

1. **Admin checks/unchecks pages** in ClubSettings.vue
2. **Frontend collects enabled page IDs**: `['home', 'about', 'waters']`
3. **Save settings** sends PUT request:
   ```json
   {
     "club": "CTC",
     "pages": ["home", "about", "waters"]
   }
   ```
4. **Backend converts to page objects**:
   ```python
   pages_input = [{'id': 'home', 'enabled': True}, ...]
   ```
5. **normalize_pages_config() validates**
   - Ensures Home is always enabled
   - Merges with template metadata
   - Returns full normalized structure
6. **Stored in database** as JSONB
7. **Frontend fetches** GET `/api/club/CTC/mini-site`
8. **Response includes pages array** with full config
9. **MiniSiteDesktop filters** to `enabledPages`
10. **Navigation menu** displays only enabled pages

## Default Values

### Hero Image
- Falls back to river emoji placeholder if URL not provided
- Expected URL: External CDN or self-hosted image
- No file upload UI yet (future enhancement)

### Headline Text
- Automatic generation: `"Welcome to {Club Name} - a small fishing club which offers access to some of the prettiest rivers and finest fly fishing in the UK."`
- Can be overridden per club in future via admin UI

### Page Content
- Each page has default placeholder content
- Customizable content fields in database schema (future use)
- Contact page has empty form fields for club to populate

## Styling

### Color Scheme
- **Primary Green:** `#1a472a`, `#2d6a45` (club branded)
- **Accent Red:** `#ff6b6b` (buttons, highlights)
- **Backgrounds:** White, light grey `#f9f9f9`
- **Text:** Dark grey `#333`, medium grey `#555`

### Responsive Breakpoints
- **768px:** Mobile/responsive threshold
- **Below 768px:** MiniSitePlaceholder (mobile)
- **Above 768px:** Full MiniSiteDesktop (desktop)

### Navigation Header
- Sticky positioning (top: 0, z-index: 100)
- Green gradient background
- Logo left, menu center, login button right
- Flex layout with responsive reflow

## Future Enhancements

1. **Content Management**
   - Admin UI text editors for page content
   - Rich text editor for About, News, Join pages
   - Image uploads for Water details

2. **Contact Form Integration**
   - Backend endpoint for form submissions
   - Email notifications to club admin
   - Form validation and error handling

3. **Logo Management**
   - Logo upload to replace text branding
   - Club logo retrieval from existing club data
   - Responsive sizing

4. **Social Media Integration**
   - Social links editing in admin UI
   - Display social icons in footer
   - Share buttons on pages

5. **Analytics**
   - Page view tracking
   - User interaction monitoring
   - Form submission tracking

6. **SEO**
   - Meta tags per page
   - Open Graph data
   - Sitemap generation

7. **Content Localisation**
   - Multi-language support
   - Region-specific content

## Testing Checklist

- [ ] Admin can enable/disable pages in ClubSettings
- [ ] Page selection saves to database correctly
- [ ] GET `/api/club/{code}/mini-site` returns all pages with enabled status
- [ ] Navigation menu shows only enabled pages
- [ ] Disabled pages show 404 or redirect to home
- [ ] Home page cannot be disabled (checkbox stays checked)
- [ ] All page components render correctly with props
- [ ] Logo displays correctly (or placeholder)
- [ ] Login button navigates to `/club/{code}/login/`
- [ ] Mobile view shows placeholder
- [ ] Desktop view shows full mini site
- [ ] URL parsing detects current page correctly
- [ ] Different page IDs load correct components
- [ ] Form submission on Contact page works (when backend ready)
- [ ] Social links display if provided

## Migration Notes

### From Previous Version
- Existing mini sites automatically upgraded
- All pages enabled by default (backward compatible)
- No data loss in migration
- Legacy `hero_image_url` still supported

### Database Migration
- See: `backend/migrations/[timestamp]_club_mini_sites_table.py`
- `pages` column added as JSONB array
- Default migration includes all 6 pages enabled

## Example Configuration

### Full Example

**Database Entry:**
```json
{
  "id": 1,
  "club_id": 5,
  "enabled": true,
  "title": "Cambridge Trout Club",
  "tagline": "Where tradition meets fly fishing excellence",
  "description": "A leading fly fishing club with exclusive access to pristine chalk streams",
  "hero_image_url": "https://cdn.example.com/river.jpg",
  "pages": [
    {"id": "home", "type": "home", "title": "Home", "enabled": true, "canDisable": false},
    {"id": "about", "type": "about", "title": "About Us", "enabled": true, "canDisable": true},
    {"id": "waters", "type": "waters", "title": "Our Waters", "enabled": true, "canDisable": true},
    {"id": "news", "type": "news", "title": "News", "enabled": false, "canDisable": true},
    {"id": "join", "type": "join", "title": "Join", "enabled": true, "canDisable": true},
    {"id": "contact", "type": "contact", "title": "Contact Us", "enabled": true, "canDisable": true}
  ],
  "social_links": {
    "facebook": "https://facebook.com/cambridgetc",
    "twitter": "https://twitter.com/cambridgetc"
  }
}
```

**Frontend Sends To API:**
```json
{
  "club": "CTC",
  "enabled": true,
  "title": "Cambridge Trout Club",
  "pages": ["home", "about", "waters", "join", "contact"]
}
```

**API Response (GET):**
```json
{
  "enabled": true,
  "title": "Cambridge Trout Club",
  "hero_image_url": "...",
  "pages": [
    {"id": "home", "enabled": true, ...},
    ...
  ]
}
```

## Support & Troubleshooting

### Pages not showing in menu
- Check if mini site is enabled
- Verify pages are enabled in ClubSettings
- Check browser console for API errors

### Wrong page displaying
- Verify URL format: `/club/{code}/{page}/`
- Check if page ID is lowercase
- Confirm page is not disabled

### Styling issues
- Check that all page component CSS files loaded
- Verify hero image URL is valid
- Test in different browsers

### Form submission not working
- Check contact form endpoint (backend not yet implemented)
- Verify form fields match expected API format
- Check browser console for validation errors

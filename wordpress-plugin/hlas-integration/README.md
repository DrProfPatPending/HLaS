# HLaS Integration WordPress Plugin

A WordPress plugin that integrates HLaS (Hook Line and Sinker) with your WordPress site, allowing you to embed beat details, catch returns, and member-only content.

### Language Convention

- User-facing copy and documentation in this repository should default to British English spelling (for example: recognised, localisation, authorised).
- Keep external API/library identifiers unchanged where spelling is fixed by the platform (for example: `wp_localize_script`).

## Features

- **Beat Details**: Display fishing beat information from HLaS with customizable layouts
- **Catch Returns**: Show logged fishing catches for authenticated members
- **Catch Return Form**: Allow members to log new fishing sessions directly from WordPress
- **Member Authentication**: Integrate HLaS member authentication with WordPress
- **Responsive Design**: Works beautifully on desktop, tablet, and mobile devices
- **Elementor Compatible**: Shortcodes work seamlessly with Elementor page builder
- **Customizable Styling**: CSS custom properties allow WordPress themes to override colors

## Requirements

- WordPress 5.0 or higher
- PHP 7.4 or higher
- Active HLaS backend API instance
- MySQL 5.7+ or PostgreSQL 10+

## Installation

1. **Download the plugin**
   - Place the `hlas-integration` folder into `/wp-content/plugins/`
   
2. **Activate the plugin**
   - Go to WordPress Admin > Plugins
   - Find "HLaS Integration" and click "Activate"

3. **Configure API Settings**
   - Go to WordPress Admin > HLaS Settings
   - Enter your HLaS API URL (e.g., `https://api.fishing-club.com`)
   - Enter the API Key/Shared Secret (from your HLaS backend configuration)
   - Click "Save Changes"

## Configuration

### Basic Settings

**HLaS API URL**
- The base URL for your HLaS backend API
- Example: `https://api.example.com`
- Required: Yes

**API Key / Shared Secret**
- Shared secret for authentication between WordPress and HLaS
- Must match the `WORDPRESS_API_KEY` environment variable on the HLaS backend
- Required: For member-only features

**Enable Debug Mode**
- When enabled, API calls and errors are logged to the browser console
- Useful for troubleshooting
- Required: No

**Cache TTL (seconds)**
- How long to cache API responses
- Set to 0 to disable caching
- Default: 3600 seconds (1 hour)
- Recommended: 3600 for production, 0 for development

**Default Club Code**
- Club code used when URL does not include `/club/{CODE}`
- Example: `CTC`

**Club Theme Map (JSON)**
- Optional per-club visual tokens and assets, keyed by club code
- Supported keys per club: `primary_color`, `secondary_color`, `text_color`, `border_color`, `error_color`, `success_color`, `logo_url`, `hero_image_url`
- Applied as CSS custom properties on `body.hlas-club-{code}`

Example:

```json
{
	"CTC": {
		"primary_color": "#1a5490",
		"secondary_color": "#f5f5f5",
		"logo_url": "https://example.com/assets/ctc-logo.png"
	},
	"GAAFFS": {
		"primary_color": "#2d6a4f",
		"secondary_color": "#edf6f1",
		"hero_image_url": "https://example.com/assets/gaaffs-hero.jpg"
	}
}
```

### Ready-to-paste Club Theme Map

Paste this directly into **HLaS Settings → Club Theme Map (JSON)**:

```json
{
	"CTC": {
		"primary_color": "#1a5490",
		"secondary_color": "#f2f7fc",
		"text_color": "#1f2933",
		"border_color": "#cfd8e3",
		"error_color": "#b42318",
		"success_color": "#2e7d32",
		"logo_url": "https://wordpress.hlastest/wp-content/uploads/club-logos/ctc-logo.png",
		"hero_image_url": "https://wordpress.hlastest/wp-content/uploads/club-heroes/ctc-hero.jpg"
	},
	"GAAFFS": {
		"primary_color": "#1f6f43",
		"secondary_color": "#edf8f1",
		"text_color": "#1f2933",
		"border_color": "#c9e3d3",
		"error_color": "#b42318",
		"success_color": "#2e7d32",
		"logo_url": "https://wordpress.hlastest/wp-content/uploads/club-logos/gaaffs-logo.png",
		"hero_image_url": "https://wordpress.hlastest/wp-content/uploads/club-heroes/gaaffs-hero.jpg"
	},
	"LADFFA": {
		"primary_color": "#7a1f3d",
		"secondary_color": "#fbf0f4",
		"text_color": "#1f2933",
		"border_color": "#e9c8d3",
		"error_color": "#b42318",
		"success_color": "#2e7d32",
		"logo_url": "https://wordpress.hlastest/wp-content/uploads/club-logos/ladffa-logo.png",
		"hero_image_url": "https://wordpress.hlastest/wp-content/uploads/club-heroes/ladffa-hero.jpg"
	}
}
```

If your media URLs differ, keep the same JSON structure and only replace `logo_url` and `hero_image_url` values.

### Environment Variable Setup

On your HLaS backend server, ensure these environment variables are set:

```bash
export WORDPRESS_DOMAIN="https://your-wordpress-site.com"
export WORDPRESS_API_KEY="your-shared-secret-key"
```

## Usage

### Single Dynamic Club Landing Page

The plugin now supports a single dynamic landing route:

- `https://wordpress.hlastest/club/CTC/`
- `https://wordpress.hlastest/club/GAAFFS/`

Setup:

1. Create one WordPress page with slug `club` (title can be anything, e.g. "Club Landing").
2. Add HLaS shortcodes to that page (you can omit `club="..."` to use URL club context).
3. Go to **Settings → Permalinks** and click **Save Changes** once to refresh rewrite rules.

Route behavior:

- `/club/{CODE}/` is routed to the single `club` page.
- `{CODE}` is exposed to the plugin as club context and used for shortcode data + theme tokens.
- Explicit shortcode `club="..."` still overrides URL context when provided.

### Shortcodes

#### Club Name
Display the current club code dynamically. This is perfect for page titles, headings, or anywhere you want the active club name to show up:

```
[hlas-club-name]
```

**Attributes:**
- None required

**Examples:**
```
[hlas-club-name]              <!-- Outputs: CTC, GAAFFS, or LADFFA -->
```

**How it works:**
- On `https://wordpress.hlastest/club/CTC/` → outputs `CTC`
- On `https://wordpress.hlastest/club/GAAFFS/` → outputs `GAAFFS`
- Falls back to `Default Club Code` setting if no URL context is available

**Use on your page title:**
This shortcode is perfect for replacing that static "club" text. Instead of manually editing the page title each time, use this shortcode to automatically display whichever club the user is viewing.

#### Beat Details
Display fishing beat information for a club:

```
[hlas-beat-details]
```

**Attributes:**
- `club` (optional): Club abbreviation (e.g., "CTC", "GAAFFS")
- `style` (optional): Display style - "table" (default) or "grid"

If `club` is omitted, the plugin resolves club in this order:
1. `club` query parameter (`?club=GAAFFS`)
2. URL path segment (`/club/GAAFFS/...`)
3. `Default Club Code` setting

**Examples:**
```
[hlas-beat-details club="CTC" style="table"]
[hlas-beat-details club="GAAFFS" style="grid"]
```

**Note:** This is a members-only shortcode. The API key must be configured in WordPress settings for the shortcode to work. Non-authenticated requests will display a message: "This information is only available to members of {Club}. Please contact {admin_email} for membership enquiries or questions on using the website."

#### Catch Returns List
Display recent catch returns for the logged-in user:

```
[hlas-catch-returns]
```

**Attributes:**
- `club` (optional): Club abbreviation
- `limit` (optional): Number of results to display (default: 10, max: 100)
- `style` (optional): Display style - "table" (default) or "timeline"

**Examples:**
```
[hlas-catch-returns club="CTC" limit="20"]
[hlas-catch-returns club="CTC" limit="5" style="timeline"]
```

**Note:** Requires user to be logged in and authenticated with HLaS. Non-authenticated users will see a message: "This information is accessible only by members of {Club}, please contact {admin_email} with any issues or enquiries as to how to access the site."

#### Catch Return Form
Display a form for users to log new fishing sessions:

```
[hlas-catch-return-form]
```

**Attributes:**
- `club` (optional): Club abbreviation

**Example:**
```
[hlas-catch-return-form club="CTC"]
```

**Note:** Requires user to be logged in and authenticated with HLaS

### In Elementor

1. Add a "Text" or "HTML" widget to your page
2. Paste the shortcode into the widget content
3. Update and view the page

## Styling

The plugin uses CSS custom properties that can be overridden by your WordPress theme:

```css
:root {
	--hlas-primary-color: #0073aa;
	--hlas-secondary-color: #f0f0f0;
	--hlas-text-color: #333;
	--hlas-border-color: #ddd;
	--hlas-error-color: #d32f2f;
	--hlas-success-color: #388e3c;
	--hlas-spacing: 16px;
	--hlas-border-radius: 4px;
}
```

### Custom Styling Example

Add this to your theme's `style.css` or via Elementor Custom CSS:

```css
:root {
	--hlas-primary-color: #1a5490;
	--hlas-secondary-color: #f5f5f5;
	--hlas-spacing: 20px;
}

.hlas-beats-table {
	font-family: Georgia, serif;
	border-collapse: collapse;
}

.hlas-beats-table th {
	background: linear-gradient(135deg, #1a5490, #2a7ab0);
	color: white;
}
```

## Authentication Integration

### Current Implementation (Phase 1)

- Supports WordPress nonces for initial testing
- API key-based authentication for plugin-to-backend communication
- Browser stores HLaS auth tokens in localStorage

### Future Implementation (Phase 2)

- Full HLaS member authentication integration
- WordPress user account linking to HLaS members
- Single sign-on between WordPress and HLaS
- Role-based access control

## Members-Only Fallback Messages

Both the **Beat Details** and **Catch Returns** shortcodes require authentication to display sensitive member information. When a user attempts to access these features without proper authentication, they will see a friendly fallback message instead.

### Beat Details Fallback
Non-authenticated users will see:
> "This information is only available to members of {Club Name}. Please contact {admin_email} for any membership enquiries or questions on using the website."

### Catch Returns Fallback
Non-authenticated users will see:
> "This information is accessible only by members of {Club Name}, please contact {admin_email} with any issues or enquiries as to how to access the site."

The admin email is automatically retrieved from the HLaS backend's club configuration, so no manual configuration is needed on the WordPress side.

## Troubleshooting

### "API client not initialized"

**Cause:** Plugin settings not configured
**Solution:** 
1. Go to WordPress Admin > HLaS Settings
2. Enter your API URL and API Key
3. Click "Save Changes"

### Beat details not loading

**Cause:** API connectivity issue
**Solution:**
1. Enable Debug Mode in HLaS Settings
2. Open browser console (F12 > Console tab)
3. Check for error messages
4. Verify API URL is correct and accessible
5. Check that CORS is enabled on your HLaS backend

### Catch returns showing "Not authenticated"

**Cause:** User not logged in or not authenticated with HLaS
**Solution:**
1. User must log in to WordPress first
2. User must authenticate with HLaS credentials
3. Check that API key matches on both WordPress and HLaS backend

### Elementor not showing shortcodes

**Cause:** Text widget not saving shortcodes
**Solution:**
1. Use "HTML" widget instead of "Text" widget
2. Ensure widget content is set to execute shortcodes
3. Clear Elementor cache

## File Structure

```
hlas-integration/
├── hlas-integration.php          # Main plugin file
├── includes/
│   ├── class-api-client.php      # API communication
│   ├── class-auth.php            # Authentication handling
│   ├── class-shortcodes.php      # Shortcode registration
│   └── class-blocks.php          # Gutenberg blocks (future)
├── js/
│   ├── api-client.js             # JavaScript API client
│   ├── beat-details.js           # Beat details rendering
│   ├── catch-returns.js          # Catch returns handling
│   └── auth.js                   # Authentication UI
├── css/
│   ├── hlas-integration.css      # Frontend styles
│   └── hlas-admin.css            # Admin styles
├── templates/                    # HTML templates (future)
└── README.md                     # This file
```

## Development Notes

### API Client Usage

```javascript
// Get beat details (public)
hlasClient.getBeatDetails('CTC')
	.then(data => console.log(data))
	.catch(error => console.error(error));

// Get catch returns (requires auth)
hlasClient.getCatchReturns('CTC', limit, offset)
	.then(data => console.log(data))
	.catch(error => console.error(error));

// Create catch return (requires auth)
hlasClient.createCatchReturn('CTC', {
	session_date: '2026-05-14',
	beat_id: 'UB001',
	fish_count: { small_trout: 2, ... },
	flies_used: 'Olive Dun',
	...
})
	.then(data => console.log(data))
	.catch(error => console.error(error));
```

### Adding Custom Filters

```php
// Filter beat details before display
add_filter('hlas_beat_details_output', function($html, $club, $data) {
	// Modify $html as needed
	return $html;
}, 10, 3);

// Filter catch returns display
add_filter('hlas_catch_returns_output', function($html, $club, $data) {
	// Modify $html as needed
	return $html;
}, 10, 3);
```

## Performance Optimization

1. **Enable Caching**
   - Set Cache TTL to 3600 seconds (default)
   - Consider using WordPress object cache (Redis/Memcached)

2. **Lazy Load Images**
   - Beat images and club logos use WordPress lazy loading

3. **Minified Assets**
   - JavaScript and CSS are production-ready
   - Consider using WordPress minification plugins

## Security

- All user input is sanitized using WordPress `sanitize_*` functions
- API requests use HTTPS (ensure your HLaS API uses HTTPS)
- Nonces protect against CSRF attacks
- User authentication is handled via WordPress and HLaS backend

## Support

For issues or feature requests:
1. Check troubleshooting section above
2. Enable debug mode and check browser console
3. Review HLaS backend logs for API errors
4. Contact your system administrator

## License

This plugin is released under the GPL v2 or later license.

## Changelog

### Version 1.0.0 (2026-05-14)
- Initial release
- Beat Details shortcode
- Catch Returns display
- Catch Return form
- HLaS API integration
- WordPress settings page
- CSS customization support

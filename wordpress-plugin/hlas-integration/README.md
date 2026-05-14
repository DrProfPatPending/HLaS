# HLaS Integration WordPress Plugin

A WordPress plugin that integrates HLaS (Hook Line and Sinker) with your WordPress site, allowing you to embed beat details, catch returns, and member-only content.

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

### Environment Variable Setup

On your HLaS backend server, ensure these environment variables are set:

```bash
export WORDPRESS_DOMAIN="https://your-wordpress-site.com"
export WORDPRESS_API_KEY="your-shared-secret-key"
```

## Usage

### Shortcodes

#### Beat Details
Display fishing beat information for a club:

```
[hlas-beat-details club="CTC"]
```

**Attributes:**
- `club` (required): Club abbreviation (e.g., "CTC", "GAAFFS")
- `style` (optional): Display style - "table" (default) or "grid"

**Examples:**
```
[hlas-beat-details club="CTC" style="table"]
[hlas-beat-details club="GAAFFS" style="grid"]
```

#### Catch Returns List
Display recent catch returns for the logged-in user:

```
[hlas-catch-returns club="CTC"]
```

**Attributes:**
- `club` (required): Club abbreviation
- `limit` (optional): Number of results to display (default: 10, max: 100)
- `style` (optional): Display style - "table" (default) or "timeline"

**Examples:**
```
[hlas-catch-returns club="CTC" limit="20"]
[hlas-catch-returns club="CTC" limit="5" style="timeline"]
```

**Note:** Requires user to be logged in and authenticated with HLaS

#### Catch Return Form
Display a form for users to log new fishing sessions:

```
[hlas-catch-return-form club="CTC"]
```

**Attributes:**
- `club` (required): Club abbreviation

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

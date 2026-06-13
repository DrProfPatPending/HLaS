<?php
/**
 * Plugin Name: HLaS Integration
 * Plugin URI: https://github.com/drprofpatpending/hlas-integration
 * Description: Integrates HLaS (Hook Line and Sinker) with WordPress for member-only content
 * Version: 1.0.0
 * Author: ScoffySoft -- Dr. Robert Scoffin with the help of Claude...
 * Author URI: https://scoffin.com
 * License: GPL v2 or later
 * License URI: https://www.gnu.org/licenses/gpl-2.0.html
 * Text Domain: hlas-integration
 * Domain Path: /languages
 * 
 * This plugin allows embedding HLaS components (Beat Details, Catch Returns) into WordPress
 * pages and posts using shortcodes and blocks.
 * 
 * @package HLaS_Integration
 * @since 1.0.0
 */

// Prevent direct access to this file
if ( ! defined( 'ABSPATH' ) ) {
	exit;
}

/**
 * Define plugin constants
 */
define( 'HLAS_PLUGIN_FILE', __FILE__ );
define( 'HLAS_PLUGIN_DIR', plugin_dir_path( __FILE__ ) );
define( 'HLAS_PLUGIN_URL', plugin_dir_url( __FILE__ ) );
define( 'HLAS_PLUGIN_VERSION', '1.0.5' );

if ( ! function_exists( 'hlas_integration_parse_club_from_request' ) ) {
	/**
	 * Resolve club short code from request path/query.
	 *
	 * Supported patterns:
	 * - /club/GAAFFS/
	 * - ?club=GAAFFS
	 *
	 * @return string Club short code or empty string.
	 */
	function hlas_integration_parse_club_from_request() {
		$club = '';

		if ( function_exists( 'get_query_var' ) ) {
			$query_var_club = (string) get_query_var( 'hlas_club' );
			if ( '' !== $query_var_club ) {
				$club = sanitize_text_field( $query_var_club );
			}
		}

		if ( '' === $club && isset( $_GET['club'] ) ) {
			$club = sanitize_text_field( wp_unslash( $_GET['club'] ) );
		}

		if ( '' === $club && isset( $_SERVER['REQUEST_URI'] ) ) {
			$request_uri = sanitize_text_field( wp_unslash( $_SERVER['REQUEST_URI'] ) );
			$path        = wp_parse_url( $request_uri, PHP_URL_PATH );

			if ( is_string( $path ) && preg_match( '#/club/([A-Za-z0-9_-]+)#i', $path, $matches ) ) {
				$club = $matches[1];
			}
		}

		$club = strtoupper( trim( (string) $club ) );

		return preg_replace( '/[^A-Z0-9_-]/', '', $club );
	}
}

if ( ! function_exists( 'hlas_integration_get_current_club' ) ) {
	/**
	 * Get effective club for current request.
	 *
	 * @return string Club short code.
	 */
	function hlas_integration_get_current_club() {
		$resolved = hlas_integration_parse_club_from_request();
		if ( '' !== $resolved ) {
			return $resolved;
		}

		$default_club = strtoupper( trim( (string) get_option( 'hlas_default_club', 'CTC' ) ) );
		$default_club = preg_replace( '/[^A-Z0-9_-]/', '', $default_club );

		return '' !== $default_club ? $default_club : 'CTC';
	}
}

/**
 * Include required files
 */
require_once( HLAS_PLUGIN_DIR . 'includes/class-api-client.php' );
require_once( HLAS_PLUGIN_DIR . 'includes/class-auth.php' );
require_once( HLAS_PLUGIN_DIR . 'includes/class-shortcodes.php' );
require_once( HLAS_PLUGIN_DIR . 'includes/class-blocks.php' );

/**
 * Main plugin class
 */
class HLaS_Integration {

	/**
	 * Instance of this class
	 *
	 * @var HLaS_Integration
	 */
	private static $instance = null;

	/**
	 * Get singleton instance
	 *
	 * @return HLaS_Integration
	 */
	public static function get_instance() {
		if ( null === self::$instance ) {
			self::$instance = new self();
		}
		return self::$instance;
	}

	/**
	 * Constructor
	 */
	private function __construct() {
		// Hook into WordPress
		add_action( 'init', array( $this, 'register_dynamic_club_route' ) );
		add_filter( 'query_vars', array( $this, 'register_query_vars' ) );
		add_action( 'plugins_loaded', array( $this, 'on_plugins_loaded' ) );
		add_action( 'admin_menu', array( $this, 'register_admin_menu' ) );
		add_action( 'admin_init', array( $this, 'register_settings' ) );
		add_action( 'wp_enqueue_scripts', array( $this, 'enqueue_frontend_assets' ) );
		add_action( 'admin_enqueue_scripts', array( $this, 'enqueue_admin_assets' ) );
		add_filter( 'body_class', array( $this, 'add_club_body_class' ) );
		add_action( 'wp_head', array( $this, 'output_club_theme_tokens' ) );

		// Register activation/deactivation hooks
		register_activation_hook( HLAS_PLUGIN_FILE, array( $this, 'activate' ) );
		register_deactivation_hook( HLAS_PLUGIN_FILE, array( $this, 'deactivate' ) );
	}

	/**
	 * Plugin activation hook
	 */
	public function activate() {
		$this->register_dynamic_club_route();

		// Create plugin options with defaults
		if ( ! get_option( 'hlas_api_url' ) ) {
			update_option( 'hlas_api_url', 'https://api.example.com' );
		}
		if ( ! get_option( 'hlas_api_key' ) ) {
			update_option( 'hlas_api_key', '' );
		}
		if ( ! get_option( 'hlas_nonce_action' ) ) {
			update_option( 'hlas_nonce_action', 'hlas_integration' );
		}
		if ( ! get_option( 'hlas_default_club' ) ) {
			update_option( 'hlas_default_club', 'CTC' );
		}
		if ( ! get_option( 'hlas_club_theme_map' ) ) {
			update_option( 'hlas_club_theme_map', '{}' );
		}

		flush_rewrite_rules();
	}

	/**
	 * Plugin deactivation hook
	 */
	public function deactivate() {
		flush_rewrite_rules();
	}

	/**
	 * Register query vars used by this plugin.
	 *
	 * @param array $vars Existing query vars.
	 * @return array
	 */
	public function register_query_vars( $vars ) {
		$vars[] = 'hlas_club';
		return $vars;
	}

	/**
	 * Register dynamic landing route for /club/{code}.
	 *
	 * This maps to the WordPress page with slug `club`.
	 */
	public function register_dynamic_club_route() {
		add_rewrite_rule(
			'^club/([A-Za-z0-9_-]+)/?$',
			'index.php?pagename=club&hlas_club=$matches[1]',
			'top'
		);
	}

	/**
	 * On plugins loaded - initialize components
	 */
	public function on_plugins_loaded() {
		// Register shortcodes
		$shortcodes = new HLaS_Shortcodes();
		$shortcodes->register_shortcodes();

		// Initialize blocks
		$blocks = new HLaS_Blocks();
		$blocks->register_blocks();

		// Initialize authentication
		$auth = new HLaS_Integration_Auth();
		$auth->init();

		// Register AJAX proxy endpoints
		add_action( 'wp_ajax_nopriv_hlas_beat_details', array( $this, 'ajax_beat_details' ) );
		add_action( 'wp_ajax_hlas_beat_details', array( $this, 'ajax_beat_details' ) );
		add_action( 'wp_ajax_nopriv_hlas_catch_returns', array( $this, 'ajax_catch_returns' ) );
		add_action( 'wp_ajax_hlas_catch_returns', array( $this, 'ajax_catch_returns' ) );
		add_action( 'wp_ajax_hlas_create_catch_return', array( $this, 'ajax_create_catch_return' ) );
	}

	/**
	 * Register admin menu
	 */
	public function register_admin_menu() {
		add_menu_page(
			'HLaS Integration',
			'HLaS Settings',
			'manage_options',
			'hlas-integration-settings',
			array( $this, 'render_settings_page' ),
			'dashicons-admin-generic',
			75
		);
	}

	/**
	 * Register plugin settings
	 */
	public function register_settings() {
		register_setting( 'hlas_integration_settings', 'hlas_api_url' );
		register_setting( 'hlas_integration_settings', 'hlas_api_key' );
		register_setting( 'hlas_integration_settings', 'hlas_enable_debug' );
		register_setting( 'hlas_integration_settings', 'hlas_cache_ttl' );
		register_setting( 'hlas_integration_settings', 'hlas_nonce_action' );
		register_setting( 'hlas_integration_settings', 'hlas_default_club', array( $this, 'sanitize_default_club' ) );
		register_setting( 'hlas_integration_settings', 'hlas_club_theme_map', array( $this, 'sanitize_club_theme_map' ) );

		add_settings_section(
			'hlas_api_settings',
			'API Configuration',
			array( $this, 'render_api_settings_section' ),
			'hlas_integration_settings'
		);

		add_settings_field(
			'hlas_api_url',
			'HLaS API URL',
			array( $this, 'render_api_url_field' ),
			'hlas_integration_settings',
			'hlas_api_settings'
		);

		add_settings_field(
			'hlas_api_key',
			'API Key / Shared Secret',
			array( $this, 'render_api_key_field' ),
			'hlas_integration_settings',
			'hlas_api_settings'
		);

		add_settings_field(
			'hlas_enable_debug',
			'Enable Debug Mode',
			array( $this, 'render_debug_field' ),
			'hlas_integration_settings',
			'hlas_api_settings'
		);

		add_settings_field(
			'hlas_cache_ttl',
			'Cache TTL (seconds)',
			array( $this, 'render_cache_ttl_field' ),
			'hlas_integration_settings',
			'hlas_api_settings'
		);

		add_settings_field(
			'hlas_default_club',
			'Default Club Code',
			array( $this, 'render_default_club_field' ),
			'hlas_integration_settings',
			'hlas_api_settings'
		);

		add_settings_field(
			'hlas_club_theme_map',
			'Club Theme Map (JSON)',
			array( $this, 'render_club_theme_map_field' ),
			'hlas_integration_settings',
			'hlas_api_settings'
		);
	}

	/**
	 * Render settings page
	 */
	public function render_settings_page() {
		?>
		<div class="wrap">
			<h1><?php esc_html_e( 'HLaS Integration Settings', 'hlas-integration' ); ?></h1>
			<form method="post" action="options.php">
				<?php settings_fields( 'hlas_integration_settings' ); ?>
				<?php do_settings_sections( 'hlas_integration_settings' ); ?>
				<?php submit_button(); ?>
			</form>

			<div class="card" style="margin-top: 20px;">
				<h2><?php esc_html_e( 'Available Shortcodes', 'hlas-integration' ); ?></h2>
				<p><strong>[hlas-beat-details]</strong> or <strong>[hlas-beat-details club="CTC"]</strong></p>
				<p><?php esc_html_e( 'If club is omitted, the plugin resolves it from /club/{CODE} in the URL (or falls back to Default Club Code).', 'hlas-integration' ); ?></p>

				<p><strong>[hlas-catch-returns limit="10"]</strong></p>
				<p><?php esc_html_e( 'Displays recent catch returns for the current user (requires authentication)', 'hlas-integration' ); ?></p>

				<p><strong>[hlas-catch-return-form]</strong></p>
				<p><?php esc_html_e( 'Displays a form to log a new catch return (requires authentication)', 'hlas-integration' ); ?></p>
			</div>
		</div>
		<?php
	}

	/**
	 * Render API settings section description
	 */
	public function render_api_settings_section() {
		echo wp_kses_post( '<p>Configure the connection to your HLaS backend API.</p>' );
	}

	/**
	 * Render API URL field
	 */
	public function render_api_url_field() {
		$value = esc_attr( get_option( 'hlas_api_url' ) );
		echo '<input type="url" name="hlas_api_url" value="' . $value . '" style="width: 400px;">';
		echo '<p class="description">e.g., https://api.example.com</p>';
	}

	/**
	 * Render API key field
	 */
	public function render_api_key_field() {
		$value = esc_attr( get_option( 'hlas_api_key' ) );
		echo '<input type="password" name="hlas_api_key" value="' . $value . '" style="width: 400px;">';
		echo '<p class="description">Shared secret for WordPress-HLaS authentication</p>';
	}

	/**
	 * Render debug mode field
	 */
	public function render_debug_field() {
		$value = get_option( 'hlas_enable_debug' );
		echo '<input type="checkbox" name="hlas_enable_debug" value="1" ' . checked( $value, 1, false ) . '>';
		echo '<p class="description">Enable debug logging in the browser console</p>';
	}

	/**
	 * Render cache TTL field
	 */
	public function render_cache_ttl_field() {
		$value = esc_attr( get_option( 'hlas_cache_ttl', 3600 ) );
		echo '<input type="number" name="hlas_cache_ttl" value="' . $value . '" min="0" max="86400">';
		echo '<p class="description">How long to cache API responses (0 = disabled)</p>';
	}

	/**
	 * Sanitize default club code.
	 *
	 * @param string $value Raw option value.
	 * @return string
	 */
	public function sanitize_default_club( $value ) {
		$value = strtoupper( trim( (string) sanitize_text_field( $value ) ) );
		$value = preg_replace( '/[^A-Z0-9_-]/', '', $value );

		return '' !== $value ? $value : 'CTC';
	}

	/**
	 * Sanitize theme map JSON.
	 *
	 * @param string $value Raw option value.
	 * @return string
	 */
	public function sanitize_club_theme_map( $value ) {
		$value   = trim( (string) $value );
		$decoded = json_decode( $value, true );

		if ( ! is_array( $decoded ) ) {
			add_settings_error( 'hlas_club_theme_map', 'hlas_club_theme_map_invalid', 'Club Theme Map must be valid JSON.', 'error' );
			return get_option( 'hlas_club_theme_map', '{}' );
		}

		return wp_json_encode( $decoded, JSON_PRETTY_PRINT | JSON_UNESCAPED_SLASHES );
	}

	/**
	 * Render default club field
	 */
	public function render_default_club_field() {
		$value = esc_attr( get_option( 'hlas_default_club', 'CTC' ) );
		echo '<input type="text" name="hlas_default_club" value="' . $value . '" style="width: 180px;" maxlength="16">';
		echo '<p class="description">Used when no <code>/club/{CODE}</code> is present in the URL.</p>';
	}

	/**
	 * Render club theme map JSON field
	 */
	public function render_club_theme_map_field() {
		$value = get_option( 'hlas_club_theme_map', '{}' );
		echo '<textarea name="hlas_club_theme_map" rows="10" cols="80" style="font-family: monospace; width: 100%; max-width: 900px;">' . esc_textarea( $value ) . '</textarea>';
		echo '<p class="description">Optional per-club tokens keyed by club code. Supported keys: primary_color, secondary_color, text_color, border_color, error_color, success_color, logo_url, hero_image_url.</p>';
	}

	/**
	 * Resolve sanitized per-club theme config.
	 *
	 * @param string $club Club short code.
	 * @return array
	 */
	private function get_theme_tokens_for_club( $club ) {
		$raw_map = get_option( 'hlas_club_theme_map', '{}' );
		$decoded = json_decode( (string) $raw_map, true );

		if ( ! is_array( $decoded ) ) {
			return array();
		}

		$club_key = strtoupper( sanitize_text_field( $club ) );
		if ( ! isset( $decoded[ $club_key ] ) || ! is_array( $decoded[ $club_key ] ) ) {
			return array();
		}

		$allowed = array(
			'primary_color'   => '--hlas-primary-color',
			'secondary_color' => '--hlas-secondary-color',
			'text_color'      => '--hlas-text-color',
			'border_color'    => '--hlas-border-color',
			'error_color'     => '--hlas-error-color',
			'success_color'   => '--hlas-success-color',
		);

		$tokens = array();
		foreach ( $allowed as $json_key => $css_var ) {
			if ( ! empty( $decoded[ $club_key ][ $json_key ] ) ) {
				$color = sanitize_hex_color( $decoded[ $club_key ][ $json_key ] );
				if ( $color ) {
					$tokens[ $css_var ] = $color;
				}
			}
		}

		if ( ! empty( $decoded[ $club_key ]['logo_url'] ) ) {
			$logo_url = esc_url_raw( $decoded[ $club_key ]['logo_url'] );
			if ( $logo_url ) {
				$tokens['--hlas-club-logo-url'] = "url('" . esc_url( $logo_url ) . "')";
			}
		}

		if ( ! empty( $decoded[ $club_key ]['hero_image_url'] ) ) {
			$hero_url = esc_url_raw( $decoded[ $club_key ]['hero_image_url'] );
			if ( $hero_url ) {
				$tokens['--hlas-club-hero-url'] = "url('" . esc_url( $hero_url ) . "')";
			}
		}

		return $tokens;
	}

	/**
	 * Add current club code as body class.
	 *
	 * @param array $classes Existing classes.
	 * @return array
	 */
	public function add_club_body_class( $classes ) {
		if ( is_admin() ) {
			return $classes;
		}

		$club = hlas_integration_get_current_club();
		if ( '' !== $club ) {
			$classes[] = 'hlas-club-' . strtolower( sanitize_html_class( $club ) );
		}

		return $classes;
	}

	/**
	 * Output per-club CSS token overrides.
	 */
	public function output_club_theme_tokens() {
		if ( is_admin() ) {
			return;
		}

		$club   = hlas_integration_get_current_club();
		$tokens = $this->get_theme_tokens_for_club( $club );
		if ( empty( $tokens ) ) {
			return;
		}

		$selector = 'body.hlas-club-' . strtolower( sanitize_html_class( $club ) );
		$lines    = array();
		foreach ( $tokens as $css_var => $css_value ) {
			$lines[] = $css_var . ': ' . $css_value . ';';
		}

		echo "\n<style id=\"hlas-club-theme-tokens\">\n";
		echo $selector . " {\n";
		echo implode( "\n", $lines ) . "\n";
		echo "}\n";
		echo "</style>\n";
	}

	/**
	 * Enqueue frontend assets
	 */
	public function enqueue_frontend_assets() {
		// Only enqueue on pages that might use HLaS shortcodes
		$post = get_post();
		if ( $post && ! is_admin() && ( has_shortcode( $post->post_content, 'hlas-beat-details' ) || has_shortcode( $post->post_content, 'hlas-catch-returns' ) || has_shortcode( $post->post_content, 'hlas-catch-return-form' ) ) ) {
			// Enqueue API client
			wp_enqueue_script(
				'hlas-api-client',
				HLAS_PLUGIN_URL . 'js/api-client.js',
				array(),
				HLAS_PLUGIN_VERSION,
				true
			);

			// Enqueue beat details script
			wp_enqueue_script(
				'hlas-beat-details',
				HLAS_PLUGIN_URL . 'js/beat-details.js',
				array( 'hlas-api-client' ),
				HLAS_PLUGIN_VERSION,
				true
			);

			// Enqueue catch returns script
			wp_enqueue_script(
				'hlas-catch-returns',
				HLAS_PLUGIN_URL . 'js/catch-returns.js',
				array( 'hlas-api-client' ),
				HLAS_PLUGIN_VERSION,
				true
			);

			// Enqueue stylesheet
			wp_enqueue_style(
				'hlas-integration-styles',
				HLAS_PLUGIN_URL . 'css/hlas-integration.css',
				array(),
				HLAS_PLUGIN_VERSION
			);

			// Localise script with settings
			wp_localize_script(
				'hlas-api-client',
				'hlasConfig',
				array(
					'apiUrl'         => get_option( 'hlas_api_url' ),
					'apiKey'         => get_option( 'hlas_api_key' ),
					'nonce'          => wp_create_nonce( get_option( 'hlas_nonce_action', 'hlas_integration' ) ),
					'userId'         => get_current_user_id(),
					'isAuthenticated' => is_user_logged_in(),
					'debug'          => (bool) get_option( 'hlas_enable_debug' ),
				)
			);
		}
	}

	/**
	 * Enqueue admin assets
	 */
	public function enqueue_admin_assets( $page ) {
		if ( 'toplevel_page_hlas-integration-settings' !== $page ) {
			return;
		}

		wp_enqueue_style(
			'hlas-admin-styles',
			HLAS_PLUGIN_URL . 'css/hlas-admin.css',
			array(),
			HLAS_PLUGIN_VERSION
		);
	}

	/**
	 * AJAX handler for beat details
	 */
	public function ajax_beat_details() {
		check_ajax_referer( get_option( 'hlas_nonce_action', 'hlas_integration' ), 'nonce' );

		$club = isset( $_POST['club'] ) ? sanitize_text_field( $_POST['club'] ) : '';
		if ( ! $club ) {
			wp_send_json_error( array( 'message' => 'Club is required' ) );
		}

		$api_url = get_option( 'hlas_api_url' );
		$api_key = get_option( 'hlas_api_key' );

		if ( ! $api_url ) {
			wp_send_json_error( array( 'message' => 'API URL not configured' ) );
		}

		$url = rtrim( $api_url, '/' ) . '/api/headless/beat-details/' . urlencode( $club );

		$response = wp_remote_get(
			$url,
			array(
				'headers' => array(
					'Authorization' => 'Bearer ' . $api_key,
					'Accept' => 'application/json',
				),
				'timeout' => 30,
			)
		);

		if ( is_wp_error( $response ) ) {
			wp_send_json_error( array( 'message' => 'API request failed: ' . $response->get_error_message() ) );
		}

		$body = wp_remote_retrieve_body( $response );
		$data = json_decode( $body, true );

		if ( null === $data ) {
			wp_send_json_error( array( 'message' => 'Invalid API response' ) );
		}

		wp_send_json_success( $data );
	}

	/**
	 * AJAX handler for catch returns
	 */
	public function ajax_catch_returns() {
		check_ajax_referer( get_option( 'hlas_nonce_action', 'hlas_integration' ), 'nonce' );

		if ( ! is_user_logged_in() ) {
			wp_send_json_error( array( 'message' => 'You must be logged in' ), 401 );
		}

		$club = isset( $_POST['club'] ) ? sanitize_text_field( $_POST['club'] ) : '';
		$limit = isset( $_POST['limit'] ) ? intval( $_POST['limit'] ) : 10;
		$offset = isset( $_POST['offset'] ) ? intval( $_POST['offset'] ) : 0;

		if ( ! $club ) {
			wp_send_json_error( array( 'message' => 'Club is required' ) );
		}

		$api_url = get_option( 'hlas_api_url' );
		$wp_api_key = get_option( 'hlas_api_key' );
		$token = HLaS_Integration_Auth::get_user_auth_token( get_current_user_id() );
		$member_id = HLaS_Integration_Auth::get_current_member_id();

		if ( ! $api_url ) {
			wp_send_json_error( array( 'message' => 'API URL not configured' ) );
		}

		if ( ! $token && ! $member_id ) {
			wp_send_json_error( array( 'message' => 'You must be authenticated with HLaS (token or member mapping required)' ), 401 );
		}

		$url = rtrim( $api_url, '/' ) . '/api/headless/catch-returns/' . urlencode( $club );
		$query = array();
		if ( $limit ) {
			$query['limit'] = intval( $limit );
		}
		if ( $offset > 0 ) {
			$query['offset'] = intval( $offset );
		}
		if ( ! empty( $query ) ) {
			$url .= '?' . http_build_query( $query );
		}

		$response = wp_remote_get(
			$url,
			array(
				'headers' => array(
					'Authorization' => $token ? 'Bearer ' . $token : '',
					'X-WordPress-API-Key' => $wp_api_key ? $wp_api_key : '',
					'X-WP-User-ID' => strval( get_current_user_id() ),
					'X-HLAS-Member-ID' => $member_id ? strval( $member_id ) : '',
					'Accept' => 'application/json',
				),
				'timeout' => 30,
			)
		);

		if ( is_wp_error( $response ) ) {
			wp_send_json_error( array( 'message' => 'API request failed: ' . $response->get_error_message() ) );
		}

		$body = wp_remote_retrieve_body( $response );
		$data = json_decode( $body, true );

		if ( null === $data ) {
			wp_send_json_error( array( 'message' => 'Invalid API response' ) );
		}

		wp_send_json_success( $data );
	}

	/**
	 * AJAX handler for creating catch returns
	 */
	public function ajax_create_catch_return() {
		check_ajax_referer( get_option( 'hlas_nonce_action', 'hlas_integration' ), 'nonce' );

		if ( ! is_user_logged_in() ) {
			wp_send_json_error( array( 'message' => 'You must be logged in' ), 401 );
		}

		$club = isset( $_POST['club'] ) ? sanitize_text_field( $_POST['club'] ) : '';
		$payload_raw = isset( $_POST['payload'] ) ? wp_unslash( $_POST['payload'] ) : '';

		if ( ! $club || ! $payload_raw ) {
			wp_send_json_error( array( 'message' => 'Club and payload are required' ) );
		}

		$payload = json_decode( $payload_raw, true );
		if ( ! is_array( $payload ) ) {
			wp_send_json_error( array( 'message' => 'Invalid payload format' ) );
		}

		$api_url = get_option( 'hlas_api_url' );
		$wp_api_key = get_option( 'hlas_api_key' );
		$token = HLaS_Integration_Auth::get_user_auth_token( get_current_user_id() );
		$member_id = HLaS_Integration_Auth::get_current_member_id();

		if ( ! $api_url ) {
			wp_send_json_error( array( 'message' => 'API URL not configured' ) );
		}

		if ( ! $token && ! $member_id ) {
			wp_send_json_error( array( 'message' => 'You must be authenticated with HLaS (token or member mapping required)' ), 401 );
		}

		$url = rtrim( $api_url, '/' ) . '/api/headless/catch-returns/' . urlencode( $club );

		$response = wp_remote_post(
			$url,
			array(
				'headers' => array(
					'Authorization' => $token ? 'Bearer ' . $token : '',
					'X-WordPress-API-Key' => $wp_api_key ? $wp_api_key : '',
					'X-WP-User-ID' => strval( get_current_user_id() ),
					'X-HLAS-Member-ID' => $member_id ? strval( $member_id ) : '',
					'Accept' => 'application/json',
					'Content-Type' => 'application/json',
				),
				'body' => wp_json_encode( $payload ),
				'timeout' => 30,
			)
		);

		if ( is_wp_error( $response ) ) {
			wp_send_json_error( array( 'message' => 'API request failed: ' . $response->get_error_message() ) );
		}

		$status = wp_remote_retrieve_response_code( $response );
		$body = wp_remote_retrieve_body( $response );
		$data = json_decode( $body, true );

		if ( $status < 200 || $status >= 300 ) {
			$message = is_array( $data ) && isset( $data['error'] ) ? $data['error'] : 'Failed to create catch return';
			wp_send_json_error( array( 'message' => $message ), $status );
		}

		if ( null === $data ) {
			wp_send_json_error( array( 'message' => 'Invalid API response' ) );
		}

		wp_send_json_success( $data );
	}
}

/**
 * Initialize the plugin
 */
HLaS_Integration::get_instance();

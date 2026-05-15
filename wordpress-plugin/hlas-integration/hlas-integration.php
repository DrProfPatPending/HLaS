<?php
/**
 * Plugin Name: HLaS Integration
 * Plugin URI: https://github.com/drprofpatpending/hlas-integration
 * Description: Integrates HLaS (Hook Line and Sinker) with WordPress for member-only content
 * Version: 1.0.0
 * Author: ScoffySoft -- Dr. Robert Scoffin with teh help of Claude...
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
define( 'HLAS_PLUGIN_VERSION', '1.0.3' );

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
		add_action( 'plugins_loaded', array( $this, 'on_plugins_loaded' ) );
		add_action( 'admin_menu', array( $this, 'register_admin_menu' ) );
		add_action( 'admin_init', array( $this, 'register_settings' ) );
		add_action( 'wp_enqueue_scripts', array( $this, 'enqueue_frontend_assets' ) );
		add_action( 'admin_enqueue_scripts', array( $this, 'enqueue_admin_assets' ) );

		// Register activation/deactivation hooks
		register_activation_hook( HLAS_PLUGIN_FILE, array( $this, 'activate' ) );
		register_deactivation_hook( HLAS_PLUGIN_FILE, array( $this, 'deactivate' ) );
	}

	/**
	 * Plugin activation hook
	 */
	public function activate() {
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

		flush_rewrite_rules();
	}

	/**
	 * Plugin deactivation hook
	 */
	public function deactivate() {
		flush_rewrite_rules();
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
				<p><strong>[hlas-beat-details club="CTC"]</strong></p>
				<p><?php esc_html_e( 'Displays beat details for the specified club', 'hlas-integration' ); ?></p>

				<p><strong>[hlas-catch-returns club="CTC" limit="10"]</strong></p>
				<p><?php esc_html_e( 'Displays recent catch returns for the current user (requires authentication)', 'hlas-integration' ); ?></p>

				<p><strong>[hlas-catch-return-form club="CTC"]</strong></p>
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

			// Localize script with settings
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

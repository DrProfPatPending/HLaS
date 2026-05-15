<?php
/**
 * HLaS Integration Authentication Class
 *
 * Handles authentication integration between WordPress and HLaS
 *
 * @package HLaS_Integration
 * @since 1.0.0
 */

if ( ! defined( 'ABSPATH' ) ) {
	exit;
}

class HLaS_Integration_Auth {

	/**
	 * Initialize authentication hooks
	 */
	public function init() {
		// Add short code for login form
		add_shortcode( 'hlas-login', array( $this, 'render_login_form' ) );

		// Add AJAX endpoints for authentication
		add_action( 'wp_ajax_hlas_login', array( $this, 'ajax_handle_login' ) );
		add_action( 'wp_ajax_nopriv_hlas_login', array( $this, 'ajax_handle_login' ) );
		add_action( 'wp_ajax_hlas_logout', array( $this, 'ajax_handle_logout' ) );

		// Enqueue auth scripts
		add_action( 'wp_enqueue_scripts', array( $this, 'enqueue_auth_scripts' ) );

		// User profile mapping fields
		add_action( 'show_user_profile', array( $this, 'render_user_profile_fields' ) );
		add_action( 'edit_user_profile', array( $this, 'render_user_profile_fields' ) );
		add_action( 'personal_options_update', array( $this, 'save_user_profile_fields' ) );
		add_action( 'edit_user_profile_update', array( $this, 'save_user_profile_fields' ) );
	}

	/**
	 * Render HLaS mapping fields in WP user profile
	 *
	 * @param WP_User $user User object.
	 */
	public function render_user_profile_fields( $user ) {
		if ( ! current_user_can( 'edit_user', $user->ID ) ) {
			return;
		}

		$member_id = get_user_meta( $user->ID, 'hlas_member_id', true );
		$club_short_name = get_user_meta( $user->ID, 'hlas_club_short_name', true );
		?>
		<h2><?php esc_html_e( 'HLaS Integration', 'hlas-integration' ); ?></h2>
		<table class="form-table" role="presentation">
			<tr>
				<th><label for="hlas_member_id"><?php esc_html_e( 'HLaS Member ID', 'hlas-integration' ); ?></label></th>
				<td>
					<input type="number" min="1" step="1" name="hlas_member_id" id="hlas_member_id" value="<?php echo esc_attr( $member_id ); ?>" class="regular-text" />
					<p class="description"><?php esc_html_e( 'Numeric member ID used by HLaS for catch returns and catch submission. Leave blank to remove mapping.', 'hlas-integration' ); ?></p>
				</td>
			</tr>
			<tr>
				<th><label for="hlas_club_short_name"><?php esc_html_e( 'HLaS Club Short Name', 'hlas-integration' ); ?></label></th>
				<td>
					<input type="text" maxlength="20" name="hlas_club_short_name" id="hlas_club_short_name" value="<?php echo esc_attr( $club_short_name ); ?>" class="regular-text" />
					<p class="description"><?php esc_html_e( 'Optional default club short name for testing (for example CTC). Leave blank to remove mapping.', 'hlas-integration' ); ?></p>
				</td>
			</tr>
		</table>
		<?php
	}

	/**
	 * Save HLaS mapping fields from WP user profile
	 *
	 * @param int $user_id User ID.
	 */
	public function save_user_profile_fields( $user_id ) {
		if ( ! current_user_can( 'edit_user', $user_id ) ) {
			return;
		}

		if ( ! isset( $_POST['hlas_member_id'] ) && ! isset( $_POST['hlas_club_short_name'] ) ) {
			return;
		}

		if ( isset( $_POST['hlas_member_id'] ) ) {
			$member_id_raw = sanitize_text_field( wp_unslash( $_POST['hlas_member_id'] ) );
			if ( '' === $member_id_raw ) {
				delete_user_meta( $user_id, 'hlas_member_id' );
			} else {
				$member_id = absint( $member_id_raw );
				if ( $member_id > 0 ) {
					update_user_meta( $user_id, 'hlas_member_id', $member_id );
				}
			}
		}

		if ( isset( $_POST['hlas_club_short_name'] ) ) {
			$club_short_name_raw = sanitize_text_field( wp_unslash( $_POST['hlas_club_short_name'] ) );
			$club_short_name = strtoupper( preg_replace( '/[^A-Za-z0-9_-]/', '', $club_short_name_raw ) );
			if ( '' === $club_short_name ) {
				delete_user_meta( $user_id, 'hlas_club_short_name' );
			} else {
				update_user_meta( $user_id, 'hlas_club_short_name', $club_short_name );
			}
		}
	}

	/**
	 * Render HLaS login form
	 *
	 * @param array $atts Shortcode attributes
	 * @return string HTML form
	 */
	public function render_login_form( $atts ) {
		if ( is_user_logged_in() ) {
			return '<div class="hlas-auth-message hlas-auth-success">You are already logged in.</div>';
		}

		ob_start();
		?>
		<div class="hlas-login-form">
			<h3><?php esc_html_e( 'HLaS Member Login', 'hlas-integration' ); ?></h3>
			<form id="hlas-login-form" class="hlas-form">
				<?php wp_nonce_field( 'hlas_login_nonce', 'hlas_nonce' ); ?>

				<div class="form-group">
					<label for="hlas-club"><?php esc_html_e( 'Club', 'hlas-integration' ); ?></label>
					<select id="hlas-club" name="club" required>
						<option value=""><?php esc_html_e( 'Select a club...', 'hlas-integration' ); ?></option>
						<option value="CTC"><?php esc_html_e( 'Club Taylor Club', 'hlas-integration' ); ?></option>
						<option value="GAAFFS"><?php esc_html_e( 'GAAFFS', 'hlas-integration' ); ?></option>
					</select>
				</div>

				<div class="form-group">
					<label for="hlas-username"><?php esc_html_e( 'Username or Member Number', 'hlas-integration' ); ?></label>
					<input type="text" id="hlas-username" name="username" required>
				</div>

				<div class="form-group">
					<label for="hlas-password"><?php esc_html_e( 'Password', 'hlas-integration' ); ?></label>
					<input type="password" id="hlas-password" name="password" required>
				</div>

				<button type="submit" class="btn btn-primary"><?php esc_html_e( 'Login', 'hlas-integration' ); ?></button>
				<div id="hlas-login-status" class="hlas-auth-message" style="display: none;"></div>
			</form>
		</div>
		<?php
		return ob_get_clean();
	}

	/**
	 * AJAX handler for login
	 */
	public function ajax_handle_login() {
		check_ajax_referer( 'hlas_login_nonce', 'hlas_nonce' );

		$username = isset( $_POST['username'] ) ? sanitize_text_field( $_POST['username'] ) : '';
		$password = isset( $_POST['password'] ) ? sanitize_text_field( $_POST['password'] ) : '';
		$club     = isset( $_POST['club'] ) ? sanitize_text_field( $_POST['club'] ) : '';

		if ( empty( $username ) || empty( $password ) || empty( $club ) ) {
			wp_send_json_error( array( 'message' => 'All fields are required' ) );
		}

		// TODO: Call HLaS backend to authenticate and get token
		// This would involve:
		// 1. Call HLaS /login endpoint (or headless equivalent)
		// 2. Authenticate against HLaS member database
		// 3. Get JWT token
		// 4. Store token in user meta
		// 5. Return success with auth token

		// For now, return placeholder
		wp_send_json_error( array( 'message' => 'Authentication not yet implemented' ) );
	}

	/**
	 * AJAX handler for logout
	 */
	public function ajax_handle_logout() {
		if ( ! is_user_logged_in() ) {
			wp_send_json_error( array( 'message' => 'Not logged in' ) );
		}

		// Clear HLaS auth token from user meta
		delete_user_meta( get_current_user_id(), 'hlas_auth_token' );
		delete_user_meta( get_current_user_id(), 'hlas_member_id' );

		wp_send_json_success( array( 'message' => 'Logged out successfully' ) );
	}

	/**
	 * Enqueue authentication scripts
	 */
	public function enqueue_auth_scripts() {
		if ( has_shortcode( get_post()->post_content, 'hlas-login' ) ) {
			wp_enqueue_script(
				'hlas-auth',
				HLAS_PLUGIN_URL . 'js/auth.js',
				array( 'jquery' ),
				HLAS_PLUGIN_VERSION,
				true
			);

			wp_localize_script(
				'hlas-auth',
				'hlasAuth',
				array(
					'ajaxUrl' => admin_url( 'admin-ajax.php' ),
				)
			);
		}
	}

	/**
	 * Check if current user is authenticated with HLaS
	 *
	 * @return bool
	 */
	public static function is_hlas_authenticated() {
		if ( ! is_user_logged_in() ) {
			return false;
		}

		$auth_token = self::get_user_auth_token( get_current_user_id() );
		$member_id = self::get_current_member_id();
		return ! empty( $auth_token ) || ! empty( $member_id );
	}

	/**
	 * Get HLaS auth token for a user
	 *
	 * @param int|null $user_id WordPress user ID (defaults to current user)
	 * @return string
	 */
	public static function get_user_auth_token( $user_id = null ) {
		if ( null === $user_id ) {
			if ( ! is_user_logged_in() ) {
				return '';
			}
			$user_id = get_current_user_id();
		}

		$token = get_user_meta( $user_id, 'hlas_auth_token', true );
		return is_string( $token ) ? trim( $token ) : '';
	}

	/**
	 * Get current user's HLaS member ID
	 *
	 * @return int|false Member ID or false if not authenticated
	 */
	public static function get_current_member_id() {
		if ( ! is_user_logged_in() ) {
			return false;
		}

		return get_user_meta( get_current_user_id(), 'hlas_member_id', true );
	}

	/**
	 * Get current user's default HLaS club short name
	 *
	 * @return string
	 */
	public static function get_current_club_short_name() {
		if ( ! is_user_logged_in() ) {
			return '';
		}

		$club_short_name = get_user_meta( get_current_user_id(), 'hlas_club_short_name', true );
		return is_string( $club_short_name ) ? trim( strtoupper( $club_short_name ) ) : '';
	}
}

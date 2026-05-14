<?php
/**
 * HLaS API Client Class
 *
 * Handles communication with the HLaS backend API endpoints
 *
 * @package HLaS_Integration
 * @since 1.0.0
 */

if ( ! defined( 'ABSPATH' ) ) {
	exit;
}

class HLaS_API_Client {

	/**
	 * Base URL for API calls
	 *
	 * @var string
	 */
	private $api_url;

	/**
	 * API key for authentication
	 *
	 * @var string
	 */
	private $api_key;

	/**
	 * Cache TTL in seconds
	 *
	 * @var int
	 */
	private $cache_ttl;

	/**
	 * Constructor
	 */
	public function __construct() {
		$this->api_url   = get_option( 'hlas_api_url' );
		$this->api_key   = get_option( 'hlas_api_key' );
		$this->cache_ttl = (int) get_option( 'hlas_cache_ttl', 3600 );
	}

	/**
	 * Get beat details for a club
	 *
	 * NOTE: This endpoint is members-only. Non-authenticated requests will receive
	 * a fallback message with club contact information (HTTP 403).
	 *
	 * @param string $club Club short name
	 * @return array|WP_Error Beat details array or fallback message
	 */
	public function get_beat_details( $club ) {
		$cache_key = 'hlas_beat_details_' . sanitize_key( $club );
		$cached    = get_transient( $cache_key );

		if ( false !== $cached ) {
			return $cached;
		}

		$url = $this->api_url . '/api/headless/beat-details/' . urlencode( $club );

		// Build headers with API authentication
		$headers = array(
			'Content-Type' => 'application/json',
		);

		// Add WordPress API key for authentication if available
		if ( ! empty( $this->api_key ) ) {
			$headers['X-WordPress-API-Key'] = $this->api_key;
		}

		$response = wp_remote_get(
			$url,
			array(
				'timeout' => 10,
				'headers' => $headers,
			)
		);

		if ( is_wp_error( $response ) ) {
			return $response;
		}

		$status_code = wp_remote_retrieve_response_code( $response );
		$body        = wp_remote_retrieve_body( $response );
		$data        = json_decode( $body, true );

		if ( null === $data ) {
			return new WP_Error( 'hlas_api_error', 'Invalid JSON response from API' );
		}

		// Handle members-only response (403) - return the fallback message
		if ( 403 === $status_code ) {
			// Still cache the fallback response so we don't hammer the API
			if ( $this->cache_ttl > 0 ) {
				set_transient( $cache_key, $data, $this->cache_ttl );
			}
			return $data;
		}

		// Handle other non-200 responses as errors
		if ( 200 !== $status_code ) {
			return new WP_Error(
				'hlas_api_error',
				sprintf( 'API returned status %d', $status_code ),
				array( 'status' => $status_code )
			);
		}

		// Cache the successful result
		if ( $this->cache_ttl > 0 ) {
			set_transient( $cache_key, $data, $this->cache_ttl );
		}

		return $data;
	}

	/**
	 * Get catch returns for current user
	 *
	 * NOTE: This endpoint is members-only. Non-authenticated requests will receive
	 * a fallback message with club contact information (HTTP 403).
	 *
	 * @param string $club  Club short name
	 * @param array  $args  Query parameters (limit, offset)
	 * @return array|WP_Error Catch returns array or fallback message
	 */
	public function get_catch_returns( $club, $args = array() ) {
		if ( ! is_user_logged_in() ) {
			return new WP_Error( 'hlas_auth_required', 'User must be logged in' );
		}

		// Get HLaS authentication token from user meta
		// This assumes user has been authenticated with HLaS
		$auth_token = get_user_meta( get_current_user_id(), 'hlas_auth_token', true );

		if ( ! $auth_token ) {
			return new WP_Error( 'hlas_user_not_authenticated', 'User is not authenticated with HLaS' );
		}

		$defaults = array(
			'limit'  => 50,
			'offset' => 0,
		);
		$args     = wp_parse_args( $args, $defaults );

		$cache_key = 'hlas_catch_returns_' . get_current_user_id() . '_' . sanitize_key( $club );
		$cached    = get_transient( $cache_key );

		if ( false !== $cached ) {
			return $cached;
		}

		$url  = $this->api_url . '/api/headless/catch-returns/' . urlencode( $club );
		$url  = add_query_arg(
			array(
				'limit'  => intval( $args['limit'] ),
				'offset' => intval( $args['offset'] ),
			),
			$url
		);

		$response = wp_remote_get(
			$url,
			array(
				'timeout' => 10,
				'headers' => array(
					'Content-Type'              => 'application/json',
					'Authorization'             => 'Bearer ' . $auth_token,
				),
			)
		);

		if ( is_wp_error( $response ) ) {
			return $response;
		}

		$status_code = wp_remote_retrieve_response_code( $response );
		$body        = wp_remote_retrieve_body( $response );
		$data        = json_decode( $body, true );

		if ( null === $data ) {
			return new WP_Error( 'hlas_api_error', 'Invalid JSON response from API' );
		}

		// Handle members-only response (403) - return the fallback message
		if ( 403 === $status_code ) {
			// Still cache the fallback response so we don't hammer the API
			if ( $this->cache_ttl > 0 ) {
				set_transient( $cache_key, $data, $this->cache_ttl );
			}
			return $data;
		}

		// Handle other non-200 responses as errors
		if ( 200 !== $status_code ) {
			return new WP_Error(
				'hlas_api_error',
				sprintf( 'API returned status %d', $status_code ),
				array( 'status' => $status_code )
			);
		}

		// Cache the successful result
		if ( $this->cache_ttl > 0 ) {
			set_transient( $cache_key, $data, $this->cache_ttl );
		}

		return $data;
	}

	/**
	 * Create a new catch return
	 *
	 * @param string $club Club short name
	 * @param array  $data Catch return data
	 * @return array|WP_Error Created catch return or error
	 */
	public function create_catch_return( $club, $data ) {
		if ( ! is_user_logged_in() ) {
			return new WP_Error( 'hlas_auth_required', 'User must be logged in' );
		}

		$auth_token = get_user_meta( get_current_user_id(), 'hlas_auth_token', true );

		if ( ! $auth_token ) {
			return new WP_Error( 'hlas_user_not_authenticated', 'User is not authenticated with HLaS' );
		}

		$url = $this->api_url . '/api/headless/catch-returns/' . urlencode( $club );

		$response = wp_remote_post(
			$url,
			array(
				'timeout' => 10,
				'headers' => array(
					'Content-Type'              => 'application/json',
					'Authorization'             => 'Bearer ' . $auth_token,
				),
				'body'    => wp_json_encode( $data ),
			)
		);

		if ( is_wp_error( $response ) ) {
			return $response;
		}

		$status_code = wp_remote_retrieve_response_code( $response );
		if ( 201 !== $status_code ) {
			$body = wp_remote_retrieve_body( $response );
			$error_data = json_decode( $body, true );
			return new WP_Error(
				'hlas_api_error',
				isset( $error_data['error'] ) ? $error_data['error'] : 'Failed to create catch return',
				array( 'status' => $status_code )
			);
		}

		$body = wp_remote_retrieve_body( $response );
		$data = json_decode( $body, true );

		return $data;
	}

	/**
	 * Send WordPress user data to HLaS for member mapping
	 * 
	 * This establishes a link between WordPress user and HLaS member
	 *
	 * @param int    $user_id WordPress user ID
	 * @param string $hlas_member_id HLaS member ID
	 * @param string $club Club short name
	 * @return bool|WP_Error True on success, WP_Error on failure
	 */
	public function link_user_to_member( $user_id, $hlas_member_id, $club ) {
		$url = $this->api_url . '/api/headless/user-mapping/link';

		$response = wp_remote_post(
			$url,
			array(
				'timeout' => 10,
				'headers' => array(
					'Content-Type'              => 'application/json',
					'X-WordPress-API-Key'       => $this->api_key,
				),
				'body'    => wp_json_encode(
					array(
						'wp_user_id'       => $user_id,
						'hlas_member_id'   => $hlas_member_id,
						'club'             => $club,
					)
				),
			)
		);

		if ( is_wp_error( $response ) ) {
			return $response;
		}

		$status_code = wp_remote_retrieve_response_code( $response );
		return 200 === $status_code || 201 === $status_code;
	}
}

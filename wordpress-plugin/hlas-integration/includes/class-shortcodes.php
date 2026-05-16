<?php
/**
 * HLaS Shortcodes Class
 *
 * Registers and handles rendering of HLaS shortcodes
 *
 * @package HLaS_Integration
 * @since 1.0.0
 */

if ( ! defined( 'ABSPATH' ) ) {
	exit;
}

class HLaS_Shortcodes {

	/**
	 * Resolve shortcode club with precedence:
	 * explicit shortcode attr > URL club context > default club option.
	 *
	 * @param string $club_attr Raw shortcode club attribute.
	 * @return string
	 */
	private function resolve_shortcode_club( $club_attr ) {
		$club_attr = strtoupper( trim( (string) sanitize_text_field( $club_attr ) ) );
		$club_attr = preg_replace( '/[^A-Z0-9_-]/', '', $club_attr );

		if ( '' !== $club_attr ) {
			return $club_attr;
		}

		if ( function_exists( 'hlas_integration_get_current_club' ) ) {
			return hlas_integration_get_current_club();
		}

		return 'CTC';
	}

	/**
	 * Register all shortcodes
	 */
	public function register_shortcodes() {
		add_shortcode( 'hlas-beat-details', array( $this, 'beat_details_shortcode' ) );
		add_shortcode( 'hlas-catch-returns', array( $this, 'catch_returns_shortcode' ) );
		add_shortcode( 'hlas-catch-return-form', array( $this, 'catch_return_form_shortcode' ) );
	}

	/**
	 * Beat Details Shortcode
	 *
	 * Usage: [hlas-beat-details club="CTC"]
	 *
	 * @param array  $atts Shortcode attributes
	 * @param string $content Enclosed content
	 * @return string HTML output
	 */
	public function beat_details_shortcode( $atts, $content = '' ) {
		$atts = shortcode_atts(
			array(
				'club'  => '',
				'style' => 'table', // table or grid
			),
			$atts,
			'hlas-beat-details'
		);

		$club = $this->resolve_shortcode_club( $atts['club'] );
		$style = sanitize_text_field( $atts['style'] );

		// Create container with data attributes
		$container_id = 'hlas-beat-details-' . sanitize_html_class( $club );

		// Output loading indicator
		ob_start();
		?>
		<div id="<?php echo esc_attr( $container_id ); ?>" 
		     class="hlas-beat-details hlas-beat-details-<?php echo esc_attr( $style ); ?>"
		     data-club="<?php echo esc_attr( $club ); ?>"
		     data-style="<?php echo esc_attr( $style ); ?>">
			<div class="hlas-loading">
				<p><?php esc_html_e( 'Loading beat details...', 'hlas-integration' ); ?></p>
				<div class="spinner"></div>
			</div>
			<div class="hlas-error" style="display: none;">
				<p class="hlas-error-message"></p>
			</div>
		</div>
		<script type="text/javascript">
			document.addEventListener('DOMContentLoaded', function() {
				if (window.hlasBeats && typeof window.hlasBeats.loadBeatDetails === 'function') {
					window.hlasBeats.loadBeatDetails('<?php echo esc_js( $container_id ); ?>', '<?php echo esc_js( $club ); ?>');
				}
			});
		</script>
		<?php
		return ob_get_clean();
	}

	/**
	 * Catch Returns List Shortcode
	 *
	 * Usage: [hlas-catch-returns club="CTC" limit="10"]
	 *
	 * Requires user to be authenticated with HLaS
	 *
	 * @param array  $atts Shortcode attributes
	 * @param string $content Enclosed content
	 * @return string HTML output
	 */
	public function catch_returns_shortcode( $atts, $content = '' ) {
		$atts = shortcode_atts(
			array(
				'club'  => '',
				'limit' => '10',
				'style' => 'table', // table or timeline
			),
			$atts,
			'hlas-catch-returns'
		);

		$club = $this->resolve_shortcode_club( $atts['club'] );
		$limit = intval( $atts['limit'] );
		$limit = max( 1, min( $limit, 100 ) ); // Ensure between 1 and 100
		$style = sanitize_text_field( $atts['style'] );

		// Check authentication
		if ( ! is_user_logged_in() ) {
			return '<div class="hlas-notice hlas-notice-warning">' . 
				   esc_html__( 'You must be logged in to view your catch returns.', 'hlas-integration' ) . 
				   '</div>';
		}

		if ( ! HLaS_Integration_Auth::is_hlas_authenticated() ) {
			return '<div class="hlas-notice hlas-notice-warning">' . 
				   esc_html__( 'You are not authenticated with HLaS. Please log in with your HLaS credentials.', 'hlas-integration' ) . 
				   '</div>';
		}

		$container_id = 'hlas-catch-returns-' . sanitize_html_class( $club ) . '-' . uniqid();

		ob_start();
		?>
		<div id="<?php echo esc_attr( $container_id ); ?>" 
		     class="hlas-catch-returns hlas-catch-returns-<?php echo esc_attr( $style ); ?>"
		     data-club="<?php echo esc_attr( $club ); ?>"
		     data-limit="<?php echo esc_attr( $limit ); ?>"
		     data-style="<?php echo esc_attr( $style ); ?>">
			<div class="hlas-loading">
				<p><?php esc_html_e( 'Loading catch returns...', 'hlas-integration' ); ?></p>
				<div class="spinner"></div>
			</div>
			<div class="hlas-error" style="display: none;">
				<p class="hlas-error-message"></p>
			</div>
		</div>
		<script type="text/javascript">
			document.addEventListener('DOMContentLoaded', function() {
				if (window.hlasReturns && typeof window.hlasReturns.loadCatchReturns === 'function') {
					window.hlasReturns.loadCatchReturns('<?php echo esc_js( $container_id ); ?>', '<?php echo esc_js( $club ); ?>', <?php echo esc_js( $limit ); ?>);
				}
			});
		</script>
		<?php
		return ob_get_clean();
	}

	/**
	 * Catch Return Form Shortcode
	 *
	 * Usage: [hlas-catch-return-form club="CTC"]
	 *
	 * Requires user to be authenticated with HLaS
	 *
	 * @param array  $atts Shortcode attributes
	 * @param string $content Enclosed content
	 * @return string HTML output
	 */
	public function catch_return_form_shortcode( $atts, $content = '' ) {
		$atts = shortcode_atts(
			array(
				'club' => '',
			),
			$atts,
			'hlas-catch-return-form'
		);

		$club = $this->resolve_shortcode_club( $atts['club'] );

		// Check authentication
		if ( ! is_user_logged_in() ) {
			return '<div class="hlas-notice hlas-notice-warning">' . 
				   esc_html__( 'You must be logged in to log a catch.', 'hlas-integration' ) . 
				   '</div>';
		}

		if ( ! HLaS_Integration_Auth::is_hlas_authenticated() ) {
			return '<div class="hlas-notice hlas-notice-warning">' . 
				   esc_html__( 'You are not authenticated with HLaS. Please log in with your HLaS credentials.', 'hlas-integration' ) . 
				   '</div>';
		}

		$form_id = 'hlas-catch-return-form-' . sanitize_html_class( $club ) . '-' . uniqid();

		ob_start();
		?>
		<div class="hlas-catch-return-form-wrapper">
			<form id="<?php echo esc_attr( $form_id ); ?>" 
			      class="hlas-catch-return-form"
			      data-club="<?php echo esc_attr( $club ); ?>">
				
				<?php wp_nonce_field( 'hlas_catch_return_nonce', 'hlas_nonce' ); ?>

				<div class="form-row">
					<div class="form-group">
						<label for="catch-date-<?php echo esc_attr( $form_id ); ?>">
							<?php esc_html_e( 'Session Date', 'hlas-integration' ); ?> <span class="required">*</span>
						</label>
						<input type="date" 
						       id="catch-date-<?php echo esc_attr( $form_id ); ?>" 
						       name="session_date" 
						       required>
					</div>

					<div class="form-group">
						<label for="catch-beat-<?php echo esc_attr( $form_id ); ?>">
							<?php esc_html_e( 'Beat', 'hlas-integration' ); ?> <span class="required">*</span>
						</label>
						<input type="text" 
						       id="catch-beat-<?php echo esc_attr( $form_id ); ?>" 
						       name="beat_id"
						       placeholder="e.g., UB001"
						       required>
					</div>
				</div>

				<fieldset>
					<legend><?php esc_html_e( 'Fish Caught', 'hlas-integration' ); ?></legend>
					
					<div class="fish-count-row">
						<div class="form-group">
							<label for="small-trout-<?php echo esc_attr( $form_id ); ?>">
								<?php esc_html_e( 'Small Trout', 'hlas-integration' ); ?>
							</label>
							<input type="number" 
							       id="small-trout-<?php echo esc_attr( $form_id ); ?>" 
							       name="small_trout" 
							       min="0" 
							       value="0">
						</div>

						<div class="form-group">
							<label for="medium-trout-<?php echo esc_attr( $form_id ); ?>">
								<?php esc_html_e( 'Medium Trout', 'hlas-integration' ); ?>
							</label>
							<input type="number" 
							       id="medium-trout-<?php echo esc_attr( $form_id ); ?>" 
							       name="medium_trout" 
							       min="0" 
							       value="0">
						</div>

						<div class="form-group">
							<label for="large-trout-<?php echo esc_attr( $form_id ); ?>">
								<?php esc_html_e( 'Large Trout', 'hlas-integration' ); ?>
							</label>
							<input type="number" 
							       id="large-trout-<?php echo esc_attr( $form_id ); ?>" 
							       name="large_trout" 
							       min="0" 
							       value="0">
						</div>
					</div>

					<div class="fish-count-row">
						<div class="form-group">
							<label for="small-grayling-<?php echo esc_attr( $form_id ); ?>">
								<?php esc_html_e( 'Small Grayling', 'hlas-integration' ); ?>
							</label>
							<input type="number" 
							       id="small-grayling-<?php echo esc_attr( $form_id ); ?>" 
							       name="small_grayling" 
							       min="0" 
							       value="0">
						</div>

						<div class="form-group">
							<label for="medium-grayling-<?php echo esc_attr( $form_id ); ?>">
								<?php esc_html_e( 'Medium Grayling', 'hlas-integration' ); ?>
							</label>
							<input type="number" 
							       id="medium-grayling-<?php echo esc_attr( $form_id ); ?>" 
							       name="medium_grayling" 
							       min="0" 
							       value="0">
						</div>

						<div class="form-group">
							<label for="large-grayling-<?php echo esc_attr( $form_id ); ?>">
								<?php esc_html_e( 'Large Grayling', 'hlas-integration' ); ?>
							</label>
							<input type="number" 
							       id="large-grayling-<?php echo esc_attr( $form_id ); ?>" 
							       name="large_grayling" 
							       min="0" 
							       value="0">
						</div>

						<div class="form-group">
							<label for="other-fish-<?php echo esc_attr( $form_id ); ?>">
								<?php esc_html_e( 'Other Fish', 'hlas-integration' ); ?>
							</label>
							<input type="number" 
							       id="other-fish-<?php echo esc_attr( $form_id ); ?>" 
							       name="other_fish" 
							       min="0" 
							       value="0">
						</div>
					</div>
				</fieldset>

				<div class="form-row">
					<div class="form-group">
						<label for="flies-<?php echo esc_attr( $form_id ); ?>">
							<?php esc_html_e( 'Flies Used', 'hlas-integration' ); ?>
						</label>
						<input type="text" 
						       id="flies-<?php echo esc_attr( $form_id ); ?>" 
						       name="flies_used"
						       maxlength="500">
					</div>

					<div class="form-group">
						<label for="weather-<?php echo esc_attr( $form_id ); ?>">
							<?php esc_html_e( 'Weather Conditions', 'hlas-integration' ); ?>
						</label>
						<input type="text" 
						       id="weather-<?php echo esc_attr( $form_id ); ?>" 
						       name="weather_conditions"
						       maxlength="500">
					</div>
				</div>

				<div class="form-group">
					<label for="predator-<?php echo esc_attr( $form_id ); ?>">
						<?php esc_html_e( 'Predator Damage', 'hlas-integration' ); ?>
					</label>
					<textarea id="predator-<?php echo esc_attr( $form_id ); ?>" 
					          name="predator_damage" 
					          rows="3" 
					          maxlength="500"></textarea>
				</div>

				<div class="form-actions">
					<button type="submit" class="btn btn-primary">
						<?php esc_html_e( 'Log Catch', 'hlas-integration' ); ?>
					</button>
					<div class="form-status" style="display: none;"></div>
				</div>
			</form>
		</div>
		<script type="text/javascript">
			document.addEventListener('DOMContentLoaded', function() {
				if (window.hlasReturns && typeof window.hlasReturns.initCatchReturnForm === 'function') {
					window.hlasReturns.initCatchReturnForm('<?php echo esc_js( $form_id ); ?>', '<?php echo esc_js( $club ); ?>');
				}
			});
		</script>
		<?php
		return ob_get_clean();
	}
}

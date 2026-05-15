/**
 * HLaS Authentication
 * 
 * Handles HLaS member login form and authentication
 * 
 * @package HLaS_Integration
 * @since 1.0.0
 */

(function(jQuery) {
	'use strict';

	jQuery(document).ready(function($) {
		// Handle HLaS login form submission
		$('#hlas-login-form').on('submit', function(e) {
			e.preventDefault();

			var $form = $(this);
			var $statusDiv = $('#hlas-login-status');
			var username = $form.find('input[name="username"]').val();
			var password = $form.find('input[name="password"]').val();
			var club = $form.find('select[name="club"]').val();

			if (!username || !password || !club) {
				showStatus($statusDiv, 'All fields are required', 'error');
				return;
			}

			// Show loading state
			var $submitBtn = $form.find('button[type="submit"]');
			$submitBtn.prop('disabled', true);
			var originalText = $submitBtn.text();
			$submitBtn.text('Logging in...');

			// Submit login (implementation would follow in next phase)
			showStatus($statusDiv, 'Login feature coming soon', 'info');

			$submitBtn.prop('disabled', false);
			$submitBtn.text(originalText);
		});

		/**
		 * Show status message
		 */
		function showStatus($element, message, type) {
			$element.removeClass('hlas-error hlas-success hlas-info');
			$element.addClass('hlas-' + type);
			$element.text(message).show();

			if (type === 'error' || type === 'info') {
				// Hide error/info after 5 seconds
				setTimeout(function() {
					$element.fadeOut();
				}, 5000);
			}
		}
	});

})(jQuery);

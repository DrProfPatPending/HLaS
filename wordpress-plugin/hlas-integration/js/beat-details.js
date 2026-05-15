/**
 * HLaS Beat Details
 * 
 * Handles loading and rendering beat details
 * 
 * @package HLaS_Integration
 * @since 1.0.0
 */

(function(window) {
	'use strict';

	/**
	 * HLaS Beats module
	 */
	var hlasBeats = {
		/**
		 * Load and render beat details
		 */
		loadBeatDetails: function(containerId, club) {
			var container = document.getElementById(containerId);
			if (!container) {
				return;
			}

			// Get client
			if (typeof window.hlasClient === 'undefined') {
				this.showError(container, 'API client not initialized');
				return;
			}

			var self = this;

			// Fetch beat details
			window.hlasClient.getBeatDetails(club)
				.then(function(data) {
					if (data.error) {
						self.showError(container, data.error);
						return;
					}

					self.renderBeatDetails(container, data);
				})
				.catch(function(error) {
					self.showError(container, 'Failed to load beat details: ' + error.message);
				});
		},

		/**
		 * Render beat details in container
		 */
		renderBeatDetails: function(container, data) {
			container.innerHTML = '';
			container.classList.remove('hlas-loading');

			// Check for members-only response (fallback message)
			if (data.members_only === true) {
				this.renderMembersOnlyMessage(container, data);
				return;
			}

			if (!data.beats || data.beats.length === 0) {
				container.innerHTML = '<div class="hlas-notice">No beats found for this club.</div>';
				return;
			}

			// Get style preference
			var style = container.getAttribute('data-style') || 'table';

			if (style === 'grid') {
				this.renderBeatsGrid(container, data);
			} else {
				this.renderBeatsTable(container, data);
			}
		},

		/**
		 * Render members-only fallback message
		 */
		renderMembersOnlyMessage: function(container, data) {
			var html = '<div class="hlas-beat-details-container hlas-members-only">';
			html += '<div class="hlas-notice hlas-notice-info">';
			html += '<p>' + this.escapeHtml(data.message) + '</p>';
			html += '</div>';
			html += '</div>';
			container.innerHTML = html;
		},

		/**
		 * Render beats as a table
		 */
		renderBeatsTable: function(container, data) {
			var html = '<div class="hlas-beat-details-container">';
			html += '<h3>Beats for ' + this.escapeHtml(data.club.name) + '</h3>';
			html += '<table class="hlas-beats-table">';
			html += '<thead>';
			html += '<tr>';
			html += '<th>Beat Name</th>';
			html += '<th>Beat ID</th>';
			html += '<th>Position</th>';
			html += '<th>River</th>';
			html += '<th>Description</th>';
			html += '</tr>';
			html += '</thead>';
			html += '<tbody>';

			for (var i = 0; i < data.beats.length; i++) {
				var beat = data.beats[i];
				html += '<tr>';
				html += '<td>' + this.escapeHtml(beat.name) + '</td>';
				html += '<td>' + this.escapeHtml(beat.beat_id) + '</td>';
				html += '<td>' + this.escapeHtml(beat.position) + '</td>';
				html += '<td>' + this.escapeHtml(beat.river) + '</td>';
				html += '<td>' + this.escapeHtml(beat.description) + '</td>';
				html += '</tr>';
			}

			html += '</tbody>';
			html += '</table>';
			html += '</div>';

			container.innerHTML = html;
		},

		/**
		 * Render beats as a grid
		 */
		renderBeatsGrid: function(container, data) {
			var html = '<div class="hlas-beat-details-container">';
			html += '<h3>Beats for ' + this.escapeHtml(data.club.name) + '</h3>';
			html += '<div class="hlas-beats-grid">';

			for (var i = 0; i < data.beats.length; i++) {
				var beat = data.beats[i];
				html += '<div class="hlas-beat-card">';
				html += '<h4>' + this.escapeHtml(beat.name) + '</h4>';
				html += '<p><strong>Beat ID:</strong> ' + this.escapeHtml(beat.beat_id) + '</p>';
				html += '<p><strong>Position:</strong> ' + this.escapeHtml(beat.position) + '</p>';
				html += '<p><strong>River:</strong> ' + this.escapeHtml(beat.river) + '</p>';
				html += '<p>' + this.escapeHtml(beat.description) + '</p>';
				html += '</div>';
			}

			html += '</div>';
			html += '</div>';

			container.innerHTML = html;
		},

		/**
		 * Show error message
		 */
		showError: function(container, message) {
			container.innerHTML = '';
			container.classList.remove('hlas-loading');
			var errorDiv = document.createElement('div');
			errorDiv.className = 'hlas-error-message';
			errorDiv.textContent = message;
			container.appendChild(errorDiv);
		},

		/**
		 * Escape HTML special characters
		 */
		escapeHtml: function(text) {
			var div = document.createElement('div');
			div.textContent = text;
			return div.innerHTML;
		}
	};

	// Export to window
	window.hlasBeats = hlasBeats;

})(window);

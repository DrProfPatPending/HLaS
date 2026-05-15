/**
 * HLaS Catch Returns
 * 
 * Handles loading, rendering, and creating catch returns
 * 
 * @package HLaS_Integration
 * @since 1.0.0
 */

(function(window) {
	'use strict';

	/**
	 * HLaS Returns module
	 */
	var hlasReturns = {
		/**
		 * Load and render catch returns list
		 */
		loadCatchReturns: function(containerId, club, limit) {
			var container = document.getElementById(containerId);
			if (!container) {
				return;
			}

			limit = limit || 10;

			if (typeof window.hlasClient === 'undefined') {
				this.showError(container, 'API client not initialized');
				return;
			}

			var self = this;

			window.hlasClient.getCatchReturns(club, limit, 0)
				.then(function(data) {
					if (data.error) {
						self.showError(container, data.error);
						return;
					}

					self.renderCatchReturns(container, data);
				})
				.catch(function(error) {
					self.showError(container, 'Failed to load catch returns: ' + error.message);
				});
		},

		/**
		 * Render catch returns list
		 */
		renderCatchReturns: function(container, data) {
			container.innerHTML = '';
			container.classList.remove('hlas-loading');

			// Check for members-only response (fallback message)
			if (data.members_only === true) {
				this.renderMembersOnlyMessage(container, data);
				return;
			}

			if (!data.returns || data.returns.length === 0) {
				container.innerHTML = '<div class="hlas-notice">No catch returns recorded yet.</div>';
				return;
			}

			var style = container.getAttribute('data-style') || 'table';

			if (style === 'timeline') {
				this.renderTimeline(container, data);
			} else {
				this.renderTable(container, data);
			}
		},

		/**
		 * Render members-only fallback message
		 */
		renderMembersOnlyMessage: function(container, data) {
			var html = '<div class="hlas-catch-returns-container hlas-members-only">';
			html += '<div class="hlas-notice hlas-notice-info">';
			html += '<p>' + this.escapeHtml(data.message) + '</p>';
			html += '</div>';
			html += '</div>';
			container.innerHTML = html;
		},

		/**
		 * Render catch returns as a table
		 */
		renderTable: function(container, data) {
			var html = '<div class="hlas-catch-returns-container">';
			html += '<h3>Your Catch Returns</h3>';
			html += '<table class="hlas-catch-returns-table">';
			html += '<thead>';
			html += '<tr>';
			html += '<th>Date</th>';
			html += '<th>Beat</th>';
			html += '<th>Trout (S/M/L)</th>';
			html += '<th>Grayling (S/M/L)</th>';
			html += '<th>Other</th>';
			html += '<th>Notes</th>';
			html += '</tr>';
			html += '</thead>';
			html += '<tbody>';

			for (var i = 0; i < data.returns.length; i++) {
				var ret = data.returns[i];
				var fish = ret.fish_count;
				var notes = this.escapeHtml(ret.notes.flies_used || '');

				html += '<tr>';
				html += '<td>' + this.formatDate(ret.session_date) + '</td>';
				html += '<td>' + this.escapeHtml(ret.beat_id) + '</td>';
				html += '<td>' + fish.small_trout + '/' + fish.medium_trout + '/' + fish.large_trout + '</td>';
				html += '<td>' + fish.small_grayling + '/' + fish.medium_grayling + '/' + fish.large_grayling + '</td>';
				html += '<td>' + fish.other_fish + '</td>';
				html += '<td title="' + notes + '">' + (notes.length > 20 ? notes.substring(0, 20) + '...' : notes) + '</td>';
				html += '</tr>';
			}

			html += '</tbody>';
			html += '</table>';
			html += '</div>';

			container.innerHTML = html;
		},

		/**
		 * Render catch returns as a timeline
		 */
		renderTimeline: function(container, data) {
			var html = '<div class="hlas-catch-returns-timeline">';
			html += '<h3>Your Catch Returns</h3>';

			for (var i = 0; i < data.returns.length; i++) {
				var ret = data.returns[i];
				var fish = ret.fish_count;
				var totalFish = fish.small_trout + fish.medium_trout + fish.large_trout +
					fish.small_grayling + fish.medium_grayling + fish.large_grayling +
					fish.other_fish;

				html += '<div class="hlas-return-card">';
				html += '<div class="return-date">' + this.formatDate(ret.session_date) + '</div>';
				html += '<div class="return-content">';
				html += '<h4>Beat: ' + this.escapeHtml(ret.beat_id) + '</h4>';
				html += '<p><strong>Total Fish:</strong> ' + totalFish + '</p>';
				html += '<p>';
				html += '<strong>Breakdown:</strong> ';
				html += 'Trout ' + fish.small_trout + '/' + fish.medium_trout + '/' + fish.large_trout + ', ';
				html += 'Grayling ' + fish.small_grayling + '/' + fish.medium_grayling + '/' + fish.large_grayling + ', ';
				html += 'Other ' + fish.other_fish;
				html += '</p>';

				if (ret.notes.flies_used) {
					html += '<p><strong>Flies:</strong> ' + this.escapeHtml(ret.notes.flies_used) + '</p>';
				}
				if (ret.notes.weather) {
					html += '<p><strong>Weather:</strong> ' + this.escapeHtml(ret.notes.weather) + '</p>';
				}

				html += '</div>';
				html += '</div>';
			}

			html += '</div>';
			container.innerHTML = html;
		},

		/**
		 * Initialize catch return form
		 */
		initCatchReturnForm: function(formId, club) {
			var form = document.getElementById(formId);
			if (!form) {
				return;
			}

			var self = this;

			form.addEventListener('submit', function(e) {
				e.preventDefault();

				if (typeof window.hlasClient === 'undefined') {
					self.showFormError(form, 'API client not initialized');
					return;
				}

				// Gather form data
				var data = {
					session_date: form.querySelector('input[name="session_date"]').value,
					beat_id: form.querySelector('input[name="beat_id"]').value,
					fish_count: {
						small_trout: parseInt(form.querySelector('input[name="small_trout"]').value) || 0,
						medium_trout: parseInt(form.querySelector('input[name="medium_trout"]').value) || 0,
						large_trout: parseInt(form.querySelector('input[name="large_trout"]').value) || 0,
						small_grayling: parseInt(form.querySelector('input[name="small_grayling"]').value) || 0,
						medium_grayling: parseInt(form.querySelector('input[name="medium_grayling"]').value) || 0,
						large_grayling: parseInt(form.querySelector('input[name="large_grayling"]').value) || 0,
						other_fish: parseInt(form.querySelector('input[name="other_fish"]').value) || 0
					},
					flies_used: form.querySelector('input[name="flies_used"]').value,
					weather_conditions: form.querySelector('input[name="weather_conditions"]').value,
					predator_damage: form.querySelector('textarea[name="predator_damage"]').value
				};

				// Show loading state
				var submitBtn = form.querySelector('button[type="submit"]');
				var originalText = submitBtn.textContent;
				submitBtn.disabled = true;
				submitBtn.textContent = 'Submitting...';

				// Submit
				window.hlasClient.createCatchReturn(club, data)
					.then(function(result) {
						if (result.error) {
							self.showFormError(form, result.error);
						} else {
							self.showFormSuccess(form, 'Catch return logged successfully!');
							form.reset();
						}
					})
					.catch(function(error) {
						self.showFormError(form, 'Error: ' + error.message);
					})
					.finally(function() {
						submitBtn.disabled = false;
						submitBtn.textContent = originalText;
					});
			});
		},

		/**
		 * Show form error message
		 */
		showFormError: function(form, message) {
			var statusDiv = form.querySelector('.form-status');
			if (!statusDiv) {
				return;
			}
			statusDiv.className = 'form-status hlas-error-message';
			statusDiv.textContent = message;
			statusDiv.style.display = 'block';
		},

		/**
		 * Show form success message
		 */
		showFormSuccess: function(form, message) {
			var statusDiv = form.querySelector('.form-status');
			if (!statusDiv) {
				return;
			}
			statusDiv.className = 'form-status hlas-success-message';
			statusDiv.textContent = message;
			statusDiv.style.display = 'block';
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
		 * Format date
		 */
		formatDate: function(dateStr) {
			try {
				var date = new Date(dateStr);
				return date.toLocaleDateString('en-US', {
					year: 'numeric',
					month: 'short',
					day: 'numeric'
				});
			} catch (e) {
				return dateStr;
			}
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
	window.hlasReturns = hlasReturns;

})(window);

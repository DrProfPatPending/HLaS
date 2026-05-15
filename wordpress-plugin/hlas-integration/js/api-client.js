/**
 * HLaS API Client
 * 
 * Handles communication with HLaS backend API from the browser
 * 
 * @package HLaS_Integration
 * @since 1.0.0
 */

(function(window) {
	'use strict';

	/**
	 * HLaS API Client class
	 */
	function HLasApiClient(config) {
		this.config = config || {};
		this.apiUrl = config.apiUrl || 'https://api.example.com';
		this.apiKey = config.apiKey || '';
		this.nonce = config.nonce || '';
		this.userId = config.userId || 0;
		this.debug = config.debug || false;
		this.token = localStorage.getItem('hlas_auth_token') || '';
	}

	/**
	 * Get WordPress AJAX URL
	 */
	HLasApiClient.prototype.getAjaxUrl = function() {
		// WordPress exposes ajaxurl globally in footer
		if (typeof window.ajaxurl !== 'undefined') {
			return window.ajaxurl;
		}
		// If not available, construct it
		return window.location.origin + '/wp-admin/admin-ajax.php';
	};

	/**
	 * Log debug messages
	 */
	HLasApiClient.prototype.log = function(message, data) {
		if (this.debug && window.console) {
			console.log('[HLaS] ' + message, data || '');
		}
	};

	/**
	 * Handle API errors
	 */
	HLasApiClient.prototype.handleError = function(error) {
		this.log('API Error:', error);
		
		if (error.response) {
			if (error.response.status === 401) {
				// Authentication error
				return {
					error: 'Unauthorized - please log in with HLaS',
					status: 401
				};
			} else if (error.response.status === 403) {
				// Permission error
				return {
					error: 'You do not have permission to access this content',
					status: 403
				};
			} else if (error.response.status === 404) {
				// Not found
				return {
					error: 'Resource not found',
					status: 404
				};
			} else {
				return {
					error: 'API Error: ' + error.response.status,
					status: error.response.status
				};
			}
		}
		
		return {
			error: error.message || 'Unknown error',
			status: 0
		};
	};

	/**
	 * Normalize WordPress AJAX responses
	 */
	HLasApiClient.prototype.normalizeWpAjaxResponse = function(payload) {
		if (payload && typeof payload.success !== 'undefined') {
			if (payload.success) {
				return payload.data;
			}
			return {
				error: (payload.data && payload.data.message) ? payload.data.message : 'Request failed'
			};
		}
		return payload;
	};

	/**
	 * Fetch beat details for a club
	 */
	HLasApiClient.prototype.getBeatDetails = function(club) {
		var self = this;
		
		// Use WordPress admin-ajax.php as proxy
		var data = new FormData();
		data.append('action', 'hlas_beat_details');
		data.append('club', club);
		data.append('nonce', this.nonce);

		this.log('Fetching beat details for club: ' + club);

		return fetch(this.getAjaxUrl(), {
			method: 'POST',
			body: data,
			credentials: 'same-origin'
		})
		.then(function(response) {
			if (!response.ok) {
				throw {
					message: 'HTTP ' + response.status,
					response: response
				};
			}
			return response.json();
		})
		.then(function(payload) {
			return self.normalizeWpAjaxResponse(payload);
		})
		.catch(function(error) {
			return self.handleError(error);
		});
	};

	/**
	 * Fetch catch returns for current user
	 */
	HLasApiClient.prototype.getCatchReturns = function(club, limit, offset) {
		var self = this;
		limit = limit || 50;
		offset = offset || 0;

		// Use WordPress admin-ajax.php as proxy
		var data = new FormData();
		data.append('action', 'hlas_catch_returns');
		data.append('club', club);
		data.append('limit', limit);
		data.append('offset', offset);
		data.append('nonce', this.nonce);

		this.log('Fetching catch returns for club: ' + club);

		return fetch(this.getAjaxUrl(), {
			method: 'POST',
			body: data,
			credentials: 'same-origin'
		})
		.then(function(response) {
			if (!response.ok) {
				throw {
					message: 'HTTP ' + response.status,
					response: response
				};
			}
			return response.json();
		})
		.then(function(payload) {
			return self.normalizeWpAjaxResponse(payload);
		})
		.catch(function(error) {
			return self.handleError(error);
		});
	};

	/**
	 * Create a new catch return
	 */
	HLasApiClient.prototype.createCatchReturn = function(club, data) {
		var self = this;
		var url = this.apiUrl + '/api/headless/catch-returns/' + encodeURIComponent(club);

		this.log('Creating catch return at: ' + url, data);

		var headers = {
			'Content-Type': 'application/json',
			'Accept': 'application/json'
		};

		// Add authentication
		if (this.token) {
			headers['Authorization'] = 'Bearer ' + this.token;
		}

		return fetch(url, {
			method: 'POST',
			headers: headers,
			body: JSON.stringify(data)
		})
		.then(function(response) {
			if (response.status !== 201 && response.status !== 200) {
				throw {
					message: 'HTTP ' + response.status,
					response: response
				};
			}
			return response.json();
		})
		.catch(function(error) {
			return self.handleError(error);
		});
	};

	/**
	 * Set authentication token
	 */
	HLasApiClient.prototype.setAuthToken = function(token) {
		this.token = token;
		if (token) {
			localStorage.setItem('hlas_auth_token', token);
		} else {
			localStorage.removeItem('hlas_auth_token');
		}
	};

	/**
	 * Get authentication token
	 */
	HLasApiClient.prototype.getAuthToken = function() {
		return this.token;
	};

	// Export to window
	window.HLasApiClient = HLasApiClient;

	// Create global instance if config is available
	if (typeof window.hlasConfig !== 'undefined') {
		window.hlasClient = new HLasApiClient(window.hlasConfig);
	}

})(window);

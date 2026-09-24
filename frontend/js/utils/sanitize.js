/**
 * Utility functions for HTML sanitization to prevent Cross-Site Scripting (XSS).
 */

/**
 * Escapes characters with special meaning in HTML to prevent XSS injection.
 * @param {unknown} value - Value to escape
 * @returns {string} - Escaped string safe for HTML interpolation
 */
export function escapeHtml(value) {
    if (value === null || value === undefined) {
        return '';
    }
    const str = String(value);
    return str
        .replace(/&/g, '&amp;')
        .replace(/</g, '&lt;')
        .replace(/>/g, '&gt;')
        .replace(/"/g, '&quot;')
        .replace(/'/g, '&#39;');
}

/**
 * Sanitizes URLs to ensure they use safe protocols (http, https, or relative paths).
 * Prevents javascript: or data: URL injection in href or src attributes.
 * @param {unknown} url - The URL to sanitize
 * @param {string} fallback - Fallback URL if untrusted
 * @returns {string} - Safe URL string
 */
export function sanitizeUrl(url, fallback = 'https://via.placeholder.com/150') {
    if (!url || typeof url !== 'string') {
        return fallback;
    }
    const trimmed = url.trim();
    if (trimmed.startsWith('https://') || trimmed.startsWith('http://') || trimmed.startsWith('/')) {
        return escapeHtml(trimmed);
    }
    return fallback;
}

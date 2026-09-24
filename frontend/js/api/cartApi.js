
const API_BASE_URL = 'http://localhost:8000/api/v1/cart';

async function handleResponse(response) {
    if (!response.ok) {
        const errorBody = await response.json().catch(() => ({ detail: 'An unknown error occurred' }));
        const error = new Error(errorBody.detail || `HTTP error! status: ${response.status}`);
        error.body = errorBody;
        throw error;
    }
    return response.json();
}

async function apiRequest(method, endpoint = '', body = null, userId) {
    const options = {
        method,
        headers: {
            'Content-Type': 'application/json',
            'X-User-ID': userId,
        },
    };
    if (body) {
        options.body = JSON.stringify(body);
    }
    const response = await fetch(`${API_BASE_URL}${endpoint}`, options);
    return handleResponse(response);
}

export const getCart = (userId) => {
    return apiRequest('GET', '', null, userId);
};

export const addItem = (userId, productId, quantity) => {
    return apiRequest('POST', '/items', { product_id: productId, quantity }, userId);
};

export const updateItemQuantity = (userId, productId, quantity) => {
    return apiRequest('PUT', `/items/${productId}`, { quantity }, userId);
};

export const removeItem = async (userId, productId) => {
    try {
        return await apiRequest('DELETE', `/items/${productId}`, null, userId);
    } catch (error) {
        // If the item is already not in the cart (404), fetch current cart
        if (error.body && error.body.detail && error.body.detail.includes('not found')) {
            return await getCart(userId);
        }
        throw error;
    }
};

export const applyCoupon = (userId, couponCode) => {
    return apiRequest('POST', '/coupon', { coupon_code: couponCode }, userId);
};

export const removeCoupon = (userId) => {
    return apiRequest('DELETE', '/coupon', null, userId);
};

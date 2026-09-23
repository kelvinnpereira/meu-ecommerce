const API_BASE_URL = '/api/v1';

/**
 * Fetches the current cart from the server.
 * @returns {Promise<object>} A promise that resolves to the cart object.
 */
async function getCart() {
    try {
        const response = await fetch(`${API_BASE_URL}/cart`);
        if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
        }
        return await response.json();
    } catch (error) {
        console.error("Failed to fetch cart:", error);
        throw error;
    }
}

/**
 * Adds an item to the cart.
 * @param {string} productId - The ID of the product to add.
 * @param {number} quantity - The quantity of the product to add.
 * @returns {Promise<object>} A promise that resolves to the updated cart object.
 */
async function addItem(productId, quantity) {
    try {
        const response = await fetch(`${API_BASE_URL}/cart/items`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({ product_id: productId, quantity }),
        });
        if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
        }
        return await response.json();
    } catch (error) {
        console.error("Failed to add item to cart:", error);
        throw error;
    }
}

/**
 * Updates the quantity of an item in the cart.
 * @param {string} productId - The ID of the product to update.
 * @param {number} quantity - The new quantity.
 * @returns {Promise<object>} A promise that resolves to the updated cart object.
 */
async function updateItem(productId, quantity) {
    try {
        const response = await fetch(`${API_BASE_URL}/cart/items/${productId}`, {
            method: 'PUT',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({ quantity }),
        });
        if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
        }
        return await response.json();
    } catch (error) {
        console.error("Failed to update item in cart:", error);
        throw error;
    }
}

/**
 * Removes an item from the cart.
 * @param {string} productId - The ID of the product to remove.
 * @returns {Promise<object>} A promise that resolves to the updated cart object.
 */
async function removeItem(productId) {
    try {
        const response = await fetch(`${API_BASE_URL}/cart/items/${productId}`, {
            method: 'DELETE',
        });
        if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
        }
        return await response.json();
    } catch (error) {
        console.error("Failed to remove item from cart:", error);
        throw error;
    }
}

/**
 * Applies a coupon to the cart.
 * @param {string} couponCode - The coupon code.
 * @returns {Promise<object>} A promise that resolves to the updated cart object.
 */
async function applyCoupon(couponCode) {
    try {
        const response = await fetch(`${API_BASE_URL}/cart/coupon`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({ coupon_code: couponCode }),
        });
        if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
        }
        return await response.json();
    } catch (error) {
        console.error("Failed to apply coupon:", error);
        throw error;
    }
}

/**
 * Removes the current coupon from the cart.
 * @returns {Promise<object>} A promise that resolves to the updated cart object.
 */
async function removeCoupon() {
    try {
        const response = await fetch(`${API_BASE_URL}/cart/coupon`, {
            method: 'DELETE',
        });
        if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
        }
        return await response.json();
    } catch (error) {
        console.error("Failed to remove coupon:", error);
        throw error;
    }
}

export const cartApi = {
    getCart,
    addItem,
    updateItem,
    removeItem,
    applyCoupon,
    removeCoupon,
};

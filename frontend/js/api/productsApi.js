const API_BASE_URL = 'http://localhost:8000/api/v1';

/**
 * Fetches the list of products from the API.
 * @returns {Promise<Array<object>>} A promise that resolves to an array of products.
 */
export const fetchProducts = async () => {
    try {
        const response = await fetch(`${API_BASE_URL}/products`);
        if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
        }
        return await response.json();
    } catch (error) {
        console.error("Could not fetch products: ", error);
        throw error;
    }
};

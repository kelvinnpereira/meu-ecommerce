const productsApi = {
    fetchProducts: async () => {
        try {
            const response = await fetch('/api/v1/products');
            if (!response.ok) {
                throw new Error(`HTTP error! status: ${response.status}`);
            }
            return await response.json();
        } catch (error) {
            console.error("Could not fetch products: ", error);
            throw error;
        }
    }
};

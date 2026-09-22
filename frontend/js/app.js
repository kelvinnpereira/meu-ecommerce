// This file will orchestrate the frontend logic
document.addEventListener('DOMContentLoaded', () => {
    const loadingIndicator = document.getElementById('loading-indicator');
    const productsContainer = document.getElementById('products-container');

    const showLoading = () => {
        loadingIndicator.classList.remove('hidden');
        productsContainer.classList.add('hidden');
    };

    const hideLoading = () => {
        loadingIndicator.classList.add('hidden');
        productsContainer.classList.remove('hidden');
    };

    const loadProducts = async () => {
        showLoading();
        try {
            const products = await productsApi.fetchProducts();
            productView.renderProducts(products);
        } catch (error) {
            console.error('Error loading products:', error);
            productsContainer.innerHTML = '<p>Erro ao carregar produtos.</p>';
        } finally {
            hideLoading();
        }
    };

    loadProducts();
});

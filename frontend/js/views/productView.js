/**
 * Renders the list of products into the DOM.
 * @param {Array<object>} products - The array of product objects.
 */
export const renderProducts = (products) => {
    const container = document.getElementById('products-container');
    if (!container) return;

    if (!products || products.length === 0) {
        container.innerHTML = '<p>Nenhum produto encontrado.</p>';
        return;
    }

    const productCards = products.map(product => `
        <div class="product" data-product-id="${product.id}">
            <img src="${product.image_url || 'https://via.placeholder.com/150'}" alt="${product.name}">
            <h3>${product.name}</h3>
            <p class="price">Preço: R$ ${product.price.toFixed(2)}</p>
            <p>Estoque: ${product.stock}</p>
            <button class="add-to-cart-btn">Adicionar ao Carrinho</button>
        </div>
    `).join('');

    container.innerHTML = productCards;
};

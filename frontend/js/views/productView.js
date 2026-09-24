import { escapeHtml, sanitizeUrl } from '../utils/sanitize.js';

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

    const productCards = products.map(product => {
        const id = escapeHtml(product.id);
        const name = escapeHtml(product.name);
        const imageUrl = sanitizeUrl(product.image_url);
        const price = typeof product.price === 'number' ? product.price.toFixed(2) : escapeHtml(product.price);
        const stock = escapeHtml(product.stock);

        return `
        <div class="product" data-product-id="${id}">
            <img src="${imageUrl}" alt="${name}">
            <h3>${name}</h3>
            <p class="price">Preço: R$ ${price}</p>
            <p>Estoque: ${stock}</p>
            <button class="add-to-cart-btn">Adicionar ao Carrinho</button>
        </div>
    `;
    }).join('');

    container.innerHTML = productCards;
};

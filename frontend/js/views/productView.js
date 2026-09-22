const productView = {
    renderProducts: (products) => {
        const container = document.getElementById('products-container');
        if (!container) return;

        if (products.length === 0) {
            container.innerHTML = '<p>Nenhum produto encontrado.</p>';
            return;
        }

        const productCards = products.map(product => `
            <div class="product-card">
                <h2>${product.name}</h2>
                <p>${product.description || ''}</p>
                <p><strong>Preço:</strong> R$ ${product.price.toFixed(2)}</p>
                <p><strong>Estoque:</strong> ${product.stock}</p>
            </div>
        `).join('');

        container.innerHTML = productCards;
    }
};

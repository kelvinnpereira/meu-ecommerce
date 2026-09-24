// frontend/js/views/cartView.js

let productsMap = new Map();

/**
 * Stores the list of products for lookup when rendering cart items.
 * @param {Array<object>} products - The array of products from the API.
 */
export const setProducts = (products) => {
    productsMap.clear();
    if (products) {
        products.forEach((p) => productsMap.set(String(p.id), p));
    }
};

/**
 * Formats a number into a BRL currency string with standard spaces.
 * @param {number} value - The number to format.
 * @returns {string} - The formatted currency string.
 */
const formatCurrency = (value) => {
    const formatted = (value || 0).toLocaleString('pt-BR', {
        style: 'currency',
        currency: 'BRL',
    });
    return formatted.replace(/\u00a0/g, ' ');
};

/**
 * Renders a single cart item into an HTML string matching style.css structure.
 * @param {object} item - The cart item object from the API.
 * @returns {string} - The HTML string for the cart item.
 */
const renderCartItem = (item) => {
    const product = productsMap.get(String(item.product_id));
    const productName =
        (product && product.name) ||
        (item.product && item.product.name) ||
        `Produto #${item.product_id}`;
    const unitPrice = item.unit_price
        ? parseFloat(item.unit_price)
        : (product && product.price) || 0;
    const stock = (product && product.stock) || 99;

    return `
        <div class="cart-item" data-product-id="${item.product_id}">
            <div class="item-info">
                <strong>${productName}</strong>
                <div>${formatCurrency(unitPrice)}</div>
            </div>
            <div class="item-actions">
                <input type="number" class="item-quantity" value="${item.quantity}" min="0" max="${stock}" />
                <button class="remove-item-btn">Remover</button>
            </div>
        </div>
    `;
};

export let isRendering = false;

/**
 * Renders the entire cart view based on the provided cart data.
 * @param {import('../domain/cart.js').Cart | null} cart - The cart object.
 */
export const render = (cart) => {
    isRendering = true;
    try {
        const cartItemsContainer = document.getElementById('cart-items-container');
        const subtotalEl = document.getElementById('cart-subtotal');
        const discountEl = document.getElementById('cart-discount');
        const totalEl = document.getElementById('cart-total');
        const couponForm = document.getElementById('coupon-form');
        const appliedCouponInfo = document.getElementById('applied-coupon-info');
        const appliedCouponCode = document.getElementById('applied-coupon-code');
        const couponInput = document.getElementById('coupon-code');

        if (!cart || cart.items.length === 0) {
            if (cartItemsContainer) {
                cartItemsContainer.innerHTML = '<p>Seu carrinho está vazio.</p>';
            }
        } else {
            if (cartItemsContainer) {
                cartItemsContainer.innerHTML = cart.items.map(renderCartItem).join('');
            }
        }

        const totals = cart ? cart.totals : { subtotal: 0, discount: 0, total: 0 };
        if (subtotalEl) subtotalEl.textContent = formatCurrency(totals.subtotal);
        if (discountEl) {
            discountEl.textContent =
                totals.discount > 0
                    ? `- ${formatCurrency(totals.discount)}`
                    : formatCurrency(0);
        }
        if (totalEl) totalEl.textContent = formatCurrency(totals.total);

        if (cart && cart.coupon) {
            if (couponForm) couponForm.style.display = 'none';
            if (appliedCouponInfo) appliedCouponInfo.style.display = 'flex';
            if (appliedCouponCode) appliedCouponCode.textContent = cart.coupon.code;
        } else {
            if (couponForm) couponForm.style.display = 'flex';
            if (appliedCouponInfo) appliedCouponInfo.style.display = 'none';
            if (couponInput) couponInput.value = '';
        }
    } finally {
        isRendering = false;
    }
};

import * as productsApi from './api/productsApi.js';
import * as productView from './views/productView.js';
import * as cartApi from './api/cartApi.js';
import * as cartView from './views/cartView.js';
import { Cart } from './domain/cart.js';

const USER_ID = 'user-123'; // Simulating a logged-in user
let cart = null;

// --- Loading Indicators ---
const showLoading = () => {
    document.getElementById('loading-indicator').classList.remove('hidden');
    document.getElementById('products-container').classList.add('hidden');
};

const hideLoading = () => {
    document.getElementById('loading-indicator').classList.add('hidden');
    document.getElementById('products-container').classList.remove('hidden');
};

// --- Cart Handlers ---

const refreshCart = async () => {
    try {
        const cartData = await cartApi.getCart(USER_ID);
        cart = cartData ? new Cart(cartData) : null;
        cartView.render(cart);
    } catch (error) {
        console.error('Failed to refresh cart:', error);
        cartView.render(null); // Render empty cart on error
    }
};

const inFlightUpdates = new Set();
const pendingQuantities = new Map();

const handleUpdateQuantity = async (productId, quantity) => {
    if (inFlightUpdates.has(productId)) {
        pendingQuantities.set(productId, quantity);
        return;
    }

    const currentItem =
        cart && cart.items.find((i) => String(i.product_id) === String(productId));
    if (!currentItem && quantity === 0) {
        return;
    }

    inFlightUpdates.add(productId);
    try {
        const updatedCartData =
            quantity > 0
                ? await cartApi.updateItemQuantity(USER_ID, productId, quantity)
                : await cartApi.removeItem(USER_ID, productId);

        cart = new Cart(updatedCartData);
        cartView.render(cart);
    } catch (error) {
        console.error(
            `Failed to update quantity for product ${productId}:`,
            error
        );
        alert('Erro ao atualizar a quantidade do item.');
        cartView.render(cart); // Revert to last known good state
    } finally {
        inFlightUpdates.delete(productId);
        if (pendingQuantities.has(productId)) {
            const nextQuantity = pendingQuantities.get(productId);
            pendingQuantities.delete(productId);
            const itemNow =
                cart && cart.items.find((i) => String(i.product_id) === String(productId));
            const currentQty = itemNow ? itemNow.quantity : 0;
            if (currentQty !== nextQuantity) {
                await handleUpdateQuantity(productId, nextQuantity);
            }
        }
    }
};

const handleRemoveItem = async (productId) => {
    if (inFlightUpdates.has(productId)) {
        return;
    }
    if (cart && cart.status === 'ORDER_CREATED') {
        await cartApi.createCart(USER_ID);
        await refreshCart();
        return;
    }
    const currentItem =
        cart && cart.items.find((i) => String(i.product_id) === String(productId));
    if (!currentItem) {
        return;
    }

    inFlightUpdates.add(productId);
    try {
        const updatedCartData = await cartApi.removeItem(USER_ID, productId);
        cart = new Cart(updatedCartData);
        cartView.render(cart);
    } catch (error) {
        console.error(`Failed to remove product ${productId}:`, error);
        if (error.body && error.body.detail && error.body.detail.includes('ORDER_CREATED')) {
            await cartApi.createCart(USER_ID);
            await refreshCart();
            return;
        }
        alert('Erro ao remover o item do carrinho.');
    } finally {
        inFlightUpdates.delete(productId);
    }
};

const handleApplyCoupon = async (couponCode) => {
    if (!couponCode) {
        alert('Por favor, insira um código de cupom.');
        return;
    }
    try {
        const updatedCartData = await cartApi.applyCoupon(USER_ID, couponCode);
        cart = new Cart(updatedCartData);
        cartView.render(cart);
    } catch (error) {
        console.error(`Failed to apply coupon ${couponCode}:`, error);
        const errorMessage = error.body
            ? error.body.detail
            : 'Erro ao aplicar o cupom.';
        alert(errorMessage);
    }
};

const handleRemoveCoupon = async () => {
    try {
        const updatedCartData = await cartApi.removeCoupon(USER_ID);
        cart = new Cart(updatedCartData);
        cartView.render(cart);
    } catch (error) {
        console.error('Failed to remove coupon:', error);
        alert('Erro ao remover o cupom.');
    }
};

const handleAddToCart = async (productId, quantity = 1) => {
    try {
        if (cart && cart.status === 'ORDER_CREATED') {
            await cartApi.createCart(USER_ID);
        }
        const updatedCartData = await cartApi.addItem(
            USER_ID,
            productId,
            quantity
        );
        cart = new Cart(updatedCartData);
        cartView.render(cart);
    } catch (error) {
        console.error(`Failed to add product ${productId} to cart:`, error);
        if (error.body && error.body.detail && error.body.detail.includes('ORDER_CREATED')) {
            try {
                await cartApi.createCart(USER_ID);
                const retryCartData = await cartApi.addItem(USER_ID, productId, quantity);
                cart = new Cart(retryCartData);
                cartView.render(cart);
                return;
            } catch (retryErr) {
                console.error('Falha ao adicionar item após criar novo carrinho:', retryErr);
            }
        }
        const errorMessage = error.body
            ? error.body.detail
            : 'Erro ao adicionar o produto ao carrinho.';
        alert(errorMessage);
    }
};

const handleCheckoutAction = async () => {
    if (!cart) {
        alert('Seu carrinho está vazio.');
        return;
    }

    if (cart.status === 'ORDER_CREATED') {
        try {
            await cartApi.createCart(USER_ID);
            await refreshCart();
        } catch (error) {
            console.error('Falha ao iniciar novo carrinho:', error);
            alert('Erro ao iniciar nova compra.');
        }
        return;
    }

    if (!cart.items || cart.items.length === 0) {
        alert('Seu carrinho está vazio.');
        return;
    }

    try {
        if (cart.status === 'IN_CHECKOUT') {
            const result = await cartApi.confirmOrder(USER_ID);
            alert(result.message || 'Pedido confirmado com sucesso!');
            await cartApi.createCart(USER_ID);
            await refreshCart();
        } else {
            const updatedCartData = await cartApi.startCheckout(USER_ID);
            cart = new Cart(updatedCartData);
            cartView.render(cart);
        }
    } catch (error) {
        console.error('Falha na operação de checkout:', error);
        const errorMessage = error.body
            ? error.body.detail
            : 'Erro ao processar o checkout.';
        alert(errorMessage);
        await refreshCart();
    }
};

const handleReturnToCart = async () => {
    try {
        const updatedCartData = await cartApi.returnToCart(USER_ID);
        cart = new Cart(updatedCartData);
        cartView.render(cart);
    } catch (error) {
        console.error('Falha ao retornar ao carrinho:', error);
        const errorMessage = error.body
            ? error.body.detail
            : 'Erro ao retornar para edição.';
        alert(errorMessage);
    }
};

// --- Event Listeners ---

const setupEventListeners = () => {
    const productsContainer = document.getElementById('products-container');
    const cartSection = document.getElementById('cart-section');

    // Add to cart button
    productsContainer.addEventListener('click', (event) => {
        if (event.target.classList.contains('add-to-cart-btn')) {
            const productElement = event.target.closest('.product');
            const productId = productElement.dataset.productId;
            handleAddToCart(productId);
        }
    });

    // Cart interactions (using event delegation)
    cartSection.addEventListener('click', (event) => {
        if (event.target.id === 'apply-coupon-btn') {
            const couponInput = document.getElementById('coupon-code');
            handleApplyCoupon(couponInput.value.trim().toUpperCase());
        }
        if (event.target.id === 'remove-coupon-btn') {
            handleRemoveCoupon();
        }
        if (event.target.id === 'checkout-btn') {
            handleCheckoutAction();
        }
        if (event.target.id === 'return-to-cart-btn') {
            handleReturnToCart();
        }
        if (event.target.classList.contains('remove-item-btn')) {
            const productId = event.target.closest('.cart-item').dataset.productId;
            handleRemoveItem(productId);
        }
    });

    // Handle quantity changes on 'input' (Playwright fill) and 'change' (user commit)
    const onQuantityChange = (event) => {
        if (cartView.isRendering) return;
        if (event.target.classList.contains('item-quantity')) {
            const quantity = parseInt(event.target.value, 10);
            if (isNaN(quantity) || quantity < 0) return;
            const cartItemEl = event.target.closest('.cart-item');
            if (!cartItemEl) return;
            const productId = cartItemEl.dataset.productId;
            if (!productId) return;
            const currentItem =
                cart && cart.items.find((i) => String(i.product_id) === String(productId));
            if (!currentItem) return;
            if (currentItem.quantity === quantity) return;
            handleUpdateQuantity(productId, quantity);
        }
    };

    cartSection.addEventListener('input', onQuantityChange);
    cartSection.addEventListener('change', onQuantityChange);
};

// --- App Initialization ---

document.addEventListener('DOMContentLoaded', async () => {
    showLoading();
    try {
        const products = await productsApi.fetchProducts();
        productView.renderProducts(products);
        cartView.setProducts(products);

        await refreshCart();

        setupEventListeners();
    } catch (error) {
        console.error('Error initializing the app:', error);
        document.getElementById('products-container').innerHTML =
            '<p>Erro ao carregar a loja. Tente novamente mais tarde.</p>';
    } finally {
        hideLoading();
    }
});

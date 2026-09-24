// frontend/js/domain/cart.js

/**
 * Represents the Cart data structure on the client-side.
 * It standardizes the cart object received from the API.
 */
export class Cart {
    constructor(data = {}) {
        this.id = data.id;
        this.userId = data.user_id;
        this.status = data.status;
        this.coupon = data.coupon || null;
        this.items = data.items || [];

        if (data.totals) {
            this.totals = {
                subtotal: parseFloat(data.totals.subtotal) || 0,
                discount: parseFloat(data.totals.discount) || 0,
                total: parseFloat(data.totals.total) || 0,
            };
        } else {
            this.totals = {
                subtotal: parseFloat(data.subtotal) || 0,
                discount: parseFloat(data.discount) || 0,
                total: parseFloat(data.total) || 0,
            };
        }
    }
}

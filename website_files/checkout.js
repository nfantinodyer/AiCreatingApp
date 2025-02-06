import { CartModule } from './cart.js';
import { PRODUCTS } from './productsData.js';
import { COUPONS } from './couponsData.js';
import { showToast, escapeHTML } from './utils.js';

export const CheckoutModule = (function() {
    function initializeCheckout() {
        CartModule.loadCart();
        const cart = CartModule.getCart();
        if (cart.length === 0) {
            showToast('Your cart is empty.', 'info');
            setTimeout(() => {
                window.location.href = 'cart.html';
            }, 1000);
            return;
        }

        displayOrderSummary();

        const checkoutForm = document.getElementById('checkoutForm');
        if (checkoutForm) {
            checkoutForm.addEventListener('submit', handleCheckoutForm);
        }
    }

    function displayOrderSummary() {
        const orderSummaryDiv = document.getElementById('orderSummary');
        if (!orderSummaryDiv) return;

        const cart = CartModule.getCart();
        let summaryHTML = '<table><tr><th>Product</th><th>Quantity</th><th>Price</th></tr>';
        let totalPrice = 0;

        cart.forEach(item => {
            const product = PRODUCTS[item.productName];
            const itemPrice = product.price * item.quantity;
            totalPrice += itemPrice;
            summaryHTML += `
                <tr>
                    <td>${escapeHTML(item.productName)}</td>
                    <td>${item.quantity}</td>
                    <td>$${itemPrice.toFixed(2)}</td>
                </tr>
            `;
        });

        let discount = 0;
        let discountDescription = '';
        let shippingCost = 5.00;
        const storedCoupon = localStorage.getItem('appliedCoupon');
        let appliedCoupon = storedCoupon ? JSON.parse(storedCoupon) : null;

        if (appliedCoupon) {
            const coupon = COUPONS[appliedCoupon.code];
            if (coupon && new Date(coupon.expires) >= new Date()) {
                if (coupon.type === 'percentage') {
                    discount = totalPrice * coupon.value;
                    discountDescription = `Discount (${coupon.value * 100}% off): -$${discount.toFixed(2)}`;
                } else if (coupon.type === 'fixed') {
                    discount = coupon.value;
                    discountDescription = `Discount ($${coupon.value.toFixed(2)} off): -$${discount.toFixed(2)}`;
                } else if (coupon.type === 'shipping') {
                    shippingCost = 0;
                    discountDescription = 'Free Shipping Applied';
                }
            } else {
                appliedCoupon = null;
                localStorage.removeItem('appliedCoupon');
            }
        }

        if (discount > totalPrice) discount = totalPrice;

        let finalTotal = totalPrice - discount + shippingCost;

        summaryHTML += '</table>';
        summaryHTML += `<p>Subtotal: $${totalPrice.toFixed(2)}</p>`;
        if (discount > 0 || discountDescription) {
            summaryHTML += `<p>${discountDescription}</p>`;
        }
        summaryHTML += `<p>Shipping: $${shippingCost.toFixed(2)}</p>`;
        summaryHTML += `<p>Total Price: $${finalTotal.toFixed(2)}</p>`;
        orderSummaryDiv.innerHTML = summaryHTML;
    }

    function handleCheckoutForm(event) {
        event.preventDefault();
        const fullName = document.getElementById('fullName').value.trim();
        const email = document.getElementById('email').value.trim();
        const address = document.getElementById('address').value.trim();
        const city = document.getElementById('city').value.trim();
        const state = document.getElementById('state').value.trim();
        const zip = document.getElementById('zip').value.trim();
        const country = document.getElementById('country').value.trim();
        const cardNumber = document.getElementById('cardNumber').value.trim();
        const cardExpiry = document.getElementById('cardExpiry').value.trim();
        const cardCVC = document.getElementById('cardCVC').value.trim();

        if (!fullName || !email || !address || !city || !state || !zip || !country || !cardNumber || !cardExpiry || !cardCVC) {
            showToast('Please fill in all required fields.', 'error');
            return;
        }

        const emailPattern = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
        if (!emailPattern.test(email)) {
            showToast('Please enter a valid email address.', 'error');
            return;
        }

        const zipPattern = /^\d{5}$/;
        if (!zipPattern.test(zip)) {
            showToast('Please enter a valid ZIP code.', 'error');
            return;
        }

        const cardNumberPattern = /^\d{16}$/;
        if (!cardNumberPattern.test(cardNumber.replace(/\s+/g, ''))) {
            showToast('Please enter a valid 16-digit card number.', 'error');
            return;
        }

        const cardExpiryPattern = /^(0[1-9]|1[0-2])\/\d{2}$/;
        if (!cardExpiryPattern.test(cardExpiry)) {
            showToast('Please enter a valid expiry date in MM/YY format.', 'error');
            return;
        }
        const [expMonth, expYear] = cardExpiry.split('/').map(num => parseInt(num));
        const currentDate = new Date();
        const currentMonth = currentDate.getMonth() + 1;
        const currentYear = parseInt(currentDate.getFullYear().toString().substr(-2));
        if (expYear < currentYear || (expYear === currentYear && expMonth < currentMonth)) {
            showToast('Your card expiry date is in the past.', 'error');
            return;
        }

        const cardCVCPattern = /^\d{3,4}$/;
        if (!cardCVCPattern.test(cardCVC)) {
            showToast('Please enter a valid CVC code.', 'error');
            return;
        }

        showToast('Processing your payment...', 'info');
        setTimeout(() => {
            showToast('Payment successful! Thank you for your purchase.', 'success');
            saveOrderHistory();
            CartModule.clearCart();
            localStorage.removeItem('appliedCoupon');
            setTimeout(() => {
                window.location.href = 'index.html';
            }, 2000);
        }, 2000);
    }

    function saveOrderHistory() {
        const orderHistory = JSON.parse(localStorage.getItem('orderHistory')) || [];
        const cart = CartModule.getCart();
        let totalPrice = 0;

        cart.forEach(item => {
            const product = PRODUCTS[item.productName];
            totalPrice += product.price * item.quantity;
        });

        let discount = 0;
        let shippingCost = 5.00;
        const storedCoupon = localStorage.getItem('appliedCoupon');
        let appliedCoupon = storedCoupon ? JSON.parse(storedCoupon) : null;

        if (appliedCoupon) {
            const coupon = COUPONS[appliedCoupon.code];
            if (coupon && new Date(coupon.expires) >= new Date()) {
                if (coupon.type === 'percentage') {
                    discount = totalPrice * coupon.value;
                } else if (coupon.type === 'fixed') {
                    discount = coupon.value;
                } else if (coupon.type === 'shipping') {
                    shippingCost = 0;
                }
            }
        }

        if (discount > totalPrice) discount = totalPrice;

        let finalTotal = totalPrice - discount + shippingCost;

        const newOrder = {
            orderNumber: Date.now(),
            date: new Date().toLocaleDateString(),
            items: cart,
            total: finalTotal,
            discount: discount,
            shippingCost: shippingCost
        };
        orderHistory.push(newOrder);
        localStorage.setItem('orderHistory', JSON.stringify(orderHistory));
    }

    return {
        initializeCheckout
    };
})();

document.addEventListener('DOMContentLoaded', () => {
    if (window.location.pathname.endsWith('checkout.html')) {
        CheckoutModule.initializeCheckout();
    }
});
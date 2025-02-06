import { showToast, escapeHTML } from './utils.js';
import { PRODUCTS } from './productsData.js';
import { COUPONS } from './couponsData.js';

export const CartModule = (function() {
    let cart = [];
    let appliedCoupon = null;

    function loadCart() {
        const storedCart = localStorage.getItem('cart');
        if (storedCart) {
            cart = JSON.parse(storedCart);
        }
        const storedCoupon = localStorage.getItem('appliedCoupon');
        if (storedCoupon) {
            appliedCoupon = JSON.parse(storedCoupon);
        }
    }

    function saveCart() {
        localStorage.setItem('cart', JSON.stringify(cart));
        localStorage.setItem('appliedCoupon', JSON.stringify(appliedCoupon));
    }

    function addToCart(productName, quantity) {
        const index = cart.findIndex(item => item.productName === productName);
        if (index > -1) {
            cart[index].quantity += quantity;
        } else {
            cart.push({ productName, quantity });
        }
        saveCart();
    }

    function getCart() {
        return cart;
    }

    function getCartCount() {
        return cart.reduce((total, item) => total + item.quantity, 0);
    }

    function clearCart() {
        cart = [];
        appliedCoupon = null;
        saveCart();
    }

    function displayCart() {
        const cartItemsDiv = document.getElementById('cartItems');
        if (!cartItemsDiv) return;

        if (cart.length === 0) {
            cartItemsDiv.innerHTML = '<p>Your cart is empty.</p>';
            document.getElementById('totalPrice').textContent = '';
            document.getElementById('checkoutButton').disabled = true;
            document.getElementById('emptyCartMessage').classList.remove('hidden');
            return;
        } else {
            document.getElementById('emptyCartMessage').classList.add('hidden');
            document.getElementById('checkoutButton').disabled = false;
        }

        let cartHTML = '<table><tr><th>Product</th><th>Quantity</th><th>Price</th><th></th></tr>';
        let totalPrice = 0;

        cart.forEach(item => {
            const product = PRODUCTS[item.productName];
            const itemPrice = product.price * item.quantity;
            totalPrice += itemPrice;
            cartHTML += `
                <tr>
                    <td>${escapeHTML(item.productName)}</td>
                    <td>
                        <input type="number" value="${item.quantity}" min="1" max="10" data-product="${escapeHTML(item.productName)}" class="quantity-input">
                    </td>
                    <td>$${itemPrice.toFixed(2)}</td>
                    <td>
                        <button data-product="${escapeHTML(item.productName)}" class="remove-item">Remove</button>
                    </td>
                </tr>
            `;
        });

        cartHTML += '</table>';
        cartItemsDiv.innerHTML = cartHTML;

        let discount = 0;
        let discountDescription = '';
        let shippingCost = 5.00;

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
                saveCart();
            }
        }

        if (discount > totalPrice) discount = totalPrice;

        let finalTotal = totalPrice - discount + shippingCost;

        let totalPriceText = `Total Price: $${finalTotal.toFixed(2)}`;
        totalPriceText += `<br>Subtotal: $${totalPrice.toFixed(2)}`;
        if (discount > 0 || discountDescription) {
            totalPriceText += `<br>${discountDescription}`;
        }
        totalPriceText += `<br>Shipping: $${shippingCost.toFixed(2)}`;
        document.getElementById('totalPrice').innerHTML = totalPriceText;

        document.querySelectorAll('.quantity-input').forEach(input => {
            input.addEventListener('change', updateQuantity);
        });
        document.querySelectorAll('.remove-item').forEach(button => {
            button.addEventListener('click', removeItem);
        });
    }

    function updateQuantity(event) {
        const productName = event.target.getAttribute('data-product');
        let newQuantity = parseInt(event.target.value);
        if (isNaN(newQuantity) || newQuantity < 1 || newQuantity > 10) {
            showToast('Quantity must be between 1 and 10.', 'error');
            event.target.value = 1;
            newQuantity = 1;
        }
        const item = cart.find(item => item.productName === productName);
        if (item) {
            item.quantity = newQuantity;
            saveCart();
            displayCart();
        }
    }

    function removeItem(event) {
        const productName = event.target.getAttribute('data-product');
        cart = cart.filter(item => item.productName !== productName);
        saveCart();
        displayCart();
        showToast(`${escapeHTML(productName)} has been removed from your cart.`, 'info');
    }

    function applyCoupon(event) {
        event.preventDefault();
        const couponCode = document.getElementById('couponCode').value.trim().toUpperCase();
        if (COUPONS[couponCode]) {
            const coupon = COUPONS[couponCode];
            if (new Date(coupon.expires) >= new Date()) {
                appliedCoupon = { code: couponCode };
                saveCart();
                displayCart();
                showToast(`Coupon "${couponCode}" applied successfully!`, 'success');
            } else {
                showToast('This coupon has expired.', 'error');
            }
        } else {
            showToast('Invalid coupon code.', 'error');
        }
    }

    function proceedToCheckout() {
        window.location.href = 'checkout.html';
    }

    return {
        loadCart,
        addToCart,
        getCart,
        getCartCount,
        clearCart,
        displayCart,
        applyCoupon,
        proceedToCheckout
    };
})();

document.addEventListener('DOMContentLoaded', () => {
    CartModule.loadCart();
    CartModule.displayCart();

    const couponForm = document.getElementById('couponForm');
    if (couponForm) {
        couponForm.addEventListener('submit', CartModule.applyCoupon);
    }

    const checkoutButton = document.getElementById('checkoutButton');
    if (checkoutButton) {
        checkoutButton.addEventListener('click', CartModule.proceedToCheckout);
    }
});
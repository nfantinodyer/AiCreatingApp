import { PRODUCTS } from './productsData.js';
import { COUPONS } from './couponsData.js';
import { showToast, escapeHTML } from './utils.js';

let cart = [];
let appliedCoupons = [];

const CartModule = (function() {
    function addToCart(product, quantity) {
        if (quantity < 1 || quantity > 10) {
            showToast('Please select a valid quantity between 1 and 10.', 'error');
            return;
        }
        const cartItem = cart.find(item => item.product === product);
        if (cartItem) {
            if (cartItem.quantity + quantity > 10) {
                showToast('Maximum quantity for this product is 10.', 'error');
                return;
            }
            cartItem.quantity += quantity;
        } else {
            cart.push({ product, quantity });
        }
        saveCart();
        displayCart();
        showToast(`${product} has been added to your cart!`, 'success');
    }

    function displayCart() {
        const cartDiv = document.getElementById('cartItems');
        const totalPriceDiv = document.getElementById('totalPrice');
        const checkoutButton = document.getElementById('checkoutButton');
        const emptyCartMessage = document.getElementById('emptyCartMessage');
        const cartCount = document.getElementById('cart-count');
        cartDiv.innerHTML = '';
        let totalPrice = 0;
        cart.forEach((item, index) => {
            const pricePerUnit = PRODUCTS[item.product].price;
            let subtotal = pricePerUnit * item.quantity;
            appliedCoupons.forEach(coupon => {
                if (coupon.type === 'percentage') {
                    subtotal *= (1 - coupon.value);
                }
                // Add other coupon types if necessary
            });
            totalPrice += subtotal;
            const productImage = PRODUCTS[item.product].image;
            cartDiv.innerHTML += `
                <div class="cart-item" role="region" aria-label="Cart item: ${escapeHTML(item.product)}">
                    <img src="${escapeHTML(productImage)}" alt="${escapeHTML(item.product)}" class="cart-image" loading="lazy">
                    <div class="cart-details">
                        <p><strong>${escapeHTML(item.product)}</strong></p>
                        <p>SKU: ${escapeHTML(PRODUCTS[item.product].sku)}</p>
                        <p>Price: $${pricePerUnit.toFixed(2)} each</p>
                        <label for="quantity-${index}" hidden>Quantity for ${escapeHTML(item.product)}</label>
                        <p>
                            Quantity: 
                            <input type="number" id="quantity-${index}" value="${item.quantity}" min="1" max="10" data-index="${index}" class="cart-quantity" aria-label="Quantity for ${escapeHTML(item.product)}">
                        </p>
                        <p>Subtotal: $${subtotal.toFixed(2)}</p>
                        <button class="btn remove-from-cart" data-index="${index}" aria-label="Remove ${escapeHTML(item.product)} from cart">Remove</button>
                    </div>
                </div>`;
        });
        if (appliedCoupons.length > 0) {
            appliedCoupons.forEach(coupon => {
                if (coupon.type === 'percentage') {
                    cartDiv.innerHTML += `<p><strong>Discount Applied (${escapeHTML(coupon.code)}): ${coupon.value * 100}%</strong></p>`;
                }
                // Handle other coupon types
            });
        }
        if (cart.length === 0) {
            if (checkoutButton) checkoutButton.disabled = true;
            if (emptyCartMessage) emptyCartMessage.style.display = 'block';
        } else {
            if (checkoutButton) checkoutButton.disabled = false;
            if (emptyCartMessage) emptyCartMessage.style.display = 'none';
        }
        if (totalPriceDiv) {
            totalPriceDiv.innerHTML = `<strong>Total Price: $${totalPrice.toFixed(2)}</strong>`;
        }
        cartCount.textContent = cart.length;
        attachCartEventListeners();
    }

    function removeFromCart(index) {
        cart.splice(index, 1);
        saveCart();
        displayCart();
        showToast('Item removed from cart.', 'info');
    }

    function updateQuantity(index, newQuantity) {
        newQuantity = parseInt(newQuantity);
        if (isNaN(newQuantity) || newQuantity < 1 || newQuantity > 10) {
            showToast('Please select a valid quantity between 1 and 10.', 'error');
            displayCart();
            return;
        }
        cart[index].quantity = newQuantity;
        saveCart();
        displayCart();
        showToast('Cart updated.', 'success');
    }

    function applyCoupon() {
        const couponCode = document.getElementById('couponCode').value.trim().toUpperCase();
        const coupon = COUPONS[couponCode];
        const today = new Date();
        if (coupon && new Date(coupon.expires) > today) {
            if (appliedCoupons.find(c => c.code === couponCode)) {
                showToast('Coupon already applied.', 'info');
                return;
            }
            appliedCoupons.push(coupon);
            saveCart();
            displayCart();
            showToast(`Coupon ${couponCode} applied!`, 'success');
        } else {
            showToast('Invalid or expired coupon code.', 'error');
        }
    }

    function proceedToCheckout() {
        if (cart.length === 0) {
            showToast('Your cart is empty.', 'error');
            return;
        }
        window.location.href = 'checkout.html';
    }

    function saveCart() {
        try {
            localStorage.setItem('cart', JSON.stringify(cart));
            localStorage.setItem('appliedCoupons', JSON.stringify(appliedCoupons));
        } catch (e) {
            console.error('Could not save cart', e);
            showToast('Failed to save cart. Please try again.', 'error');
        }
    }

    function loadCart() {
        const savedCart = localStorage.getItem('cart');
        const savedCoupons = localStorage.getItem('appliedCoupons');
        if (savedCart) {
            try {
                cart = JSON.parse(savedCart);
            } catch (e) {
                console.error('Could not parse cart data', e);
                cart = [];
                saveCart();
            }
        }
        if (savedCoupons) {
            try {
                appliedCoupons = JSON.parse(savedCoupons);
            } catch (e) {
                console.error('Could not parse coupons data', e);
                appliedCoupons = [];
                saveCart();
            }
        }
        displayCart();
    }

    function attachCartEventListeners() {
        document.querySelectorAll('.remove-from-cart').forEach(button => {
            button.addEventListener('click', () => {
                const index = button.dataset.index;
                removeFromCart(index);
            });
        });

        document.querySelectorAll('.cart-quantity').forEach(input => {
            input.addEventListener('change', (e) => {
                const index = e.target.dataset.index;
                const newQuantity = e.target.value;
                updateQuantity(index, newQuantity);
            });
        });

        const applyCouponButton = document.getElementById('applyCouponButton');
        if (applyCouponButton) {
            applyCouponButton.addEventListener('click', applyCoupon);
        }

        const checkoutButton = document.getElementById('checkoutButton');
        if (checkoutButton) {
            checkoutButton.addEventListener('click', proceedToCheckout);
        }
    }

    function getCart() {
        return cart;
    }

    function clearCart() {
        cart = [];
        appliedCoupons = [];
        saveCart();
        displayCart();
    }

    window.addEventListener('storage', (event) => {
        if (event.key === 'cart' || event.key === 'appliedCoupons') {
            loadCart();
        }
    });

    return {
        addToCart,
        displayCart,
        removeFromCart,
        updateQuantity,
        applyCoupon,
        proceedToCheckout,
        loadCart,
        getCart,
        clearCart
    };
})();

document.addEventListener('DOMContentLoaded', () => {
    CartModule.loadCart();
});
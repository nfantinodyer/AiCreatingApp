import { CartModule } from './products.js';
import { PRODUCTS } from './productsData.js';
import { COUPONS } from './couponsData.js';
import { showToast, escapeHTML } from './utils.js';

const stripe = Stripe('YOUR_PUBLIC_STRIPE_KEY');
const elements = stripe.elements();
const card = elements.create('card');
card.mount('#card-element');

card.addEventListener('change', function(event) {
    const displayError = document.getElementById('card-errors');
    if (event.error) {
        displayError.textContent = escapeHTML(event.error.message);
    } else {
        displayError.textContent = '';
    }
});

const checkoutForm = document.getElementById('checkoutForm');
if (checkoutForm) {
    checkoutForm.addEventListener('submit', handleFormSubmit);
}

function displayOrderSummary() {
    const orderSummaryDiv = document.getElementById('orderSummary');
    if (!orderSummaryDiv) return;

    const cart = CartModule.getCart();
    if (cart.length === 0) {
        orderSummaryDiv.innerHTML = '<p>Your cart is empty.</p>';
        return;
    }

    let summaryHTML = '<ul>';
    let totalPrice = 0;
    cart.forEach(item => {
        const price = PRODUCTS[item.product].price;
        let subtotal = price * item.quantity;
        const appliedCoupons = getAppliedCoupons();
        appliedCoupons.forEach(coupon => {
            if (coupon.type === 'percentage') {
                subtotal *= (1 - coupon.value);
            }
            // Handle other coupon types
        });
        totalPrice += subtotal;
        summaryHTML += `<li>${escapeHTML(item.product)} - $${price.toFixed(2)} x ${item.quantity} = $${subtotal.toFixed(2)}</li>`;
    });
    const discount = getTotalDiscount();
    if (discount > 0) {
        summaryHTML += `<li><strong>Discount: ${(discount * 100).toFixed(0)}%</strong></li>`;
    }
    summaryHTML += `</ul><p><strong>Total: $${totalPrice.toFixed(2)}</strong></p>`;
    orderSummaryDiv.innerHTML = summaryHTML;
}

function getAppliedCoupons() {
    try {
        const coupons = JSON.parse(localStorage.getItem('appliedCoupons')) || [];
        return coupons;
    } catch (e) {
        console.error('Could not parse coupons data', e);
        return [];
    }
}

function getTotalDiscount() {
    const coupons = getAppliedCoupons();
    let discount = 0;
    coupons.forEach(coupon => {
        if (coupon.type === 'percentage') {
            discount += coupon.value;
        }
        // Handle other coupon types
    });
    return discount > 1 ? 1 : discount;
}

async function fetchClientSecret() {
    const response = await fetch('/create-payment-intent', { // Ensure server supports this endpoint
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ cart: CartModule.getCart(), coupons: getAppliedCoupons() })
    });
    if (!response.ok) {
        throw new Error('Network response was not ok');
    }
    const data = await response.json();
    return data.clientSecret;
}

async function handleFormSubmit(event) {
    event.preventDefault();
    const submitButton = checkoutForm.querySelector('button[type="submit"]');
    submitButton.disabled = true;
    showToast('Processing your payment...', 'info');

    try {
        const clientSecret = await fetchClientSecret();
        const billingDetails = {
            name: document.getElementById('fullName').value,
            address: {
                line1: document.getElementById('address').value,
                city: document.getElementById('city').value,
                postal_code: document.getElementById('postalCode').value,
                country: document.getElementById('country').value
            }
        };

        const { paymentIntent, error } = await stripe.confirmCardPayment(clientSecret, {
            payment_method: {
                card: card,
                billing_details: billingDetails
            }
        });

        const displayError = document.getElementById('card-errors');
        if (error) {
            showToast(escapeHTML(error.message), 'error');
            displayError.textContent = escapeHTML(error.message);
            submitButton.disabled = false;
        } else if (paymentIntent.status === 'succeeded') {
            document.getElementById('successMessage').style.display = 'block';
            checkoutForm.style.display = 'none';
            showToast('Your order has been placed successfully!', 'success');
            CartModule.clearCart();
            submitButton.disabled = false;
            // Dynamically update schema.org Order
            updateOrderSchema(paymentIntent);
            // Optionally redirect to order confirmation page
            // window.location.href = 'order-confirmation.html';
        }
    } catch (err) {
        console.error(err);
        showToast('An unexpected error occurred. Please try again.', 'error');
        submitButton.disabled = false;
    }
}

function updateOrderSchema(paymentIntent) {
    const orderSchemaScript = document.createElement('script');
    orderSchemaScript.type = 'application/ld+json';
    const orderData = {
        "@context": "http://schema.org",
        "@type": "Order",
        "orderStatus": "http://schema.org/OrderProcessing",
        "orderDate": new Date().toISOString(),
        "customer": {
            "@type": "Person",
            "name": document.getElementById('fullName').value
        },
        "acceptedOffer": CartModule.getCart().map(item => ({
            "@type": "Offer",
            "itemOffered": {
                "@type": "Product",
                "name": item.product,
                "sku": PRODUCTS[item.product].sku,
                "price": PRODUCTS[item.product].price.toFixed(2),
                "priceCurrency": "USD"
            },
            "price": PRODUCTS[item.product].price.toFixed(2),
            "priceCurrency": "USD",
            "quantity": item.quantity
        }))
    };
    orderSchemaScript.textContent = JSON.stringify(orderData, null, 2);
    document.head.appendChild(orderSchemaScript);
}

export function initializeCheckout() {
    displayOrderSummary();
}

document.addEventListener('DOMContentLoaded', () => {
    if (window.location.pathname.endsWith('checkout.html')) {
        initializeCheckout();
    }
});
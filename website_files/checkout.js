import { CartModule } from './cart.js';
import { PRODUCTS } from './productsData.js';
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
        const subtotal = price * item.quantity * (1 - (parseFloat(localStorage.getItem('discount')) || 0));
        totalPrice += subtotal;
        summaryHTML += `<li>${escapeHTML(item.product)} - $${price.toFixed(2)} x ${item.quantity} = $${subtotal.toFixed(2)}</li>`;
    });
    const discount = parseFloat(localStorage.getItem('discount')) || 0;
    if (discount > 0) {
        summaryHTML += `<li><strong>Discount: ${(discount * 100).toFixed(0)}%</strong></li>`;
    }
    summaryHTML += `</ul><p><strong>Total: $${totalPrice.toFixed(2)}</strong></p>`;
    orderSummaryDiv.innerHTML = summaryHTML;
}

async function fetchClientSecret() {
    const response = await fetch('/create-payment-intent', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ cart: CartModule.getCart() })
    });
    const data = await response.json();
    return data.clientSecret;
}

async function handleFormSubmit(event) {
    event.preventDefault();
    const submitButton = checkoutForm.querySelector('button[type="submit"]');
    submitButton.disabled = true;

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

    try {
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
            // Optionally redirect to order confirmation page
            // window.location.href = 'order-confirmation.html';
        }
    } catch (err) {
        console.error(err);
        showToast('An unexpected error occurred. Please try again.', 'error');
        submitButton.disabled = false;
    }
}

function handleOrderTracking() {
    // Implementation for order tracking if applicable
}

export function initializeCheckout() {
    displayOrderSummary();
}

document.addEventListener('DOMContentLoaded', () => {
    if (window.location.pathname.endsWith('checkout.html')) {
        initializeCheckout();
    }
});

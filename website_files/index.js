import { CartModule } from './cart.js';
import { showToast } from './utils.js';

// Initialize modules when DOM is ready
document.addEventListener('DOMContentLoaded', () => {
    // Load the cart
    CartModule.loadCart();

    // Newsletter Form
    const newsletterForm = document.getElementById('newsletterForm');
    if (newsletterForm) {
        newsletterForm.addEventListener('submit', handleNewsletterForm);
    }

    // Initialize Featured Products
    initializeFeaturedProducts();
});

function handleNewsletterForm(event) {
    event.preventDefault();
    const emailInput = document.getElementById('newsletterEmail');
    const email = emailInput.value.trim();
    const emailPattern = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;

    if (!emailPattern.test(email)) {
        showToast('Please enter a valid email address.', 'error');
        document.getElementById('newsletterEmailError').textContent = 'Invalid email.';
        emailInput.setAttribute('aria-invalid', 'true');
        return;
    } else {
        document.getElementById('newsletterEmailError').textContent = '';
        emailInput.removeAttribute('aria-invalid');
    }

    // Get CSRF token
    const csrfTokenInput = document.querySelector('input[name="csrf_token"]');
    const csrfToken = csrfTokenInput ? csrfTokenInput.value : '';

    // Send the email to the server (Assuming an API endpoint exists)
    fetch('/subscribe-newsletter', {
        method: 'POST',
        headers: { 
            'Content-Type': 'application/json',
            'X-CSRF-Token': csrfToken
        },
        body: JSON.stringify({ email })
    })
    .then(response => {
        if (response.ok) {
            showToast('Thank you for subscribing to our newsletter!', 'success');
            newsletterForm.reset();
        } else {
            return response.json().then(errorData => {
                throw new Error(errorData.message || 'Failed to subscribe.');
            });
        }
    })
    .catch(error => {
        console.error(error);
        showToast('An error occurred. Please try again later.', 'error');
    });
}

function initializeFeaturedProducts() {
    // Highlight featured products or add any dynamic behavior
    // For example, you could fetch featured products from the server
    console.log('Featured products initialized.');
}
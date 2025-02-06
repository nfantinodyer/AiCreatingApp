import { CartModule } from './cart.js';
import { showToast } from './utils.js';

document.addEventListener('DOMContentLoaded', () => {
    CartModule.loadCart();

    // Newsletter Form
    const newsletterForm = document.getElementById('newsletterForm');
    if (newsletterForm) {
        newsletterForm.addEventListener('submit', handleNewsletterForm);
    }

    // Initialize Product Features if on Index Page
    if (window.location.pathname.endsWith('index.html') || window.location.pathname === '/') {
        // Example: Highlight featured products or similar
        initializeFeaturedProducts();
    }
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

    // Here you would typically send the email to the server
    showToast('Thank you for subscribing to our newsletter!', 'success');
    newsletterForm.reset();
}

function initializeFeaturedProducts() {
    // Example: You can add scripts to highlight featured products, animate them or similar
    console.log('Featured products initialized.');
}
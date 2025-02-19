import { CartModule } from './cart.js';
import { CheckoutModule } from './checkout.js';
import { ContactModule } from './contact.js';
import { ProductModule } from './products.js';
import { IndexModule } from './index.js';

// Initialize modules as needed based on the current page
document.addEventListener('DOMContentLoaded', () => {
    const path = window.location.pathname;
    if (path.endsWith('cart.html')) {
        CartModule.loadCart();
    } else if (path.endsWith('checkout.html')) {
        CheckoutModule.initializeCheckout();
    } else if (path.endsWith('contact.html')) {
        ContactModule.validateContactForm();
    } else if (path.endsWith('products.html')) {
        ProductModule.init();
    } else if (path.endsWith('index.html') || path === '/') {
        IndexModule.init();
    }
    // Common initializations can go here
});
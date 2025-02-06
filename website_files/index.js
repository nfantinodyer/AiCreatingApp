import { CartModule } from './cart.js';
import { showToast, escapeHTML } from './utils.js';
import { PRODUCTS } from './productsData.js';

document.addEventListener('DOMContentLoaded', () => {
    CartModule.loadCart();
    updateCartCount();
    const newsletterForm = document.getElementById('newsletterForm');
    if (newsletterForm) {
        newsletterForm.addEventListener('submit', handleNewsletterForm);
    }
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
    showToast('Thank you for subscribing to our newsletter!', 'success');
    newsletterForm.reset();
}

function initializeFeaturedProducts() {
    const featuredProductsSection = document.getElementById('featured-products');
    if (!featuredProductsSection) return;

    const featuredProducts = ['Organic Bananas', 'Golden Bananas'];
    let productsHTML = '<div class="product-list">';

    featuredProducts.forEach(productName => {
        const product = PRODUCTS[productName];
        productsHTML += `
            <article class="product">
                <figure>
                    <picture>
                        <source srcset="${escapeHTML(product.image)}" type="image/webp">
                        <img src="${escapeHTML(product.image.replace('.webp', '.jpg'))}" alt="${escapeHTML(productName)}" loading="lazy">
                    </picture>
                    <figcaption>${escapeHTML(product.description)}</figcaption>
                </figure>
                <h4>${escapeHTML(productName)}</h4>
                <p>Price: $${product.price.toFixed(2)} each</p>
                <a href="${escapeHTML(product.productPage)}" class="btn">View Product</a>
            </article>
        `;
    });

    productsHTML += '</div>';
    featuredProductsSection.innerHTML = productsHTML;
}

function updateCartCount() {
    const cartCount = document.getElementById('cart-count');
    if (cartCount) {
        cartCount.textContent = CartModule.getCartCount();
    }
}
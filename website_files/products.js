import { showToast, escapeHTML } from './utils.js';
import { PRODUCTS } from './productsData.js';
import { CartModule } from './cart.js';

document.addEventListener('DOMContentLoaded', () => {
    if (window.location.pathname.endsWith('products.html')) {
        displayProductListing();
        updateCartCount();
    }
});

function displayProductListing() {
    const productListingSection = document.getElementById('productListing');
    if (!productListingSection) return;

    let productsHTML = '';
    for (const [productName, product] of Object.entries(PRODUCTS)) {
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
    }

    productListingSection.innerHTML = productsHTML;
}

function updateCartCount() {
    const cartCount = document.getElementById('cart-count');
    if (cartCount) {
        cartCount.textContent = CartModule.getCartCount();
    }
}
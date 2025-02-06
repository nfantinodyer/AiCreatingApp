import { CartModule } from './cart.js';
import { PRODUCTS } from './productsData.js';
import { showToast, escapeHTML } from './utils.js';

document.addEventListener('DOMContentLoaded', () => {
    CartModule.loadCart();
    initializeProductPage();
    updateCartCount();
});

function initializeProductPage() {
    const productName = getProductFromURL();
    const product = PRODUCTS[productName];
    if (!product) {
        showToast('Product not found.', 'error');
        return;
    }

    document.title = `${escapeHTML(productName)} - Banana Shop`;
    document.getElementById('productName').textContent = escapeHTML(productName);
    document.getElementById('productDescription').textContent = escapeHTML(product.description);
    document.getElementById('productPrice').textContent = `$${product.price.toFixed(2)} each`;
    const productImage = document.getElementById('productImage');
    productImage.src = product.image.replace('.webp', '.jpg');
    productImage.alt = escapeHTML(productName);

    const addToCartButton = document.getElementById('addToCartButton');
    addToCartButton.addEventListener('click', handleAddToCart);

    loadCustomerReviews();
}

function getProductFromURL() {
    const path = window.location.pathname;
    const productFileName = path.substring(path.lastIndexOf('/') + 1);
    const productName = productFileName
        .replace('product-', '')
        .replace('.html', '')
        .split('-')
        .map(word => word.charAt(0).toUpperCase() + word.slice(1))
        .join(' ');
    return productName;
}

function updateCartCount() {
    const cartCount = document.getElementById('cart-count');
    if (cartCount) {
        cartCount.textContent = CartModule.getCartCount();
    }
}

function handleAddToCart() {
    const productName = getProductFromURL();
    const quantityInput = document.getElementById('quantity');
    let quantity = parseInt(quantityInput.value);
    if (isNaN(quantity) || quantity < 1 || quantity > 10) {
        showToast('Please enter a quantity between 1 and 10.', 'error');
        return;
    }
    CartModule.addToCart(productName, quantity);
    showToast(`${quantity} ${escapeHTML(productName)} added to cart.`, 'success');
    updateCartCount();
}

function loadCustomerReviews() {
    const reviews = JSON.parse(localStorage.getItem('reviews')) || {};
    const productName = getProductFromURL();
    const productReviews = reviews[productName] || [];
    const reviewsContainer = document.getElementById('customerReviews');
    if (reviewsContainer) {
        if (productReviews.length > 0) {
            let reviewsHTML = '';
            productReviews.forEach(review => {
                reviewsHTML += `<div class="review">
                    <p class="reviewer-name">${escapeHTML(review.name)}</p>
                    <p class="review-text">${escapeHTML(review.comment)}</p>
                </div>`;
            });
            reviewsContainer.innerHTML = reviewsHTML;
        } else {
            reviewsContainer.innerHTML = '<p>No reviews yet. Be the first to review this product!</p>';
        }
    }

    const reviewForm = document.getElementById('reviewForm');
    if (reviewForm) {
        reviewForm.addEventListener('submit', handleSubmitReview);
    }
}

function handleSubmitReview(event) {
    event.preventDefault();
    const name = document.getElementById('reviewerName').value.trim();
    const comment = document.getElementById('reviewText').value.trim();

    if (!name || !comment) {
        showToast('Please fill in all fields.', 'error');
        return;
    }

    const productName = getProductFromURL();
    const reviews = JSON.parse(localStorage.getItem('reviews')) || {};
    const productReviews = reviews[productName] || [];

    productReviews.push({ name, comment });
    reviews[productName] = productReviews;
    localStorage.setItem('reviews', JSON.stringify(reviews));

    showToast('Thank you for your review!', 'success');
    event.target.reset();
    loadCustomerReviews();
}
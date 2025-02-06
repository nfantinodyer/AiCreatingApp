import { showToast, escapeHTML } from './utils.js';
import { PRODUCTS } from './productsData.js';
import { CartModule } from './cart.js';

const ProductModule = (function() {
    let currentPage = 1;
    const itemsPerPage = 4;
    let filteredProducts = Object.keys(PRODUCTS);

    function loadProducts() {
        const productList = document.getElementById('product-list');
        const loadingSpinner = document.getElementById('loadingSpinner');
        loadingSpinner.style.display = 'block';
        productList.innerHTML = '';

        setTimeout(() => { // Simulate async data fetching
            const start = (currentPage - 1) * itemsPerPage;
            const end = start + itemsPerPage;
            const paginatedProducts = filteredProducts.slice(start, end);
            if (paginatedProducts.length === 0) {
                productList.innerHTML = '<p>No products found.</p>';
            } else {
                paginatedProducts.forEach(productName => {
                    const product = PRODUCTS[productName];
                    productList.innerHTML += `
                        <article class="product">
                            <figure>
                                <img src="${escapeHTML(product.image)}" alt="${escapeHTML(productName)} - ${escapeHTML(product.description)}" srcset="${escapeHTML(product.image.replace('.jpg', '-small.jpg'))} 600w, ${escapeHTML(product.image)} 1200w" sizes="(max-width: 600px) 600px, 1200px" loading="lazy">
                                <figcaption>${escapeHTML(product.description)}</figcaption>
                            </figure>
                            <h3>${escapeHTML(productName)}</h3>
                            <p>Price: $${product.price.toFixed(2)} each</p>
                            <p>In Stock</p>
                            <label for="quantity${escapeHTML(productName)}">Quantity:</label>
                            <input type="number" id="quantity${escapeHTML(productName)}" value="1" min="1" max="10" aria-label="Quantity for ${escapeHTML(productName)}">
                            <button class="btn add-to-cart" data-product="${escapeHTML(productName)}" aria-label="Add ${escapeHTML(productName)} to Cart">Add to Cart</button>
                        </article>`;
                });
            }
            loadingSpinner.style.display = 'none';
            attachProductEventListeners();
        }, 500);
    }

    function setupPagination() {
        const prevPageBtn = document.getElementById('prevPage');
        const nextPageBtn = document.getElementById('nextPage');
        const currentPageSpan = document.getElementById('currentPage');

        prevPageBtn.addEventListener('click', () => {
            if (currentPage > 1) {
                currentPage--;
                updateProducts();
            }
        });

        nextPageBtn.addEventListener('click', () => {
            if (currentPage < Math.ceil(filteredProducts.length / itemsPerPage)) {
                currentPage++;
                updateProducts();
            }
        });
    }

    function setupSearchFilter() {
        const searchInput = document.getElementById('searchInput');
        const filterSelect = document.getElementById('filterSelect');

        let debounceTimeout;
        searchInput.addEventListener('input', () => {
            clearTimeout(debounceTimeout);
            debounceTimeout = setTimeout(() => {
                applyFilters();
            }, 300);
        });

        filterSelect.addEventListener('change', () => {
            applyFilters();
        });
    }

    function applyFilters() {
        const searchTerm = document.getElementById('searchInput').value.trim().toLowerCase();
        const filterValue = document.getElementById('filterSelect').value;
        filteredProducts = Object.keys(PRODUCTS).filter(productName => {
            const matchesSearch = productName.toLowerCase().includes(searchTerm);
            const matchesFilter = filterValue === 'all' || productName.toLowerCase().includes(filterValue);
            return matchesSearch && matchesFilter;
        });
        currentPage = 1;
        updateProducts();
    }

    function updateProducts() {
        loadProducts();
        document.getElementById('currentPage').textContent = currentPage;
    }

    function attachProductEventListeners() {
        document.querySelectorAll('.add-to-cart').forEach(button => {
            button.addEventListener('click', () => {
                const productName = button.dataset.product;
                const quantityInput = document.getElementById(`quantity${productName}`);
                const quantity = parseInt(quantityInput.value);
                CartModule.addToCart(productName, quantity);
            });
        });
    }

    return {
        loadProducts,
        setupPagination,
        setupSearchFilter,
        updateProducts
    };
})();

document.addEventListener('DOMContentLoaded', () => {
    if (window.location.pathname.endsWith('products.html')) {
        ProductModule.setupSearchFilter();
        ProductModule.setupPagination();
        ProductModule.updateProducts();
        CartModule.displayCart();
    }
});

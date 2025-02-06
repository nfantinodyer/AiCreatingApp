let cart = [];

function addToCart(product, quantity) {
    if (quantity < 1 || quantity > 10) {
        alert('Please select a valid quantity.');
        return;
    }
    const cartItem = cart.find(item => item.product === product);
    if (cartItem) {
        cartItem.quantity += quantity;
    } else {
        cart.push({ product, quantity });
    }
    saveCart();
    displayCart();
    alert(`${product} has been added to your cart!`);
}

function displayCart() {
    const cartDiv = document.getElementById('cart') || document.getElementById('cartItems');
    const totalPriceDiv = document.getElementById('totalPrice');
    const checkoutButton = document.getElementById('checkoutButton');
    const emptyCartMessage = document.getElementById('emptyCartMessage');
    cartDiv.innerHTML = '';
    let totalPrice = 0;
    cart.forEach((item, index) => {
        cartDiv.innerHTML += `<p>${item.product} - Quantity: ${item.quantity} <button onclick="removeFromCart(${index})">Remove</button></p>`;
        if (item.product === 'Organic Bananas') totalPrice += item.quantity * 1.00;
        if (item.product === 'Golden Bananas') totalPrice += item.quantity * 0.80;
    });
    if (cart.length === 0) {
        checkoutButton.disabled = true;
        emptyCartMessage.style.display = 'block';
    } else {
        checkoutButton.disabled = false;
        emptyCartMessage.style.display = 'none';
    }
    totalPriceDiv.innerHTML = `<strong>Total Price: $${totalPrice.toFixed(2)}</strong>`;
}

function removeFromCart(index) {
    cart.splice(index, 1);
    saveCart();
    displayCart();
}

function proceedToCheckout() {
    if (cart.length === 0) {
        alert('Your cart is empty.');
        return;
    }
    window.location.href = 'checkout.html';
}

function saveCart() {
    try {
        localStorage.setItem('cart', JSON.stringify(cart));
    } catch (e) {
        console.error('Could not save cart', e);
    }
}

function loadCart() {
    const savedCart = localStorage.getItem('cart');
    if (savedCart) {
        cart = JSON.parse(savedCart);
        displayCart();
    }
}

window.onload = loadCart;

var contactForm = document.getElementById('contactForm');
if (contactForm) {
    contactForm.addEventListener('submit', function(event) {
        event.preventDefault();
        const emailPattern = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
        const namePattern = /^[a-zA-Z ]+$/;
        if (!emailPattern.test(this.email.value)) {
            alert('Please enter a valid email address.');
            return;
        }
        if (!namePattern.test(this.name.value)) {
            alert('Please enter a valid name without special characters.');
            return;
        }
        if (!this.name.value || !this.message.value || this.message.value.length < 10) {
            alert('Please fill in all fields and ensure the message is at least 10 characters long.');
            return;
        }
        alert('Thank you for contacting us!');
        this.reset();
    });
}
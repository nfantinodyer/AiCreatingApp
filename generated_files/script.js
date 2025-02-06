function addToCart(product) {
    alert(product + ' has been added to your cart!');
}

document.getElementById('contact-form').addEventListener('submit', function(event) {
    event.preventDefault();
    alert('Your message has been sent!');
    this.reset();
});
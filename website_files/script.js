function addToCart(product) {
    alert(product + ' has been added to your cart!');
}

var contactForm = document.getElementById('contactForm');
if (contactForm) {
    contactForm.addEventListener('submit', function(event) {
        event.preventDefault();
        alert('Thank you for contacting us!');
        this.reset();
    });
}
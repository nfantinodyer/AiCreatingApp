import { showToast, escapeHTML } from './utils.js';

export const ContactModule = (function() {
    function validateContactForm(event) {
        event.preventDefault();
        const name = document.getElementById('contactName').value.trim();
        const email = document.getElementById('contactEmail').value.trim();
        const message = document.getElementById('contactMessage').value.trim();

        if (!name || !email || !message) {
            showToast('Please fill in all required fields.', 'error');
            return;
        }

        const emailPattern = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
        if (!emailPattern.test(email)) {
            showToast('Please enter a valid email address.', 'error');
            return;
        }

        showToast('Thank you for contacting us!', 'success');
        document.getElementById('contactForm').reset();
    }

    return {
        validateContactForm
    };
})();

document.addEventListener('DOMContentLoaded', () => {
    const contactForm = document.getElementById('contactForm');
    if (contactForm) {
        contactForm.addEventListener('submit', ContactModule.validateContactForm);
    }
});
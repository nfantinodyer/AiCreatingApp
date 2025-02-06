import { showToast, escapeHTML } from './utils.js';

const ContactModule = (function() {
    const contactForm = document.getElementById('contactForm');
    if (contactForm) {
        contactForm.addEventListener('submit', validateContactForm);
    }

    function validateContactForm(event) {
        event.preventDefault();
        const form = event.target;
        const captchaResponse = grecaptcha.getResponse();
        if (captchaResponse.length === 0) {
            showToast('Please complete the CAPTCHA.', 'error');
            document.getElementById('captchaError').textContent = 'Please complete the CAPTCHA.';
            return;
        } else {
            document.getElementById('captchaError').textContent = '';
        }

        const emailPattern = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
        const namePattern = /^[a-zA-Z ]+$/;

        let valid = true;

        if (!namePattern.test(form.name.value)) {
            showToast('Please enter a valid name without special characters.', 'error');
            document.getElementById('nameError').textContent = 'Invalid name.';
            valid = false;
        } else {
            document.getElementById('nameError').textContent = '';
        }

        if (!emailPattern.test(form.email.value)) {
            showToast('Please enter a valid email address.', 'error');
            document.getElementById('emailError').textContent = 'Invalid email.';
            valid = false;
        } else {
            document.getElementById('emailError').textContent = '';
        }

        if (!form.subject.value) {
            showToast('Please select a subject.', 'error');
            document.getElementById('subjectError').textContent = 'Subject is required.';
            valid = false;
        } else {
            document.getElementById('subjectError').textContent = '';
        }

        if (!form.message.value || form.message.value.length < 10) {
            showToast('Please fill in all fields and ensure the message is at least 10 characters long.', 'error');
            document.getElementById('messageError').textContent = 'Message must be at least 10 characters.';
            valid = false;
        } else {
            document.getElementById('messageError').textContent = '';
        }

        if (valid) {
            // Here you would typically send the data to the server
            showToast('Thank you for contacting us!', 'success');
            form.reset();
            grecaptcha.reset();
        }
    }

    return {
        validateContactForm
    };
})();

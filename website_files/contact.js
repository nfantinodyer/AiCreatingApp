import { showToast, escapeHTML } from './utils.js';

document.addEventListener('DOMContentLoaded', () => {
    const contactForm = document.getElementById('contactForm');
    if (contactForm) {
        contactForm.addEventListener('submit', validateContactForm);
    }
});

function validateContactForm(event) {
    event.preventDefault();
    const form = event.target;
    if (typeof grecaptcha === 'undefined') {
        showToast('reCAPTCHA is not loaded. Please try again later.', 'error');
        return;
    }
    const captchaResponse = grecaptcha.getResponse();
    if (captchaResponse.length === 0) {
        showToast('Please complete the CAPTCHA.', 'error');
        document.getElementById('captchaError').textContent = 'Please complete the CAPTCHA.';
        return;
    } else {
        document.getElementById('captchaError').textContent = '';
    }

    const emailPattern = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
    const namePattern = /^[a-zA-Z ,.'-]+$/;

    let valid = true;

    if (!namePattern.test(form.name.value)) {
        showToast('Please enter a valid name without special characters.', 'error');
        document.getElementById('nameError').textContent = 'Invalid name.';
        form.name.setAttribute('aria-invalid', 'true');
        valid = false;
    } else {
        document.getElementById('nameError').textContent = '';
        form.name.removeAttribute('aria-invalid');
    }

    if (!emailPattern.test(form.email.value)) {
        showToast('Please enter a valid email address.', 'error');
        document.getElementById('emailError').textContent = 'Invalid email.';
        form.email.setAttribute('aria-invalid', 'true');
        valid = false;
    } else {
        document.getElementById('emailError').textContent = '';
        form.email.removeAttribute('aria-invalid');
    }

    if (!form.subject.value) {
        showToast('Please select a subject.', 'error');
        document.getElementById('subjectError').textContent = 'Subject is required.';
        valid = false;
    } else {
        document.getElementById('subjectError').textContent = '';
    }

    if (!form.message.value || form.message.value.length < 10) {
        showToast('Please ensure the message is at least 10 characters long.', 'error');
        document.getElementById('messageError').textContent = 'Message must be at least 10 characters.';
        form.message.setAttribute('aria-invalid', 'true');
        valid = false;
    } else {
        document.getElementById('messageError').textContent = '';
        form.message.removeAttribute('aria-invalid');
    }

    if (valid) {
        const csrfToken = form.elements['csrf_token'].value;
        // Send data to server-side endpoint
        fetch('/submit-contact', {
            method: 'POST',
            headers: { 
                'Content-Type': 'application/json',
                'X-CSRF-Token': csrfToken
            },
            body: JSON.stringify({
                subject: form.subject.value,
                name: form.name.value,
                email: form.email.value,
                message: form.message.value,
                recaptcha: captchaResponse
            })
        })
        .then(response => {
            if (response.ok) {
                showToast('Thank you for contacting us!', 'success');
                form.reset();
                grecaptcha.reset();
            } else {
                return response.json().then(errorData => {
                    throw new Error(errorData.message || 'Failed to submit the form.');
                });
            }
        })
        .catch(error => {
            console.error(error);
            showToast('An error occurred. Please try again later.', 'error');
        });
    }
}
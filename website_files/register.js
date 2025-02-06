import { showToast } from './utils.js';

document.addEventListener('DOMContentLoaded', () => {
    const registerForm = document.getElementById('registerForm');
    if (registerForm) {
        registerForm.addEventListener('submit', handleRegister);
    }
});

function handleRegister(event) {
    event.preventDefault();

    const email = document.getElementById('email').value.trim();
    const password = document.getElementById('password').value.trim();

    if (!email || !password) {
        showToast('Please enter your email and password.', 'error');
        return;
    }

    const emailPattern = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
    if (!emailPattern.test(email)) {
        showToast('Please enter a valid email address.', 'error');
        return;
    }

    localStorage.setItem('userEmail', email);
    localStorage.setItem('password', password);
    localStorage.setItem('userName', email);
    localStorage.setItem('isLoggedIn', 'true');
    showToast('Registration successful!', 'success');
    setTimeout(() => {
        window.location.href = 'account.html';
    }, 1000);
}
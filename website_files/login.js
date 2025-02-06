import { showToast } from './utils.js';

document.addEventListener('DOMContentLoaded', () => {
    const loginForm = document.getElementById('loginForm');
    if (loginForm) {
        loginForm.addEventListener('submit', handleLogin);
    }
});

function handleLogin(event) {
    event.preventDefault();

    const email = document.getElementById('email').value.trim();
    const password = document.getElementById('password').value.trim();

    if (!email || !password) {
        showToast('Please enter your email and password.', 'error');
        return;
    }

    let storedEmail = localStorage.getItem('userEmail');
    let storedPassword = localStorage.getItem('password');

    if (!storedEmail || !storedPassword) {
        localStorage.setItem('userEmail', email);
        localStorage.setItem('password', password);
        localStorage.setItem('userName', email);
        localStorage.setItem('isLoggedIn', 'true');
        showToast('Registration successful!', 'success');
        setTimeout(() => {
            window.location.href = 'account.html';
        }, 1000);
    } else {
        if (email === storedEmail && password === storedPassword) {
            localStorage.setItem('isLoggedIn', 'true');
            showToast('Login successful!', 'success');
            setTimeout(() => {
                window.location.href = 'account.html';
            }, 1000);
        } else {
            showToast('Invalid email or password.', 'error');
        }
    }
}
import { showToast, escapeHTML } from './utils.js';

document.addEventListener('DOMContentLoaded', () => {
    updateNavigationMenu();
    updateUserGreeting();
});

function updateNavigationMenu() {
    const navMenu = document.getElementById('nav-menu');
    if (!navMenu) return;

    navMenu.innerHTML = '';

    const isLoggedIn = localStorage.getItem('isLoggedIn') === 'true';

    const menuItems = [
        { text: 'Home', href: 'index.html' },
        { text: 'Products', href: 'products.html' },
        { text: 'Contact', href: 'contact.html' },
        { text: 'Cart', href: 'cart.html' },
        { text: isLoggedIn ? 'My Account' : 'Login', href: isLoggedIn ? 'account.html' : 'login.html' }
    ];

    menuItems.forEach(item => {
        const li = document.createElement('li');
        const a = document.createElement('a');
        a.textContent = item.text;
        a.href = item.href;
        a.setAttribute('aria-label', item.text);
        li.appendChild(a);
        navMenu.appendChild(li);
    });
}

function updateUserGreeting() {
    const isLoggedIn = localStorage.getItem('isLoggedIn') === 'true';
    const userGreeting = document.getElementById('userGreeting');
    if (userGreeting) {
        if (isLoggedIn) {
            const userName = localStorage.getItem('userName') || 'User';
            userGreeting.textContent = `Welcome, ${escapeHTML(userName)}`;
        } else {
            userGreeting.textContent = '';
        }
    }
}
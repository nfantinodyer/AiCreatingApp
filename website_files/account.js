import { showToast, escapeHTML } from './utils.js';

document.addEventListener('DOMContentLoaded', () => {
    const isLoggedIn = localStorage.getItem('isLoggedIn');
    if (isLoggedIn !== 'true') {
        window.location.href = 'login.html';
    } else {
        const userName = localStorage.getItem('userName') || 'User';
        document.getElementById('userName').textContent = escapeHTML(userName);

        const fullNameInput = document.getElementById('fullName');
        const emailInput = document.getElementById('email');
        fullNameInput.value = localStorage.getItem('fullName') || '';
        emailInput.value = localStorage.getItem('email') || '';

        const accountDetailsForm = document.getElementById('accountDetailsForm');
        accountDetailsForm.addEventListener('submit', (event) => {
            event.preventDefault();
            const fullName = fullNameInput.value.trim();
            const email = emailInput.value.trim();
            if (fullName && email) {
                localStorage.setItem('fullName', fullName);
                localStorage.setItem('email', email);
                showToast('Account details updated successfully.', 'success');
            } else {
                showToast('Please fill in all required fields.', 'error');
            }
        });

        const changePasswordForm = document.getElementById('changePasswordForm');
        changePasswordForm.addEventListener('submit', (event) => {
            event.preventDefault();
            const currentPassword = document.getElementById('currentPassword').value;
            const newPassword = document.getElementById('newPassword').value;
            const confirmNewPassword = document.getElementById('confirmNewPassword').value;
            const storedPassword = localStorage.getItem('password') || '';
            if (currentPassword !== storedPassword) {
                showToast('Current password is incorrect.', 'error');
                return;
            }
            if (newPassword !== confirmNewPassword) {
                showToast('New passwords do not match.', 'error');
                return;
            }
            localStorage.setItem('password', newPassword);
            showToast('Password changed successfully.', 'success');
            changePasswordForm.reset();
        });

        const orderHistoryList = document.getElementById('orderHistoryList');
        const orderHistory = JSON.parse(localStorage.getItem('orderHistory')) || [];
        if (orderHistory.length > 0) {
            let ordersHTML = '<ul>';
            orderHistory.forEach(order => {
                ordersHTML += `<li>Order #${order.orderNumber} - ${order.date} - Total: $${order.total.toFixed(2)}</li>`;
            });
            ordersHTML += '</ul>';
            orderHistoryList.innerHTML = ordersHTML;
        } else {
            orderHistoryList.innerHTML = '<p>You have no order history.</p>';
        }

        const logoutButton = document.getElementById('logoutButton');
        logoutButton.addEventListener('click', () => {
            localStorage.removeItem('isLoggedIn');
            localStorage.removeItem('userName');
            localStorage.removeItem('fullName');
            localStorage.removeItem('email');
            localStorage.removeItem('password');
            showToast('You have been logged out.', 'info');
            setTimeout(() => {
                window.location.href = 'index.html';
            }, 1000);
        });
    }
});
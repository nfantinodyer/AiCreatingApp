export function showToast(message, type = 'info') {
    const toast = document.getElementById('toast');
    if (!toast) return;
    toast.textContent = message;
    toast.className = `toast ${type} show`;
    if (type === 'success') {
        toast.setAttribute('role', 'status');
    } else {
        toast.setAttribute('role', 'alert');
    }
    setTimeout(() => {
        toast.classList.remove('show');
    }, parseInt(getComputedStyle(document.documentElement).getPropertyValue('--toast-duration')) || 5000);
}

export function escapeHTML(str) {
    const replacements = { '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#039;' };
    return str.replace(/[&<>"']/g, match => replacements[match]);
}
export function showToast(message, type = 'info') {
    const toast = document.getElementById('toast');
    if (!toast) return;
    toast.textContent = message;
    toast.className = `toast show ${type}`;
    if (type === 'success') {
        toast.setAttribute('role', 'status');
    } else {
        toast.setAttribute('role', 'alert');
    }
    setTimeout(() => {
        toast.className = toast.className.replace('show', '');
    }, 5000);
}

export function escapeHTML(str) {
    const div = document.createElement('div');
    div.appendChild(document.createTextNode(str));
    return div.innerHTML;
}

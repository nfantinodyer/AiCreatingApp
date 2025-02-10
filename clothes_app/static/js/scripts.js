function searchImages() {
    const queryInput = document.getElementById('image-query');
    const sourceInput = document.getElementById('image-source');
    if (!queryInput || !sourceInput) {
        console.error('Search elements not found.');
        return;
    }
    const query = queryInput.value;
    const source = sourceInput.value;
    if (!query) {
        alert('Please enter a search query.');
        return;
    }
    fetch(`/search_images?query=${encodeURIComponent(query)}&source=${encodeURIComponent(source)}`)
        .then(response => response.json())
        .then(data => {
            const resultsDiv = document.getElementById('image-results');
            resultsDiv.innerHTML = '';
            if (data.results.length === 0) {
                resultsDiv.innerHTML = '<p>No images found.</p>';
                return;
            }
            data.results.forEach(url => {
                const img = document.createElement('img');
                img.src = url;
                img.alt = 'Search Image';
                img.className = 'pinterest-image';
                resultsDiv.appendChild(img);
            });
        })
        .catch(error => {
            console.error('Error fetching images:', error);
        });
}

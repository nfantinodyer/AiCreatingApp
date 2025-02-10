function searchImages() {
    const queryInput = document.getElementById('image-query');
    const sourceInput = document.getElementById('image-source');
    if (!queryInput || !sourceInput) {
        console.error('Search elements not found.');
        alert('Search elements not found.');
        return;
    }
    const query = queryInput.value.trim();
    const source = sourceInput.value;
    if (!query) {
        alert('Please enter a search query.');
        return;
    }

    const resultsDiv = document.getElementById('image-results');
    resultsDiv.innerHTML = 'Loading...';

    fetch(`/api/search_images?query=${encodeURIComponent(query)}&source=${encodeURIComponent(source)}`)
        .then(response => response.json())
        .then(data => {
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
            resultsDiv.innerHTML = '<p>An error occurred while fetching images.</p>';
            alert('An error occurred while fetching images.');
        });
}

function confirmRemoval(formId) {
    if (confirm("Are you sure you want to remove this image? This action cannot be undone.")) {
        document.getElementById(formId).submit();
    }
}

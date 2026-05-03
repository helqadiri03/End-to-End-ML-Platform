document.addEventListener('DOMContentLoaded', function() {
    const uploadForm = document.getElementById('uploadForm');
    const fileInput = document.getElementById('fileInput');
    const loadingSpinner = document.getElementById('loadingSpinner');

    fileInput.addEventListener('change', function() {
        if (fileInput.files.length > 0) {
            const file = fileInput.files[0];
            
            // Check file size before uploading (100MB limit)
            if (file.size > 100 * 1024 * 1024) {
                alert('File is too large. Maximum size is 100MB');
                return;
            }

            const formData = new FormData();
            formData.append('file', file);

            // Show loading spinner
            loadingSpinner.style.display = 'block';

            fetch('/upload', {
                method: 'POST',
                body: formData
            })
            .then(response => {
                if (!response.ok) {
                    return response.json().then(data => {
                        throw new Error(data.error || 'Upload failed');
                    });
                }
                return response.json();
            })
            .then(data => {
                if (data.error) {
                    throw new Error(data.error);
                }
                window.location.href = '/visualization?file_id=' + data.file_id;
            })
            .catch(error => {
                console.error('Error:', error);
                loadingSpinner.style.display = 'none';
                alert('Error: ' + error.message);
            });
        }
    });
});

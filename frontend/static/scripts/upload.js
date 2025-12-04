// frontend/static/scripts/upload.js

document.addEventListener('DOMContentLoaded', () => {
    // --- CSV Upload Elements ---
    const csvDropZone = document.getElementById('csv-drop-zone');
    const csvFileInput = document.getElementById('csv-file-input');
    const csvUploadForm = document.getElementById('csv-upload-form');
    const csvStatus = document.getElementById('csv-status');

    // Helper function to update the status message
    const updateStatus = (message, isError = false) => {
        csvStatus.textContent = message;
        // Use accent color for errors, secondary text color for normal messages
        csvStatus.style.color = isError ? 'var(--accent-clr)' : 'var(--secondary-text-clr)'; 
    };
    
    // 1. Drop Zone Click Handler
    // Clicking the drop zone opens the native file dialog
    csvDropZone.addEventListener('click', () => {
        csvFileInput.click();
    });

    // 2. File Input Change Handler (shows selected file name)
    csvFileInput.addEventListener('change', () => {
        if (csvFileInput.files.length > 0) {
            updateStatus(`File selected: ${csvFileInput.files[0].name}`, false);
        }
    });

    // --- 3. Drag and Drop Visual Handlers ---

    // Prevent default browser behavior for all drag events
    ['dragenter', 'dragover', 'dragleave', 'drop'].forEach(eventName => {
        csvDropZone.addEventListener(eventName, preventDefaults, false);
    });

    function preventDefaults(e) {
        e.preventDefault();
        e.stopPropagation();
    }

    // Add visual feedback (the 'dragover' class you styled in CSS)
    ['dragenter', 'dragover'].forEach(eventName => {
        csvDropZone.addEventListener(eventName, () => csvDropZone.classList.add('dragover'), false);
    });

    // Remove visual feedback
    ['dragleave', 'drop'].forEach(eventName => {
        csvDropZone.addEventListener(eventName, () => csvDropZone.classList.remove('dragover'), false);
    });

    // 4. Drop Event Handler (handles file drop)
    csvDropZone.addEventListener('drop', (e) => {
        const dt = e.dataTransfer;
        // Assign the dropped files to the file input element
        csvFileInput.files = dt.files; 
        if (csvFileInput.files.length > 0) {
            updateStatus(`File dropped: ${csvFileInput.files[0].name}`, false);
        }
    }, false);

    // --- 5. Form Submission Handler (The AJAX POST Request) ---
    csvUploadForm.addEventListener('submit', async (e) => {
        e.preventDefault();
        
        if (csvFileInput.files.length === 0) {
            updateStatus('Please select a CSV file first.', true);
            return;
        }

        const fileToUpload = csvFileInput.files[0];
        // Use FormData to correctly package the file for a multipart/form-data POST request
        const formData = new FormData();
        // The key 'file' must match what Flask's request.files['file'] expects in routes.py
        formData.append('file', fileToUpload); 

        updateStatus(`Uploading ${fileToUpload.name}...`, false);
        
        try {
            const response = await fetch('/api/v1/upload', {
                method: 'POST',
                body: formData,
            });

            const result = await response.json();

            if (response.ok && result.status === 'completed') {
                updateStatus(
                    `Upload successful: ${result.success_count} rows inserted. ` +
                    `${result.fail_count} rows failed.`, 
                    result.fail_count > 0 
                );
                // Optionally clear the file input after success
                csvFileInput.value = '';
                
                if (result.errors && result.errors.length > 0) {
                     console.error("CSV Upload Errors:", result.errors);
                }
            } else {
                // Handle API errors (e.g., file not found, processing failed)
                updateStatus(`Upload failed: ${result.message || 'Unknown error occurred.'}`, true);
                console.error("Upload failed details:", result);
            }
        } catch (error) {
            // Handle network/fetch error
            updateStatus(`A network or server error occurred: ${error.message}`, true);
            console.error("Fetch error:", error);
        }
    });
});
document.addEventListener('DOMContentLoaded', () => {
    
    // --- Reusable Setup Function ---
    const setupUploadBox = (config) => {
        const { dropZone, fileInput, form, statusElement, endpoint, fileTypeLabel } = config;

        // Helper to update status for THIS specific box
        const updateStatus = (message, isError = false) => {
            statusElement.textContent = message;
            statusElement.style.color = isError ? 'var(--accent-clr)' : 'var(--secondary-text-clr)';
        };

        // 1. Click Handler
        dropZone.addEventListener('click', () => fileInput.click());

        // 2. Selection Feedback
        fileInput.addEventListener('change', () => {
            if (fileInput.files.length > 0) {
                updateStatus(`${fileTypeLabel} selected: ${fileInput.files[0].name}`, false);
            }
        });

        // 3. Drag and Drop Visuals
        const preventDefaults = (e) => {
            e.preventDefault();
            e.stopPropagation();
        };

        ['dragenter', 'dragover', 'dragleave', 'drop'].forEach(name => {
            dropZone.addEventListener(name, preventDefaults, false);
        });

        ['dragenter', 'dragover'].forEach(name => {
            dropZone.addEventListener(name, () => dropZone.classList.add('dragover'), false);
        });

        ['dragleave', 'drop'].forEach(name => {
            dropZone.addEventListener(name, () => dropZone.classList.remove('dragover'), false);
        });

        // 4. Drop Handler
        dropZone.addEventListener('drop', (e) => {
            const dt = e.dataTransfer;
            fileInput.files = dt.files;
            if (fileInput.files.length > 0) {
                updateStatus(`${fileTypeLabel} dropped: ${fileInput.files[0].name}`, false);
            }
        }, false);

        // 5. Form Submission
        form.addEventListener('submit', async (e) => {
            e.preventDefault();

            if (fileInput.files.length === 0) {
                updateStatus(`Please select a ${fileTypeLabel} file first.`, true);
                return;
            }

            const fileToUpload = fileInput.files[0];
            const formData = new FormData();
            formData.append('file', fileToUpload);

            updateStatus(`Uploading ${fileToUpload.name}...`, false);

            try {
                const response = await fetch(endpoint, {
                    method: 'POST',
                    body: formData,
                });

                const result = await response.json();

                if (response.ok) {
                    // Custom success message based on file type
                    const successMsg = result.audio_id 
                        ? `Audio synced successfully! ID: ${result.audio_id}`
                        : `Upload successful: ${result.success_count} rows inserted.`;
                    
                    updateStatus(successMsg, false);
                    fileInput.value = ''; // Clear input
                } else {
                    updateStatus(`Upload failed: ${result.error || result.message || 'Unknown error'}`, true);
                }
            } catch (error) {
                updateStatus(`Network error: ${error.message}`, true);
            }
        });
    };

    // --- Initialize CSV Upload ---
    setupUploadBox({
        dropZone: document.getElementById('csv-drop-zone'),
        fileInput: document.getElementById('csv-file-input'),
        form: document.getElementById('csv-upload-form'),
        statusElement: document.getElementById('csv-status'),
        endpoint: '/api/v1/upload',
        fileTypeLabel: 'CSV'
    });

    // --- Initialize Audio Upload ---
    setupUploadBox({
        dropZone: document.getElementById('audio-drop-zone'),
        fileInput: document.getElementById('audio-file-input'),
        form: document.getElementById('audio-upload-form'),
        statusElement: document.getElementById('audio-status'),
        endpoint: '/api/v1/audio/upload',
        fileTypeLabel: 'Audio'
    });

});
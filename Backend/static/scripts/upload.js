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
            const count = fileInput.files.length;
            if (count > 0) {
                const msg = count === 1 ? fileInput.files[0].name : `${count} files selected`;
                updateStatus(`${fileTypeLabel}: ${msg}`, false);
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
            const count = fileInput.files.length;
            if (count > 0) {
                const msg = count === 1 ? fileInput.files[0].name : `${count} files dropped`;
                updateStatus(`${fileTypeLabel}: ${msg}`, false);
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
            // Loop through all selected files
                for (let i = 0; i < fileInput.files.length; i++) {
                    // Use 'files[]' as the key so Flask can recognize it as a list
                    formData.append('files[]', fileInput.files[i]);
                }

            updateStatus(`Uploading ${fileInput.files.length} ${fileTypeLabel} files...`, false);

            try {
                const response = await fetch(endpoint, {
                    method: 'POST',
                    body: formData,
                });

                const result = await response.json();

            if (response.ok) {
                let successMsg = "";
                if (result.audio_count !== undefined) {
                    successMsg = `Successfully synced ${result.audio_count} audio files!`;
                } 
                else if (result.audio_id) {
                    successMsg = `Audio synced successfully! ID: ${result.audio_id}`;
                }
                else if (result.success_count !== undefined) {
                    successMsg = `Upload successful: ${result.success_count} rows inserted.`;
                } 
                else {
                    successMsg = "Upload successful!";
                }

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
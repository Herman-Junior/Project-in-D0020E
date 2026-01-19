// static/scripts/audio.js

document.addEventListener('DOMContentLoaded', () => {
    loadAudioList();
});

async function loadAudioList() {
    const container = document.getElementById('audio-list-viewport');
    
    try {
        const response = await fetch('/api/v1/audio/list');
        const recordings = await response.json();

        if (!recordings || recordings.length === 0) {
            container.innerHTML = '<div class="container upload-box"><p>No audio recordings found.</p></div>';
            return;
        }

        // Map through recordings to create boxes that look exactly like your "Upload" boxes
        container.innerHTML = recordings.map(record => `
            <div class="container upload-box audio-item" data-audio-id="${record.id}" data-filename="${record.filename}">
                <div style="display: flex; justify-content: space-between; align-items: center;">
                    <div>
                        <h3 style="margin: 0; color: var(--primary-text-clr);">${record.filename}</h3>
                        <small style="color: var(--secondary-text-clr);">${record.date} at ${record.start_time}</small>
                    </div>
                    <span class="info-tag">Click to Correlate</span>
                </div>
            </div>
        `).join('');

        // Attach clicks after rendering
        setupClickHandlers();

    } catch (error) {
        container.innerHTML = `<p class="error">Error loading audio: ${error.message}</p>`;
    }
}
document.addEventListener('DOMContentLoaded', () => {
    // --- ELEMENTS ---
    const content = document.getElementById('correlation-content');
    const title = document.getElementById('selected-audio-title');
    const deleteButton = document.getElementById('delete-selected-btn');
    const loadAudioBtn = document.getElementById('load-audio-btn');
    const resultsContainer = document.getElementById('audio-results-container');
    const bulkContainer = document.getElementById('bulk-actions-container');
    const selectedCountSpan = document.getElementById('selected-count');

    // --- 1. INITIALIZATION ---
    
    // Attach delete logic
    if (deleteButton) {
        deleteButton.addEventListener('click', deleteSelected);
    }

    // Attach Load/Filter logic
    if (loadAudioBtn) {
        loadAudioBtn.addEventListener('click', fetchFilteredAudio);
    }

    // Run once on page load to bind existing items (rendered by Jinja)
    attachItemListeners();

    // --- 2. FILTERING LOGIC ---

    async function fetchFilteredAudio() {
        // Gather values from the inputs
        const params = new URLSearchParams({
            start_date: document.getElementById('start-date').value,
            end_date: document.getElementById('end-date').value,
            start_time: document.getElementById('start-time').value,
            end_time: document.getElementById('end-time').value
        });

        resultsContainer.innerHTML = '<p class="status-message info">Loading recordings...</p>';
        if (bulkContainer) bulkContainer.style.display = 'none';

        try {
            // Note: Update this URL to match your Flask route (e.g., /api/v1/audio)
            const response = await fetch(`/api/v1/audio?${params.toString()}`);
            if (!response.ok) throw new Error("Failed to fetch data");
            
            const recordings = await response.json();
            
            renderAudioList(recordings);
        } catch (error) {
            resultsContainer.innerHTML = `<p class="status-message error">Error: ${error.message}</p>`;
        }
    }

    function renderAudioList(recordings) {
        if (recordings.length === 0) {
            resultsContainer.innerHTML = '<div class="container upload-box"><p class="status-message">No recordings found.</p></div>';
            return;
        }

        // Rebuild the HTML list
        resultsContainer.innerHTML = recordings.map(record => `
            <div class="container upload-box audio-item" 
                data-audio-id="${record.id}" 
                data-filename="${record.filename}"
                style="display: flex !important; flex-direction: row !important; align-items: center !important; gap: 20px; cursor: pointer; padding: 20px;">

                <div class="checkbox-container" style="display: flex; align-items: center;">
                    <input type="checkbox" class="delete-checkbox" data-id="${record.id}" 
                        style="width: 20px; height: 20px; cursor: pointer;">
                </div>
                
                <div style="text-align: left; flex-grow: 1">
                    <h2 style="margin: 0;">${record.filename}</h2>
                    <p style="color: var(--secondary-text-clr); margin-top: 5px;">
                        ${record.date} | ${record.start_time}
                    </p>
                </div>
            </div>
        `).join('');

        // IMPORTANT: Re-bind events to the new HTML elements
        attachItemListeners();
    }

    // --- 3. EVENT BINDING ---

    function attachItemListeners() {
        // Navigation to details
        const audioItems = document.querySelectorAll('.audio-item');
        audioItems.forEach(item => {
            item.onclick = () => {
                const audioId = item.getAttribute('data-audio-id');
                const filename = item.getAttribute('data-filename');
                window.location.href = `/audio/details?id=${audioId}&name=${encodeURIComponent(filename)}`;
            };
        });

        // Checkbox Logic
        const checkboxes = document.querySelectorAll('.delete-checkbox');
        checkboxes.forEach(cb => {
            // Prevent row click when clicking checkbox
            cb.onclick = (e) => e.stopPropagation();

            // Handle bulk action visibility
            cb.onchange = () => {
                const checkedCount = document.querySelectorAll('.delete-checkbox:checked').length;
                if (checkedCount > 0) {
                    if (bulkContainer) bulkContainer.style.display = 'flex';
                    if (selectedCountSpan) selectedCountSpan.textContent = checkedCount;
                } else {
                    if (bulkContainer) bulkContainer.style.display = 'none';
                }
            };
        });
    }

    // --- 4. DETAILS PAGE LOGIC ---
    const urlParams = new URLSearchParams(window.location.search);
    const idFromUrl = urlParams.get('id');
    const nameFromUrl = urlParams.get('name');

    if (idFromUrl && content) {
        loadDetailData(idFromUrl, nameFromUrl);
    }

    async function loadDetailData(audioId, filename) {
        if (title) title.innerText = filename;
        content.innerHTML = '<p class="status-message info">Fetching environmental data...</p>';

        try {
            const response = await fetch(`/api/v1/audio/environmental?audio_id=${audioId}`);
            if (!response.ok) throw new Error(`Status: ${response.status}`);
            const data = await response.json();
            renderData(data); 
        } catch (error) {
            content.innerHTML = `<p class="status-message error">Error: ${error.message}</p>`;
        }
    }

    // --- 5. DELETE ACTION ---
    async function deleteSelected() {
        const selectedCheckboxes = document.querySelectorAll('.delete-checkbox:checked');
        const selectedIds = Array.from(selectedCheckboxes).map(cb => cb.getAttribute('data-id'));

        if (selectedIds.length === 0) {
            alert('No rows selected for deletion.');
            return;
        }

        if (confirm("Are you sure about deleting the selected rows?")) {
            try {
                const response = await fetch('/api/v1/delete', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ ids: selectedIds, type: 'audio' })
                });

                if (response.ok) {
                    alert('Selected rows deleted successfully.');
                    location.reload(); 
                } else {
                    alert("Something went wrong during deletion.");
                }
            } catch (e) {
                alert("Network error: " + e.message);
            }
        }
    }

    // --- 6. RENDER TABLES ---
    function renderData(data) {
        let html = '';

        if (!data.sensor_data?.length && !data.weather_data?.length) {
            content.innerHTML = '<p class="status-message info">No correlated data found.</p>';
            return;
        }

        if (data.sensor_data?.length > 0) {
            html += '<h2 class="section-title">Correlated Sensor Data</h2>';
            html += '<div class="table-container"><table class="data-table"><thead><tr><th>Date</th><th>Time</th><th>Moisture</th></tr></thead><tbody>';
            data.sensor_data.forEach(s => {
                const [date, time] = s.timestamp.split(' ');
                html += `<tr><td>${date}</td><td>${time}</td><td>${s.moisture}%</td></tr>`;
            });
            html += '</tbody></table></div>'; 
        }

        if (data.weather_data?.length > 0) {
            html += '<h2 class="section-title">Correlated Weather Data</h2>';
            html += '<div class="table-container"><table class="data-table"><thead><tr><th>Date</th><th>Time</th><th>Daily Rain</th><th>In Hum</th><th>In Temp</th><th>Out Hum</th><th>Out Temp</th><th>Rain Rate</th><th>Wind Dir</th><th>Wind Speed</th></tr></thead><tbody>';
            data.weather_data.forEach(w => {
                const [date, time] = w.timestamp.split(' ');
                html += `<tr>
                    <td>${date}</td><td>${time}</td>
                    <td>${w.daily_rain || 0} mm</td><td>${w.in_humidity || 0}%</td>
                    <td>${w.in_temperature || 0}°C</td><td>${w.out_humidity || 0}%</td>
                    <td>${w.out_temperature || 0}°C</td><td>${w.rain_rate || 0} mm/h</td>
                    <td>${w.wind_direction || 'N/A'}</td><td>${w.wind_speed || 0} m/s</td>
                </tr>`;
            });
            html += '</tbody></table></div>'; 
        }
        content.innerHTML = html; 
    }
});
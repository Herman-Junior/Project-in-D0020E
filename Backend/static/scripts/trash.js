document.addEventListener('DOMContentLoaded', () => {
    const loadButton = document.getElementById('load-audio-btn'); // Matches your HTML ID
    
    // --- 1. FILTERING LOGIC ---
    if (loadButton) {
        loadButton.addEventListener('click', async () => {
            const params = new URLSearchParams({
                start_date: document.getElementById('start-date').value,
                end_date: document.getElementById('end-date').value,
                start_time: document.getElementById('start-time').value,
                end_time: document.getElementById('end-time').value
            });

            try {
                // Call the new API endpoint we discussed for routes.py
                const response = await fetch(`/api/v1/trash/filter?${params.toString()}`);
                const data = await response.json();

                // Clear and Rebuild the three lists
                renderTrashList('audio-trash-list', data.audio, 'audio');
                renderTrashList('sensor-trash-list', data.sensors, 'sensor');
                renderTrashList('weather-trash-list', data.weather, 'weather');

                // Force immediate timer update for new elements
                updateTimers(); 
            } catch (e) {
                console.error("Failed to filter trash:", e);
                alert("Error loading filtered data.");
            }
        });
    }

    // --- 2. RESTORE LOGIC ---
    // We attach this to the window so the 'onclick' in the HTML can find it
    window.restoreItems = async function(ids, type) {
        if (!confirm(`Restore these ${type} items?`)) return;

        try {
            const response = await fetch('/api/v1/restore', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ ids: ids, type: type })
            });

            if (response.ok) {
                // Instead of a full reload, we just click 'Load' again to refresh data
                loadButton.click(); 
            } else {
                alert("Error restoring data.");
            }
        } catch (e) {
            alert("Network error: " + e.message);
        }
    };

    // --- 3. DYNAMIC RENDERING ---
function renderTrashList(containerId, items, type) {
    const container = document.getElementById(containerId);
    if (!container) return;

    // Show a "No data" message if the list is empty
    if (!items || items.length === 0) {
        container.innerHTML = `<p style="color: #888; padding-left: 10px;">No deleted ${type} data found.</p>`;
        return;
    }

    container.innerHTML = items.map(item => {
        // 1. Get the correct ID for the restore button
        const itemId = item.id || item.sensor_id || item.weather_id;
        
        // 2. Format the timestamp: Change "2025-10-30T12:00:00" to "2025-10-30 12:00:00"
        let displayTime = item.timestamp ? item.timestamp.replace('T', ' ') : "No Date";

        // 3. Determine what text to show in the left column
        let infoText = "";
        if (type === 'audio') {
            infoText = item.filename || "Unknown Audio";
        } else if (type === 'sensor') {
            infoText = `${displayTime} - Moisture: ${item.moisture}%`;
        } else if (type === 'weather') {
            infoText = `${displayTime} - Temp: ${item.out_temperature}°C`;
        }

        // 4. Return the HTML row
        return `
            <div class="trash-item" style="display: flex; justify-content: space-between; align-items: center; padding: 15px 20px; border-bottom: 1px solid #444; width: 100%; box-sizing: border-box;">
                <span style="flex: 1; white-space: nowrap; overflow: hidden; text-overflow: ellipsis;">
                    ${infoText}
                </span>
                
                <span class="timer-display" data-deadline="${item.delete_at}" style="color: #ffca28; font-family: monospace; margin: 0 40px; min-width: 180px; text-align: center;">
                    Loading timer...
                </span>

                <button onclick="restoreItems(['${itemId}'], '${type}')" class="insert-btn" style="background: #28a745; width: 120px; flex-shrink: 0;">
                    Restore
                </button>
            </div>
        `;
    }).join('');
}

    // --- 4. TIMER LOGIC ---
    window.updateTimers = function() {
        const timerElements = document.querySelectorAll('.timer-display');

        timerElements.forEach(el => {
            const deadlineStr = el.getAttribute('data-deadline');
            if (!deadlineStr || deadlineStr === "None") {
                el.innerHTML = "No delete date";
                return;
            }

            const deadline = new Date(deadlineStr).getTime();
            const now = new Date().getTime();
            const diff = deadline - now;

            if (diff <= 0) {
                el.innerHTML = "Deleting soon...";
                return;
            }

            const days = Math.floor(diff / (1000 * 60 * 60 * 24));
            const hours = Math.floor((diff % (1000 * 60 * 60 * 24)) / (1000 * 60 * 60));
            const minutes = Math.floor((diff % (1000 * 60 * 60)) / (1000 * 60));
            const seconds = Math.floor((diff % (1000 * 60)) / 1000);

            el.innerHTML = `${days}d ${hours}h ${minutes}m ${seconds}s left`;
        });
    };

    // Initialize timers
    setInterval(updateTimers, 1000);
});
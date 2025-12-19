document.addEventListener('DOMContentLoaded', () => {
    // Select the panel where we will display the results
    const panel = document.getElementById('correlation-panel');
    const content = document.getElementById('correlation-content');
    const title = document.getElementById('selected-audio-title');

    // Attach click events to all audio items
    const audioItems = document.querySelectorAll('.audio-item');
    
    audioItems.forEach(item => {
        item.addEventListener('click', async () => {
            const audioId = item.getAttribute('data-audio-id');
            const filename = item.getAttribute('data-filename');

            // Show the panel and a loading state
            panel.style.display = 'block';
            title.innerText = `Correlated Data for: ${filename}`;
            content.innerHTML = '<p class="status-message info">Fetching environmental data...</p>';

            try {
                // CALLS EXISTING API: /api/v1/audio/environmental
                // This utilizes the get_audio_with_environmental_data route
                const response = await fetch(`/api/v1/audio/environmental?audio_id=${audioId}`);
                const data = await response.json();

                if (data && data.length > 0) {
                    // Create a simple list or table of the correlated sensor data
                    renderData(data, content);
                } else {
                    content.innerHTML = '<p class="status-message info">No matching environmental data found for this time period.</p>';
                }
                
                panel.scrollIntoView({ behavior: 'smooth' });
            } catch (error) {
                content.innerHTML = `<p class="status-message error">Error: ${error.message}</p>`;
            }
        });
    });

    function renderData(data, container) {
        // Displaying the sensor readings in a readable format
        let html = '<ul class="data-list">';
        data.forEach(entry => {
            html += `<li><strong>${entry.time}:</strong> Moisture: ${entry.moisture}%</li>`;
        });
        html += '</ul>';
        container.innerHTML = html;
    }
});
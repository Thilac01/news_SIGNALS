document.addEventListener('DOMContentLoaded', () => {
    fetchStats();
    fetchData();
    setupModalHandlers();
    setupMarketData(); // Initialize market data
    setupExportHandler(); // Initialize export feature
    updateClock();
    setupNotifications();
    setInterval(updateClock, 1000);

    // Refresh every 30 seconds
    setInterval(() => {
        fetchStats();
        fetchData();
        updateNotifications();
    }, 30000);

    // Modal Close Handler
    document.querySelector('.close-modal').addEventListener('click', () => {
        document.getElementById('detail-modal').style.display = 'none';
    });

    window.addEventListener('click', (event) => {
        const modal = document.getElementById('detail-modal');
        if (event.target === modal) {
            modal.style.display = 'none';
        }

        const notifDropdown = document.getElementById('notif-dropdown');
        const notifBtn = document.getElementById('notif-btn');
        if (notifDropdown && notifBtn && !notifDropdown.contains(event.target) && !notifBtn.contains(event.target)) {
            notifDropdown.classList.remove('show');
        }
    });

    const refreshBtn = document.getElementById('refresh-btn');
    if (refreshBtn) {
        refreshBtn.addEventListener('click', async () => {
            const icon = refreshBtn.querySelector('i');
            icon.classList.add('fa-spin');
            refreshBtn.disabled = true;
            refreshBtn.style.opacity = '0.7';

            try {
                const response = await fetch('/api/refresh', { method: 'POST' });
                const res = await response.json();
                if (res.status === 'success') {
                    setTimeout(() => {
                        fetchStats();
                        fetchData();
                        updateNotifications();
                        icon.classList.remove('fa-spin');
                        refreshBtn.disabled = false;
                        refreshBtn.style.opacity = '1';
                    }, 2000);
                } else {
                    alert('Refresh failed: ' + res.message);
                    icon.classList.remove('fa-spin');
                    refreshBtn.disabled = false;
                    refreshBtn.style.opacity = '1';
                }
            } catch (error) {
                console.error('Error refreshing:', error);
                icon.classList.remove('fa-spin');
                refreshBtn.disabled = false;
                refreshBtn.style.opacity = '1';
            }
        });
    }
});

function setupNotifications() {
    const notifBtn = document.getElementById('notif-btn');
    const notifDropdown = document.getElementById('notif-dropdown');

    if (notifBtn && notifDropdown) {
        notifBtn.addEventListener('click', (e) => {
            e.stopPropagation(); // Prevent immediate close
            notifDropdown.classList.toggle('show');
        });
        // Initial check
        updateNotifications();
    }
}

async function updateNotifications() {
    try {
        const response = await fetch('/api/data');
        const data = await response.json();

        // Filter for "High Risk" or "Major Event"
        const alerts = data.filter(item => item.impact_level === 'High Risk' || (item.event_flag && item.event_flag !== 'Normal' && item.event_flag !== 'nan'));

        const notifList = document.getElementById('notif-list');
        const notifDot = document.getElementById('notif-dot');

        if (notifList) {
            if (alerts.length === 0) {
                notifList.innerHTML = '<div style="padding: 20px; text-align: center; color: var(--text-muted); font-size: 0.8rem;">No new alerts</div>';
                if (notifDot) notifDot.style.display = 'none';
            } else {
                notifList.innerHTML = '';
                alerts.slice(0, 5).forEach(alert => {
                    const div = document.createElement('div');
                    div.className = 'notif-item';
                    div.innerHTML = `
                        <div class="notif-title">${alert.Title}</div>
                        <div class="notif-meta">
                            <span>${alert.Source}</span>
                            <span class="notif-badge">${alert.impact_level}</span>
                        </div>
                    `;
                    div.addEventListener('click', () => {
                        if (alert.Link) window.open(alert.Link, '_blank');
                    });
                    notifList.appendChild(div);
                });

                if (notifDot) {
                    notifDot.style.display = 'block';
                    notifDot.classList.add('pulse');
                }
            }
        }
    } catch (e) {
        console.error("Notifications update failed", e);
    }
}

function updateClock() {
    const now = new Date();
    const timeElem = document.getElementById('clock-time');
    const dateElem = document.getElementById('clock-date');

    if (timeElem && dateElem) {
        timeElem.textContent = now.toLocaleTimeString('en-US', {
            hour: 'numeric',
            minute: '2-digit',
            hour12: true
        });

        dateElem.textContent = now.toLocaleDateString('en-US', {
            weekday: 'long',
            month: 'short',
            day: 'numeric'
        });
    }
}

let currentData = [];

function setupExportHandler() {
    const exportBtn = document.getElementById('btn-export');
    if (!exportBtn) return;

    exportBtn.addEventListener('click', () => {
        if (!currentData || currentData.length === 0) {
            alert('No data available to export.');
            return;
        }

        // Convert JSON to CSV
        const headers = Object.keys(currentData[0]);
        const csvRows = [];

        // Add headers
        csvRows.push(headers.join(','));

        // Add values
        for (const row of currentData) {
            const values = headers.map(header => {
                const escaped = ('' + (row[header] || '')).replace(/"/g, '\\"');
                return `"${escaped}"`;
            });
            csvRows.push(values.join(','));
        }

        const csvString = csvRows.join('\n');
        const blob = new Blob([csvString], { type: 'text/csv' });
        const url = window.URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.setAttribute('hidden', '');
        a.setAttribute('href', url);
        a.setAttribute('download', `signal_monitor_export_${new Date().toISOString().slice(0, 10)}.csv`);
        document.body.appendChild(a);
        a.click();
        document.body.removeChild(a);
    });
}

async function fetchStats() {
    try {
        const response = await fetch('/api/stats');
        const data = await response.json();

        document.getElementById('stat-risk').textContent = data.high_risk;
        document.getElementById('stat-opportunity').textContent = data.opportunity;
        document.getElementById('stat-events').textContent = data.major_events;
        document.getElementById('stat-total').textContent = data.total_articles;
        if (data.last_updated) {
            document.getElementById('last-updated').textContent = 'Last Updated: ' + data.last_updated;
        }
    } catch (error) {
        console.error('Error fetching stats:', error);
    }
}

let impactChart = null;
let opsChart = null;

async function fetchData() {
    try {
        const response = await fetch('/api/data');
        const data = await response.json();
        currentData = data; // Store globally

        updateCharts(data);
        updateSignals(data);
    } catch (error) {
        console.error('Error fetching data:', error);
    }
}

function setupModalHandlers() {
    // National Activity Card
    const nationalCard = document.getElementById('list-national').closest('.card');
    nationalCard.addEventListener('click', () => openDetailModal('national'));

    // Operational Environment Card
    const operationalCard = document.getElementById('list-operational').closest('.card');
    operationalCard.addEventListener('click', () => openDetailModal('operational'));

    // Risk & Opportunity Card
    const riskCard = document.getElementById('list-risk').closest('.card');
    riskCard.addEventListener('click', () => openDetailModal('risk'));

    // Transport & Mobility Card
    const transportCard = document.getElementById('list-transport').closest('.card');
    transportCard.addEventListener('click', () => openDetailModal('transport'));

    // Weather & Hazards Card
    const weatherCard = document.getElementById('list-weather').closest('.card');
    weatherCard.addEventListener('click', () => openDetailModal('weather'));

    // Economic Indicators Card
    const economyCard = document.getElementById('list-economy').closest('.card');
    economyCard.addEventListener('click', () => openDetailModal('economy'));

    // Public Sentiment Card
    const sentimentCard = document.getElementById('list-sentiment').closest('.card');
    sentimentCard.addEventListener('click', () => openDetailModal('sentiment'));

    // Energy & Utilities Card
    const energyCard = document.getElementById('list-energy').closest('.card');
    energyCard.addEventListener('click', () => openDetailModal('energy'));
}

function openDetailModal(type) {
    const modal = document.getElementById('detail-modal');
    const title = document.getElementById('modal-title');
    const body = document.getElementById('modal-body');

    modal.style.display = 'block';
    body.innerHTML = '';

    let items = [];

    if (type === 'national') {
        title.textContent = 'National Activity Indicators';
        items = currentData.filter(d => d.event_flag && d.event_flag !== 'Normal' && d.event_flag !== 'nan');
        // Group by Event Flag
        renderGroupedItems(body, items, 'event_flag');
    } else if (type === 'operational') {
        title.textContent = 'Operational Environment Indicators';
        items = currentData.filter(d => d.operational_tag && d.operational_tag !== 'general');
        // Group by Operational Tag
        renderGroupedItems(body, items, 'operational_tag');
    } else if (type === 'risk') {
        title.textContent = 'Risk & Opportunity Insights';
        items = currentData.filter(d => {
            const imp = (d.impact_level || '').toLowerCase();
            return imp.includes('risk') || imp.includes('opportunity');
        });
        // Group by Impact Level
        renderGroupedItems(body, items, 'impact_level');
    } else if (type === 'transport') {
        title.textContent = 'Transport & Mobility Indicators';
        items = currentData.filter(d => d.operational_tag && d.operational_tag.includes('transport'));
        renderGroupedItems(body, items, 'operational_tag');
    } else if (type === 'weather') {
        title.textContent = 'Weather & Natural Hazards';
        items = currentData.filter(d => d.operational_tag && d.operational_tag.includes('weather'));
        renderGroupedItems(body, items, 'operational_tag');
    } else if (type === 'economy') {
        title.textContent = 'Economic Indicators';
        items = currentData.filter(d => d.operational_tag && d.operational_tag.includes('economic'));
        renderGroupedItems(body, items, 'operational_tag');
    } else if (type === 'sentiment') {
        title.textContent = 'Public Sentiment & Social Media Trends';
        items = currentData.filter(d => d.operational_tag && d.operational_tag.includes('sentiment'));
        renderGroupedItems(body, items, 'operational_tag');
    } else if (type === 'energy') {
        title.textContent = 'Energy & Utilities (Power, Fuel)';
        items = currentData.filter(d => d.operational_tag && (d.operational_tag.includes('energy') || d.operational_tag.includes('utilities')));
        renderGroupedItems(body, items, 'operational_tag');
    }
}

function renderGroupedItems(container, items, groupField) {
    if (items.length === 0) {
        container.innerHTML = '<p style="color: var(--text-secondary);">No indicators found for this category.</p>';
        return;
    }

    // Grouping logic
    const groups = {};
    items.forEach(item => {
        // Handle comma-separated tags if necessary, but keep simple for now
        const key = item[groupField] || 'Uncategorized';
        if (!groups[key]) groups[key] = [];
        groups[key].push(item);
    });

    Object.keys(groups).sort().forEach(groupName => {
        const section = document.createElement('div');
        section.className = 'modal-section';

        const h3 = document.createElement('h3');
        h3.innerHTML = `<i class="fa-solid fa-layer-group" style="font-size: 0.9em; opacity: 0.7;"></i> ${groupName}`;
        section.appendChild(h3);

        groups[groupName].forEach(item => {
            const div = document.createElement('div');
            div.style.cssText = 'padding: 1rem; background: rgba(255,255,255,0.03); border-radius: 8px; margin-bottom: 0.5rem; border: 1px solid var(--border);';
            div.innerHTML = `
                <div style="font-weight: 500; margin-bottom: 0.25rem;">${item.Title}</div>
                <div style="font-size: 0.85rem; color: var(--text-secondary); margin-bottom: 0.5rem;">${item.Summary}</div>
                <div style="display: flex; justify-content: space-between; font-size: 0.75rem; color: var(--text-muted);">
                    <span>${item.Source}</span>
                    <a href="${item.Link}" target="_blank" style="color: var(--accent);">Read Source <i class="fa-solid fa-external-link-alt"></i></a>
                </div>
            `;
            section.appendChild(div);
        });

        container.appendChild(section);
    });
}

function updateSignals(data) {
    if (!data) return;

    // 1. National Activity (Major Events / Emerging)
    const nationalItems = data.filter(d => d.event_flag && d.event_flag !== 'Normal' && d.event_flag !== 'nan');
    renderSignalList('list-national', nationalItems.slice(0, 5), 'event_flag');

    // 2. Operational Environment (Tags != general)
    const operationalItems = data.filter(d => d.operational_tag && d.operational_tag !== 'general');
    renderSignalList('list-operational', operationalItems.slice(0, 5), 'operational_tag');

    // 3. Risk & Opportunity (Impact contains Risk or Opportunity)
    // Sort by absolute impact score to get most significant
    const riskOppItems = data.filter(d => {
        const imp = (d.impact_level || '').toLowerCase();
        return imp.includes('risk') || imp.includes('opportunity');
    }).sort((a, b) => Math.abs(b.impact_score) - Math.abs(a.impact_score));
    renderSignalList('list-risk', riskOppItems.slice(0, 5), 'impact_level');

    // 4. Transport & Mobility
    const transportItems = data.filter(d => d.operational_tag && d.operational_tag.includes('transport'));
    renderSignalList('list-transport', transportItems.slice(0, 5), 'operational_tag');

    // 5. Weather & Hazards
    const weatherItems = data.filter(d => d.operational_tag && d.operational_tag.includes('weather'));
    renderSignalList('list-weather', weatherItems.slice(0, 5), 'operational_tag');

    // 6. Economic Indicators
    const economyItems = data.filter(d => d.operational_tag && d.operational_tag.includes('economic'));
    renderSignalList('list-economy', economyItems.slice(0, 5), 'operational_tag');

    // 7. Public Sentiment
    const sentimentItems = data.filter(d => d.operational_tag && d.operational_tag.includes('sentiment'));
    renderSignalList('list-sentiment', sentimentItems.slice(0, 5), 'operational_tag');

    // 8. Energy & Utilities
    const energyItems = data.filter(d => d.operational_tag && (d.operational_tag.includes('energy') || d.operational_tag.includes('utilities')));
    renderSignalList('list-energy', energyItems.slice(0, 5), 'operational_tag');
}

function renderSignalList(elementId, items, badgeField) {
    const list = document.getElementById(elementId);
    list.innerHTML = '';

    if (items.length === 0) {
        list.innerHTML = '<div style="color: var(--text-muted); font-size: 0.8rem; font-style: italic;">No active indicators</div>';
        return;
    }

    items.forEach(item => {
        const row = document.createElement('div');
        row.style.cssText = 'padding: 0.75rem 0; border-bottom: 1px solid var(--border-color); font-size: 0.9rem;';

        let badgeColor = '#64748b';
        const badgeText = item[badgeField];

        // Simple badge logic
        if (badgeText.includes('Risk')) badgeColor = '#ef4444';
        else if (badgeText.includes('Opportunity')) badgeColor = '#22c55e';
        else if (badgeText.includes('Major')) badgeColor = '#f59e0b';
        else if (badgeText !== 'general') badgeColor = '#3b82f6';

        row.innerHTML = `
            <div style="display: flex; justify-content: space-between; align-items: flex-start; gap: 0.5rem; margin-bottom: 0.25rem;">
                <span style="font-weight: 500; color: var(--text-primary); line-height: 1.3;">${item.Title}</span>
            </div>
            <div style="display: flex; gap: 0.5rem; align-items: center; margin-top: 0.4rem;">
                <span style="background: ${badgeColor}20; color: ${badgeColor}; font-size: 0.7rem; padding: 2px 6px; border-radius: 4px; font-weight: 600;">
                    ${badgeText}
                </span>
                <span style="font-size: 0.75rem; color: var(--text-muted);">${item.Source}</span>
            </div>
        `;
        list.appendChild(row);
    });
}


function updateCharts(data) {
    // Impact Distribution
    const impactCounts = {};
    data.forEach(d => {
        impactCounts[d.impact_level] = (impactCounts[d.impact_level] || 0) + 1;
    });

    const impactLabels = ["High Risk", "Risk", "Neutral", "Opportunity", "High Opportunity"];
    const impactValues = impactLabels.map(l => impactCounts[l] || 0);

    const ctxImpact = document.getElementById('impactChart').getContext('2d');

    if (impactChart) {
        impactChart.data.datasets[0].data = impactValues;
        impactChart.update();
    } else {
        impactChart = new Chart(ctxImpact, {
            type: 'doughnut',
            data: {
                labels: impactLabels,
                datasets: [{
                    data: impactValues,
                    backgroundColor: [
                        '#ef4444', // High Risk
                        'rgba(239, 68, 68, 0.6)', // Risk
                        '#94a3b8', // Neutral
                        'rgba(34, 197, 94, 0.6)', // Opportunity
                        '#22c55e'  // High Opportunity
                    ],
                    borderWidth: 0
                }]
            },
            options: {
                responsive: true,
                plugins: {
                    legend: {
                        position: 'right',
                        labels: { color: '#94a3b8' }
                    }
                }
            }
        });
    }

    // Operational Categories
    const opsCounts = {};
    data.forEach(d => {
        const tags = d.operational_tag.split(', ');
        tags.forEach(t => {
            if (t !== 'general') {
                opsCounts[t] = (opsCounts[t] || 0) + 1;
            }
        });
    });

    const opsLabels = Object.keys(opsCounts);
    const opsValues = Object.values(opsCounts);

    const ctxOps = document.getElementById('opsChart').getContext('2d');

    if (opsChart) {
        opsChart.data.labels = opsLabels;
        opsChart.data.datasets[0].data = opsValues;
        opsChart.update();
    } else {
        opsChart = new Chart(ctxOps, {
            type: 'bar',
            data: {
                labels: opsLabels,
                datasets: [{
                    label: 'Count',
                    data: opsValues,
                    backgroundColor: '#3b82f6',
                    borderRadius: 4
                }]
            },
            options: {
                responsive: true,
                scales: {
                    y: {
                        beginAtZero: true,
                        grid: { color: '#334155' },
                        ticks: { color: '#94a3b8' }
                    },
                    x: {
                        grid: { display: false },
                        ticks: { color: '#94a3b8' }
                    }
                },
                plugins: {
                    legend: { display: false }
                }
            }
        });
    }
}

// ===== MARKET DATA FUNCTIONALITY =====

let marketChart = null;
let currentMarketType = 'usd-lkr';

function setupMarketData() {
    const selector = document.getElementById('market-selector');
    const refreshBtn = document.getElementById('market-refresh-btn');

    if (selector) {
        selector.addEventListener('change', (e) => {
            currentMarketType = e.target.value;
            fetchMarketData(currentMarketType);
        });
    }

    if (refreshBtn) {
        refreshBtn.addEventListener('click', async () => {
            const icon = refreshBtn.querySelector('i');
            icon.classList.add('fa-spin');
            refreshBtn.disabled = true;

            try {
                await fetch('/api/market/update', { method: 'POST' });
                await fetchMarketData(currentMarketType);
            } catch (error) {
                console.error('Error updating market data:', error);
            } finally {
                icon.classList.remove('fa-spin');
                refreshBtn.disabled = false;
            }
        });
    }

    // Initial load
    fetchMarketData(currentMarketType);
}

async function fetchMarketData(type) {
    try {
        let endpoint = '';
        let title = '';

        switch (type) {
            case 'usd-lkr':
                endpoint = '/api/market/usd-lkr';
                title = 'USD / LKR Exchange Rate';
                break;
            case 'gold':
                endpoint = '/api/market/gold';
                title = 'Gold Price (24K per gram)';
                break;
            case 'fuel':
                endpoint = '/api/market/fuel';
                title = 'Fuel Prices';
                break;
            case 'inflation':
                endpoint = '/api/market/inflation';
                title = 'Inflation Rate (%)';
                break;
        }

        const response = await fetch(endpoint);
        const data = await response.json();

        document.getElementById('market-title').textContent = title;
        renderMarketData(data, type);
    } catch (error) {
        console.error('Error fetching market data:', error);
        document.getElementById('market-current-value').textContent = 'Error loading data';
    }
}

function renderMarketData(data, type) {
    const valueContainer = document.getElementById('market-current-value');
    const subtitleContainer = document.getElementById('market-subtitle');

    if (type === 'fuel') {
        // Fuel prices - display all fuel types
        if (data.current) {
            let html = '<div style="display: grid; grid-template-columns: repeat(auto-fit, minmax(200px, 1fr)); gap: 1rem;">';
            for (const [fuel, price] of Object.entries(data.current)) {
                html += `
                    <div style="background: rgba(255,255,255,0.05); padding: 1rem; border-radius: 8px;">
                        <div style="font-size: 0.85rem; color: var(--text-secondary); margin-bottom: 0.25rem;">${fuel}</div>
                        <div style="font-size: 1.5rem; font-weight: 600; color: var(--accent);">Rs. ${price.toFixed(2)}</div>
                    </div>
                `;
            }
            html += '</div>';
            valueContainer.innerHTML = html;
            subtitleContainer.textContent = 'Per Liter';
        } else {
            valueContainer.textContent = 'No data available';
            subtitleContainer.textContent = '';
        }

        // Render fuel chart
        renderFuelChart(data.history);
    } else {
        // USD/LKR, Gold, or Inflation - single value
        if (data.current !== null && data.current !== undefined) {
            let prefix = '';
            let suffix = '';

            if (type === 'usd-lkr') {
                prefix = 'Rs. ';
                subtitleContainer.textContent = 'per USD';
            } else if (type === 'gold') {
                prefix = 'Rs. ';
                subtitleContainer.textContent = 'per gram (24K)';
            } else if (type === 'inflation') {
                // suffix = '%'; // CPI is an index, no percentage
                subtitleContainer.textContent = 'Consumer Price Index (Base 2013=100)';
            }

            valueContainer.textContent = prefix + data.current.toFixed(2) + suffix;
        } else {
            valueContainer.textContent = 'No data available';
            subtitleContainer.textContent = '';
        }

        // Render single value chart
        renderMarketChart(data.history, type);
    }
}

function renderMarketChart(history, type) {
    if (!history || history.length === 0) {
        return;
    }

    const ctx = document.getElementById('marketChart').getContext('2d');

    const labels = history.map(item => item.date);
    const values = history.map(item => item.value);

    if (marketChart) {
        marketChart.destroy();
    }

    let chartLabel = 'Value';
    if (type === 'usd-lkr') chartLabel = 'USD/LKR Rate';
    else if (type === 'gold') chartLabel = 'Gold Price (LKR)';
    else if (type === 'inflation') chartLabel = 'Consumer Price Index (CPI)';

    marketChart = new Chart(ctx, {
        type: 'line',
        data: {
            labels: labels,
            datasets: [{
                label: chartLabel,
                data: values,
                borderColor: '#3b82f6',
                backgroundColor: 'rgba(59, 130, 246, 0.1)',
                borderWidth: 2,
                fill: true,
                tension: 0.4
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            scales: {
                y: {
                    beginAtZero: false,
                    grid: { color: '#334155' },
                    ticks: { color: '#94a3b8' }
                },
                x: {
                    grid: { display: false },
                    ticks: {
                        color: '#94a3b8',
                        maxRotation: 45,
                        minRotation: 45
                    }
                }
            },
            plugins: {
                legend: {
                    display: true,
                    labels: { color: '#94a3b8' }
                }
            }
        }
    });
}


function renderFuelChart(history) {
    if (!history || history.length === 0) {
        return;
    }

    const ctx = document.getElementById('marketChart').getContext('2d');

    const labels = history.map(item => item.date);

    // Extract all fuel types
    const fuelTypes = new Set();
    history.forEach(item => {
        if (item.values) {
            Object.keys(item.values).forEach(fuel => fuelTypes.add(fuel));
        }
    });

    const datasets = [];
    const colors = ['#3b82f6', '#10b981', '#f59e0b', '#ef4444', '#8b5cf6'];
    let colorIndex = 0;

    fuelTypes.forEach(fuelType => {
        const data = history.map(item => item.values && item.values[fuelType] ? item.values[fuelType] : null);
        datasets.push({
            label: fuelType,
            data: data,
            borderColor: colors[colorIndex % colors.length],
            backgroundColor: 'transparent',
            borderWidth: 2,
            tension: 0.4
        });
        colorIndex++;
    });

    if (marketChart) {
        marketChart.destroy();
    }

    marketChart = new Chart(ctx, {
        type: 'line',
        data: {
            labels: labels,
            datasets: datasets
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            scales: {
                y: {
                    beginAtZero: false,
                    grid: { color: '#334155' },
                    ticks: { color: '#94a3b8' }
                },
                x: {
                    grid: { display: false },
                    ticks: {
                        color: '#94a3b8',
                        maxRotation: 45,
                        minRotation: 45
                    }
                }
            },
            plugins: {
                legend: {
                    display: true,
                    position: 'top',
                    labels: { color: '#94a3b8' }
                }
            }
        }
    });
}

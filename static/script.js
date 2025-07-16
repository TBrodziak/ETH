// Ethereum Monitoring Bot Dashboard JavaScript

class EthBotDashboard {
    constructor() {
        this.updateInterval = null;
        this.priceChart = null;
        this.isUpdating = false;
        
        this.init();
    }
    
    init() {
        // Initialize Feather icons if available
        if (typeof feather !== 'undefined') {
            feather.replace();
        }
        
        // Set up event listeners
        this.setupEventListeners();
        
        // Start periodic updates
        this.startPeriodicUpdates();
        
        // Initial data load
        this.updateDashboard();
        
        console.log('ETH Bot Dashboard initialized');
    }
    
    setupEventListeners() {
        // Bot control buttons
        document.getElementById('startBtn').addEventListener('click', () => this.startBot());
        document.getElementById('stopBtn').addEventListener('click', () => this.stopBot());
        document.getElementById('testBtn').addEventListener('click', () => this.testTelegram());
        document.getElementById('manualCheckBtn').addEventListener('click', () => this.manualCheck());
        
        // Auto-refresh when page becomes visible
        document.addEventListener('visibilitychange', () => {
            if (!document.hidden && !this.isUpdating) {
                this.updateDashboard();
            }
        });
    }
    
    startPeriodicUpdates() {
        // Update every 10 seconds
        this.updateInterval = setInterval(() => {
            if (!this.isUpdating) {
                this.updateDashboard();
            }
        }, 10000);
    }
    
    stopPeriodicUpdates() {
        if (this.updateInterval) {
            clearInterval(this.updateInterval);
            this.updateInterval = null;
        }
    }
    
    async updateDashboard() {
        if (this.isUpdating) return;
        
        this.isUpdating = true;
        
        try {
            // Update main status
            await this.updateStatus();
            
            // Update price history
            await this.updatePriceHistory();
            
            // Update last update time
            document.getElementById('lastUpdate').textContent = new Date().toLocaleString();
            
        } catch (error) {
            console.error('Error updating dashboard:', error);
            this.showAlert('Error updating dashboard: ' + error.message, 'danger');
        } finally {
            this.isUpdating = false;
        }
    }
    
    async updateStatus() {
        try {
            const response = await fetch('/api/status');
            const data = await response.json();
            
            // Update status indicators
            this.updateBotStatus(data.bot_running);
            this.updatePriceDisplay(data.current_price);
            this.updateCounters(data.total_alerts_sent, data.total_news_sent);
            this.updateConfiguration(data.config);
            this.updateSystemStatus(data);
            this.updateScheduledTasks(data.scheduler);
            
        } catch (error) {
            console.error('Error fetching status:', error);
            throw error;
        }
    }
    
    updateBotStatus(isRunning) {
        const statusElement = document.getElementById('botStatus');
        const statusCard = statusElement.closest('.status-card');
        
        if (isRunning) {
            statusElement.innerHTML = '<span class="status-badge online">✅ Running</span>';
            statusCard.classList.remove('pulse');
            statusCard.classList.add('pulse');
        } else {
            statusElement.innerHTML = '<span class="status-badge offline">❌ Stopped</span>';
            statusCard.classList.remove('pulse');
        }
        
        if (typeof feather !== 'undefined') {
            feather.replace();
        }
    }
    
    updatePriceDisplay(currentPrice) {
        if (currentPrice !== null && currentPrice !== undefined) {
            const priceElement = document.getElementById('currentPrice');
            const priceDisplayElement = document.getElementById('priceDisplay');
            
            const formattedPrice = `$${currentPrice.toLocaleString('en-US', {
                minimumFractionDigits: 2,
                maximumFractionDigits: 2
            })}`;
            
            priceElement.textContent = formattedPrice;
            if (priceDisplayElement) {
                priceDisplayElement.textContent = formattedPrice;
            }
        }
    }
    
    updateCounters(alertCount, newsCount) {
        document.getElementById('alertCount').textContent = alertCount || 0;
        document.getElementById('newsCount').textContent = newsCount || 0;
    }
    
    updateConfiguration(config) {
        if (config) {
            document.getElementById('priceThreshold').textContent = `${config.price_threshold}%`;
            document.getElementById('checkInterval').textContent = `${config.check_interval}s`;
            document.getElementById('dailyReports').textContent = config.daily_report_hours.join(', ');
            document.getElementById('newsEnabled').textContent = config.news_enabled ? 'Enabled' : 'Disabled';
        }
    }
    
    updateSystemStatus(data) {
        // Bot start time
        if (data.bot_start_time) {
            const startTime = new Date(data.bot_start_time).toLocaleString();
            document.getElementById('botStartTime').textContent = startTime;
        }
        
        // Last error
        const errorElement = document.getElementById('lastError');
        if (data.last_error) {
            errorElement.textContent = data.last_error;
            errorElement.className = 'text-danger';
        } else {
            errorElement.textContent = 'None';
            errorElement.className = 'text-success';
        }
    }
    
    updateScheduledTasks(scheduler) {
        const tasksContainer = document.getElementById('scheduledTasks');
        
        if (!scheduler || !scheduler.tasks) {
            tasksContainer.innerHTML = '<div class="text-muted">No scheduled tasks</div>';
            return;
        }
        
        let tasksHtml = '';
        scheduler.tasks.forEach(task => {
            const statusClass = scheduler.running ? 'running' : 'scheduled';
            const statusText = scheduler.running ? 'Running' : 'Scheduled';
            
            let scheduleInfo = '';
            if (task.type === 'periodic') {
                scheduleInfo = `Every ${task.interval}`;
            } else if (task.type === 'hourly') {
                scheduleInfo = `Hours: ${task.hours.join(', ')}`;
            } else if (task.type === 'daily') {
                scheduleInfo = `Daily at ${task.time}`;
            }
            
            tasksHtml += `
                <div class="task-item">
                    <div class="task-info">
                        <h6>${task.name}</h6>
                        <small>${scheduleInfo}</small>
                    </div>
                    <span class="task-status ${statusClass}">${statusText}</span>
                </div>
            `;
        });
        
        tasksContainer.innerHTML = tasksHtml;
    }
    
    async updatePriceHistory() {
        try {
            const response = await fetch('/api/price-history');
            const data = await response.json();
            
            if (data.error) {
                console.error('Price history error:', data.error);
                return;
            }
            
            // Update 24h change display
            const changeElement = document.getElementById('priceChange');
            if (changeElement && data.change_percent !== undefined) {
                const isPositive = data.change_percent >= 0;
                const sign = isPositive ? '+' : '';
                
                changeElement.textContent = `${sign}${data.change_percent.toFixed(2)}%`;
                changeElement.className = `price-change ${isPositive ? 'positive' : 'negative'}`;
            }
            
            // Update simple chart if available
            this.updatePriceChart(data);
            
        } catch (error) {
            console.error('Error fetching price history:', error);
        }
    }
    
    updatePriceChart(data) {
        const ctx = document.getElementById('priceChart');
        if (!ctx) return;
        
        // Destroy existing chart
        if (this.priceChart) {
            this.priceChart.destroy();
        }
        
        // Create simple price visualization
        const isPositive = data.change_percent >= 0;
        const color = isPositive ? '#28a745' : '#dc3545';
        
        this.priceChart = new Chart(ctx, {
            type: 'line',
            data: {
                labels: ['24h ago', 'Now'],
                datasets: [{
                    label: 'ETH Price',
                    data: [data.price_24h_ago, data.current_price],
                    borderColor: color,
                    backgroundColor: color + '20',
                    borderWidth: 3,
                    fill: true,
                    tension: 0.4,
                    pointBackgroundColor: color,
                    pointBorderColor: '#fff',
                    pointBorderWidth: 2,
                    pointRadius: 6
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                scales: {
                    y: {
                        beginAtZero: false,
                        grid: {
                            color: '#e9ecef'
                        },
                        ticks: {
                            callback: function(value) {
                                return '$' + value.toLocaleString();
                            }
                        }
                    },
                    x: {
                        grid: {
                            display: false
                        }
                    }
                },
                plugins: {
                    legend: {
                        display: false
                    },
                    tooltip: {
                        callbacks: {
                            label: function(context) {
                                return 'Price: $' + context.parsed.y.toLocaleString();
                            }
                        }
                    }
                },
                elements: {
                    point: {
                        hoverRadius: 8
                    }
                }
            }
        });
    }
    
    // Bot control methods
    async startBot() {
        await this.apiCall('/api/start', 'POST', 'Starting bot...');
    }
    
    async stopBot() {
        await this.apiCall('/api/stop', 'POST', 'Stopping bot...');
    }
    
    async testTelegram() {
        await this.apiCall('/api/test-telegram', 'POST', 'Testing Telegram connection...');
    }
    
    async manualCheck() {
        await this.apiCall('/api/manual-check', 'POST', 'Running manual check...');
    }
    
    async apiCall(url, method, loadingMessage) {
        try {
            this.showAlert(loadingMessage, 'info');
            
            const response = await fetch(url, { method });
            const data = await response.json();
            
            if (data.success) {
                this.showAlert(data.message, 'success');
            } else {
                this.showAlert(data.message, 'danger');
            }
            
            // Update dashboard after API call
            setTimeout(() => this.updateDashboard(), 1000);
            
        } catch (error) {
            this.showAlert('Network error: ' + error.message, 'danger');
        }
    }
    
    showAlert(message, type = 'info') {
        const alertContainer = document.getElementById('alertContainer');
        const alertId = 'alert-' + Date.now();
        
        const alertHtml = `
            <div id="${alertId}" class="alert alert-${type} alert-dismissible fade show" role="alert">
                <i data-feather="${this.getAlertIcon(type)}"></i>
                ${message}
                <button type="button" class="btn-close" data-bs-dismiss="alert"></button>
            </div>
        `;
        
        alertContainer.insertAdjacentHTML('afterbegin', alertHtml);
        if (typeof feather !== 'undefined') {
            feather.replace();
        }
        
        // Auto-dismiss after 5 seconds
        setTimeout(() => {
            const alert = document.getElementById(alertId);
            if (alert) {
                const bsAlert = new bootstrap.Alert(alert);
                bsAlert.close();
            }
        }, 5000);
    }
    
    getAlertIcon(type) {
        const icons = {
            success: 'check-circle',
            danger: 'alert-circle',
            warning: 'alert-triangle',
            info: 'info'
        };
        return icons[type] || 'info';
    }
    
    // Cleanup method
    destroy() {
        this.stopPeriodicUpdates();
        if (this.priceChart) {
            this.priceChart.destroy();
        }
    }
}

// Initialize dashboard when DOM is loaded
document.addEventListener('DOMContentLoaded', () => {
    window.ethBotDashboard = new EthBotDashboard();
});

// Handle page unload
window.addEventListener('beforeunload', () => {
    if (window.ethBotDashboard) {
        window.ethBotDashboard.destroy();
    }
});

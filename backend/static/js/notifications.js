/**
 * Modern Notification System for ServicesBladi
 * Handles dynamic notification fetching, display, and management
 */

class NotificationManager {
    constructor() {
        this.isOpen = false;
        this.notifications = [];
        this.unreadCount = 0;
        this.refreshInterval = null;
        this.baseUrl = '/notifications/api';
        
        this.init();
    }

    init() {
        this.bindEvents();
        this.loadNotifications();
        this.startAutoRefresh();
    }

    bindEvents() {
        // Notification button (works for both desktop and mobile)
        const notificationButton = document.getElementById('notification-button');
        
        if (notificationButton) {
            notificationButton.addEventListener('click', (e) => {
                e.stopPropagation();
                this.toggleDropdown();
            });
        }

        // Mark all read button
        const markAllReadBtn = document.getElementById('mark-all-read-btn');
        if (markAllReadBtn) {
            markAllReadBtn.addEventListener('click', () => this.markAllAsRead());
        }

        // Refresh notifications button
        const refreshBtn = document.getElementById('refresh-notifications-btn');
        if (refreshBtn) {
            refreshBtn.addEventListener('click', () => this.loadNotifications());
        }

        // Close dropdown when clicking outside
        document.addEventListener('click', (e) => {
            const dropdown = document.getElementById('notification-dropdown');
            const containers = document.querySelectorAll('.notification-container');
            
            let clickedInside = false;
            containers.forEach(container => {
                if (container && container.contains(e.target)) {
                    clickedInside = true;
                }
            });
            
            if (dropdown && !clickedInside) {
                this.closeDropdown();
            }
        });

        // Keyboard navigation
        document.addEventListener('keydown', (e) => {
            if (e.key === 'Escape' && this.isOpen) {
                this.closeDropdown();
            }
        });
    }

    async loadNotifications() {
        try {
            this.showLoading();
            
            const response = await fetch(`${this.baseUrl}/get/`, {
                method: 'GET',
                headers: {
                    'X-Requested-With': 'XMLHttpRequest',
                    'Content-Type': 'application/json',
                },
                credentials: 'same-origin'
            });

            if (!response.ok) {
                throw new Error(`HTTP error! status: ${response.status}`);
            }

            const data = await response.json();
            this.notifications = data.notifications || [];
            this.unreadCount = data.unread_count || 0;
            
            this.updateUI();
            this.renderNotifications();
            
        } catch (error) {
            console.error('Error loading notifications:', error);
            this.showError('Failed to load notifications');
        } finally {
            this.hideLoading();
        }
    }

    async markAsRead(notificationId) {
        try {
            const response = await fetch(`${this.baseUrl}/mark-read/${notificationId}/`, {
                method: 'POST',
                headers: {
                    'X-Requested-With': 'XMLHttpRequest',
                    'Content-Type': 'application/json',
                    'X-CSRFToken': this.getCSRFToken()
                },
                credentials: 'same-origin'
            });

            if (response.ok) {
                // Update local state
                const notification = this.notifications.find(n => n.id === notificationId);
                if (notification && !notification.is_read) {
                    notification.is_read = true;
                    this.unreadCount = Math.max(0, this.unreadCount - 1);
                    this.updateUI();
                    this.renderNotifications();
                }
            }
        } catch (error) {
            console.error('Error marking notification as read:', error);
        }
    }

    async markAllAsRead() {
        try {
            const response = await fetch(`${this.baseUrl}/mark-all-read/`, {
                method: 'POST',
                headers: {
                    'X-Requested-With': 'XMLHttpRequest',
                    'Content-Type': 'application/json',
                    'X-CSRFToken': this.getCSRFToken()
                },
                credentials: 'same-origin'
            });

            if (response.ok) {
                // Update local state
                this.notifications.forEach(n => n.is_read = true);
                this.unreadCount = 0;
                this.updateUI();
                this.renderNotifications();
            }
        } catch (error) {
            console.error('Error marking all notifications as read:', error);
        }
    }

    async deleteNotification(notificationId) {
        try {
            const response = await fetch(`${this.baseUrl}/delete/${notificationId}/`, {
                method: 'DELETE',
                headers: {
                    'X-Requested-With': 'XMLHttpRequest',
                    'Content-Type': 'application/json',
                    'X-CSRFToken': this.getCSRFToken()
                },
                credentials: 'same-origin'
            });

            if (response.ok) {
                // Remove from local state
                const index = this.notifications.findIndex(n => n.id === notificationId);
                if (index !== -1) {
                    const notification = this.notifications[index];
                    if (!notification.is_read) {
                        this.unreadCount = Math.max(0, this.unreadCount - 1);
                    }
                    this.notifications.splice(index, 1);
                    this.updateUI();
                    this.renderNotifications();
                }
            }
        } catch (error) {
            console.error('Error deleting notification:', error);
        }
    }

    toggleDropdown() {
        if (this.isOpen) {
            this.closeDropdown();
        } else {
            this.openDropdown();
        }
    }

    openDropdown() {
        const dropdown = document.getElementById('notification-dropdown');
        if (dropdown) {
            dropdown.classList.remove('hidden', 'notification-hide');
            dropdown.classList.add('notification-show');
            this.isOpen = true;
            
            // Load fresh notifications when opening
            this.loadNotifications();
        }
    }

    closeDropdown() {
        const dropdown = document.getElementById('notification-dropdown');
        if (dropdown) {
            dropdown.classList.add('notification-hide');
            setTimeout(() => {
                dropdown.classList.add('hidden');
                dropdown.classList.remove('notification-show', 'notification-hide');
            }, 200);
            this.isOpen = false;
        }
    }

    showMobileNotifications() {
        // For mobile, we'll redirect to a full page view or show a modal
        // For now, just open the dropdown
        this.openDropdown();
    }

    updateUI() {
        // Update badge (single notification badge for both desktop and mobile)
        const badge = document.getElementById('notification-badge');
        
        if (badge) {
            if (this.unreadCount > 0) {
                badge.textContent = this.unreadCount > 99 ? '99+' : this.unreadCount;
                badge.classList.remove('hidden');
                badge.classList.add('notification-pulse');
            } else {
                badge.classList.add('hidden');
                badge.classList.remove('notification-pulse');
            }
        }

        // Update mark all read button
        const markAllReadBtn = document.getElementById('mark-all-read-btn');
        if (markAllReadBtn) {
            markAllReadBtn.style.display = this.unreadCount > 0 ? 'block' : 'none';
        }
    }

    renderNotifications() {
        const container = document.getElementById('notifications-content');
        const emptyState = document.getElementById('notifications-empty');
        
        if (!container) return;

        if (this.notifications.length === 0) {
            container.innerHTML = '';
            if (emptyState) emptyState.classList.remove('hidden');
            return;
        }

        if (emptyState) emptyState.classList.add('hidden');

        container.innerHTML = this.notifications.map(notification => 
            this.renderNotificationItem(notification)
        ).join('');

        // Bind events for notification items
        this.bindNotificationEvents();
    }

    renderNotificationItem(notification) {
        const isUnread = !notification.is_read;
        const bgClass = isUnread ? 'bg-blue-50' : 'bg-white';
        const dotClass = isUnread ? 'bg-blue-500' : 'bg-gray-300';
        
        return `
            <div class="notification-item px-3 py-2 hover:bg-gray-50 transition-colors duration-150 ${bgClass}" 
                 data-notification-id="${notification.id}">
                <div class="flex items-start space-x-2">
                    <!-- Icon and unread indicator -->
                    <div class="flex-shrink-0 flex items-center">
                        <div class="w-6 h-6 rounded-full ${notification.color} flex items-center justify-center">
                            ${notification.icon}
                        </div>
                        ${isUnread ? `<div class="w-1.5 h-1.5 ${dotClass} rounded-full ml-1"></div>` : ''}
                    </div>
                    
                    <!-- Content -->
                    <div class="flex-1 min-w-0">
                        <div class="flex items-start justify-between">
                            <div class="flex-1">
                                <p class="text-xs font-medium text-gray-900 truncate">
                                    ${notification.title}
                                </p>
                                <p class="text-xs text-gray-600 mt-0.5 line-clamp-2">
                                    ${notification.content}
                                </p>
                                <p class="text-xs text-gray-500 mt-0.5">
                                    ${notification.time_ago}
                                </p>
                            </div>
                            
                            <!-- Actions -->
                            <div class="flex items-center space-x-0.5 ml-1">
                                ${!isUnread ? '' : `
                                    <button class="mark-read-btn text-blue-600 hover:text-blue-800 text-xs p-0.5 rounded"
                                            data-notification-id="${notification.id}"
                                            title="Mark as read">
                                        ✓
                                    </button>
                                `}
                                <button class="delete-btn text-red-600 hover:text-red-800 text-xs p-0.5 rounded"
                                        data-notification-id="${notification.id}"
                                        title="Delete">
                                    ×
                                </button>
                            </div>
                        </div>
                    </div>
                </div>
            </div>
        `;
    }

    bindNotificationEvents() {
        // Mark as read buttons
        document.querySelectorAll('.mark-read-btn').forEach(btn => {
            btn.addEventListener('click', (e) => {
                e.stopPropagation();
                const notificationId = parseInt(btn.dataset.notificationId);
                this.markAsRead(notificationId);
            });
        });

        // Delete buttons
        document.querySelectorAll('.delete-btn').forEach(btn => {
            btn.addEventListener('click', (e) => {
                e.stopPropagation();
                const notificationId = parseInt(btn.dataset.notificationId);
                if (confirm('Are you sure you want to delete this notification?')) {
                    this.deleteNotification(notificationId);
                }
            });
        });

        // Notification item click (mark as read)
        document.querySelectorAll('.notification-item').forEach(item => {
            item.addEventListener('click', () => {
                const notificationId = parseInt(item.dataset.notificationId);
                const notification = this.notifications.find(n => n.id === notificationId);
                if (notification && !notification.is_read) {
                    this.markAsRead(notificationId);
                }
            });
        });
    }

    showLoading() {
        const loading = document.getElementById('notifications-loading');
        const content = document.getElementById('notifications-content');
        const empty = document.getElementById('notifications-empty');
        
        if (loading) loading.classList.remove('hidden');
        if (content) content.classList.add('hidden');
        if (empty) empty.classList.add('hidden');
    }

    hideLoading() {
        const loading = document.getElementById('notifications-loading');
        const content = document.getElementById('notifications-content');
        
        if (loading) loading.classList.add('hidden');
        if (content) content.classList.remove('hidden');
    }

    showError(message) {
        const container = document.getElementById('notifications-content');
        if (container) {
            container.innerHTML = `
                <div class="px-4 py-3 text-center">
                    <div class="text-red-600 text-sm">
                        <svg class="mx-auto h-8 w-8 mb-2" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 8v4m0 4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
                        </svg>
                        ${message}
                    </div>
                    <button onclick="notificationManager.loadNotifications()" class="mt-2 text-blue-600 hover:text-blue-800 text-sm">
                        Try again
                    </button>
                </div>
            `;
        }
    }

    startAutoRefresh() {
        // Refresh notifications every 30 seconds
        this.refreshInterval = setInterval(() => {
            if (!this.isOpen) {
                // Only refresh counts when dropdown is closed to avoid interference
                this.loadNotificationCounts();
            }
        }, 30000);
    }

    async loadNotificationCounts() {
        try {
            const response = await fetch(`${this.baseUrl}/counts/`, {
                method: 'GET',
                headers: {
                    'X-Requested-With': 'XMLHttpRequest',
                },
                credentials: 'same-origin'
            });

            if (response.ok) {
                const data = await response.json();
                this.unreadCount = data.unread_count || 0;
                this.updateUI();
            }
        } catch (error) {
            console.error('Error loading notification counts:', error);
        }
    }

    getCSRFToken() {
        const token = document.querySelector('[name=csrfmiddlewaretoken]');
        if (token) return token.value;
        
        const cookie = document.cookie.split(';').find(c => c.trim().startsWith('csrftoken='));
        return cookie ? cookie.split('=')[1] : '';
    }

    destroy() {
        if (this.refreshInterval) {
            clearInterval(this.refreshInterval);
        }
    }
}

// Initialize notification manager when DOM is loaded
let notificationManager;

document.addEventListener('DOMContentLoaded', () => {
    notificationManager = new NotificationManager();
});

// Clean up on page unload
window.addEventListener('beforeunload', () => {
    if (notificationManager) {
        notificationManager.destroy();
    }
});

// Export for use in other scripts
window.NotificationManager = NotificationManager;

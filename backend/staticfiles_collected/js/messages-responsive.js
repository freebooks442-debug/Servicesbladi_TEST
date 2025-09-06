/**
 * ServicesBladi - Messages Responsive JavaScript
 * Handles mobile-first responsive behavior for messaging interfaces
 */

class MessagesResponsive {
    constructor(options = {}) {
        this.options = {
            breakpoint: 992,
            animationDuration: 300,
            debounceDelay: 300,
            ...options
        };
        
        this.isMobile = window.innerWidth <= this.options.breakpoint;
        this.isNavigating = false;
        this.lastClickTime = 0;
        this.clickDelay = 1000; // Prevent rapid clicks
        
        this.init();
    }
    
    init() {
        this.cacheDOMElements();
        this.bindEvents();
        this.initMobileView();
        
        console.log('Messages responsive initialized');
    }
    
    cacheDOMElements() {
        this.chatContainer = document.querySelector('.chat-container');
        this.contactsList = document.querySelector('.contacts-list');
        this.chatMain = document.querySelector('.chat-main');
        this.showContactsBtn = document.getElementById('showContacts');
        this.contactItems = document.querySelectorAll('.contact-item');
        this.searchInput = document.getElementById('contactSearch');
    }
    
    bindEvents() {
        // Back to contacts button
        if (this.showContactsBtn) {
            this.showContactsBtn.addEventListener('click', (e) => this.handleBackToContacts(e));
        }
        
        // Contact item clicks
        this.contactItems.forEach(item => {
            item.addEventListener('click', (e) => this.handleContactClick(e, item));
        });
        
        // Search functionality
        if (this.searchInput) {
            let searchTimeout;
            this.searchInput.addEventListener('input', (e) => {
                clearTimeout(searchTimeout);
                searchTimeout = setTimeout(() => {
                    this.handleSearch(e.target.value.trim());
                }, this.options.debounceDelay);
            });
        }
        
        // Window resize
        window.addEventListener('resize', () => this.handleResize());
        
        // Prevent double-tap zoom on mobile
        if (this.isMobile) {
            this.preventDoubleTabZoom();
        }
    }
    
    handleBackToContacts(e) {
        e.preventDefault();
        
        if (!this.chatContainer) return;
        
        // Show contacts list
        this.chatContainer.classList.remove('chat-active');
        
        // Navigate back after animation
        setTimeout(() => {
            this.navigateToMessages();
        }, this.options.animationDuration);
    }
    
    handleContactClick(e, contactItem) {
        e.preventDefault();
        
        const now = Date.now();
        if (now - this.lastClickTime < this.clickDelay) {
            console.log('Click ignored - too soon');
            return;
        }
        
        if (this.isNavigating) {
            console.log('Already navigating');
            return;
        }
        
        this.lastClickTime = now;
        this.isNavigating = true;
        
        const contactId = contactItem.dataset.contactId;
        if (!contactId || !/^\d+$/.test(contactId)) {
            console.warn('Invalid contact ID');
            this.isNavigating = false;
            return;
        }
        
        // Visual feedback
        contactItem.style.opacity = '0.6';
        contactItem.classList.add('loading');
        
        // Mobile behavior
        if (this.isMobile && this.chatContainer) {
            this.chatContainer.classList.add('chat-active');
            
            setTimeout(() => {
                this.navigateToContact(contactId);
            }, this.options.animationDuration);
        } else {
            // Desktop behavior
            setTimeout(() => {
                this.navigateToContact(contactId);
            }, 100);
        }
    }
    
    handleSearch(searchTerm) {
        if (!searchTerm || searchTerm.length > 50) {
            this.resetSearch();
            return;
        }
        
        try {
            this.contactItems.forEach(item => {
                const nameEl = item.querySelector('.contact-name');
                if (nameEl && nameEl.textContent) {
                    const name = nameEl.textContent.toLowerCase();
                    const isVisible = name.includes(searchTerm.toLowerCase());
                    item.style.display = isVisible ? 'flex' : 'none';
                }
            });
        } catch (error) {
            console.error('Search error:', error);
            this.resetSearch();
        }
    }
    
    resetSearch() {
        this.contactItems.forEach(item => {
            item.style.display = 'flex';
        });
    }
    
    handleResize() {
        const wasMobile = this.isMobile;
        this.isMobile = window.innerWidth <= this.options.breakpoint;
        
        if (!this.isMobile && wasMobile && this.chatContainer) {
            // Reset mobile classes when switching to desktop
            this.chatContainer.classList.remove('chat-active');
        }
        
        if (this.isMobile && !wasmobile) {
            // Initialize mobile view when switching to mobile
            this.initMobileView();
        }
    }
    
    initMobileView() {
        if (!this.isMobile || !this.chatContainer) return;
        
        const activeContact = document.querySelector('.contact-item.active');
        
        if (activeContact) {
            // If there's an active contact on mobile, show chat
            this.chatContainer.classList.add('chat-active');
        }
    }
    
    navigateToMessages() {
        try {
            // Get the base messages URL from the current context
            const currentPath = window.location.pathname;
            
            if (currentPath.includes('/client/')) {
                window.location.href = '/client/messages/';
            } else if (currentPath.includes('/expert/')) {
                window.location.href = '/expert/messages/';
            } else {
                window.location.href = '/messages/';
            }
        } catch (error) {
            console.error('Navigation error:', error);
            this.isNavigating = false;
        }
    }
    
    navigateToContact(contactId) {
        try {
            const currentPath = window.location.pathname;
            
            if (currentPath.includes('/client/')) {
                window.location.href = `/client/messages/?contact=${contactId}`;
            } else if (currentPath.includes('/expert/')) {
                window.location.href = `/expert/messages/?client=${contactId}`;
            } else {
                window.location.href = `/messages/?contact=${contactId}`;
            }
        } catch (error) {
            console.error('Navigation error:', error);
            this.isNavigating = false;
            
            // Reset UI state
            this.contactItems.forEach(item => {
                item.style.opacity = '1';
                item.classList.remove('loading');
            });
            
            if (this.chatContainer) {
                this.chatContainer.classList.remove('chat-active');
            }
        }
    }
    
    preventDoubleTabZoom() {
        let lastTouchEnd = 0;
        
        document.addEventListener('touchend', function(event) {
            const now = Date.now();
            if (now - lastTouchEnd <= 300) {
                event.preventDefault();
            }
            lastTouchEnd = now;
        }, false);
    }
    
    // Public methods for external use
    showChat() {
        if (this.chatContainer) {
            this.chatContainer.classList.add('chat-active');
        }
    }
    
    showContacts() {
        if (this.chatContainer) {
            this.chatContainer.classList.remove('chat-active');
        }
    }
    
    isMobileView() {
        return this.isMobile;
    }
    
    destroy() {
        // Cleanup event listeners if needed
        window.removeEventListener('resize', this.handleResize);
    }
}

// Auto-initialize when DOM is ready
document.addEventListener('DOMContentLoaded', function() {
    // Only initialize if we're on a messages page
    const isMessagesPage = window.location.pathname.includes('/messages');
    const hasMessagingElements = document.querySelector('.chat-container');
    
    if (isMessagesPage && hasMessagingElements) {
        window.messagesResponsive = new MessagesResponsive();
    }
});

// Export for use in other scripts
if (typeof module !== 'undefined' && module.exports) {
    module.exports = MessagesResponsive;
}

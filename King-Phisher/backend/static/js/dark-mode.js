/**
 * Dark Mode Toggle for King-Phisher
 * Handles theme switching with localStorage persistence
 */

(function () {
    'use strict';

    // Get current theme from localStorage or system preference
    function getCurrentTheme() {
        const stored = localStorage.getItem('theme');
        if (stored) return stored;

        // Check system preference
        if (window.matchMedia && window.matchMedia('(prefers-color-scheme: dark)').matches) {
            return 'dark';
        }

        return 'light';
    }

    // Apply theme to document
    function applyTheme(theme) {
        document.documentElement.setAttribute('data-theme', theme);
        localStorage.setItem('theme', theme);

        // Update toggle button icon
        const toggle = document.querySelector('.theme-toggle');
        if (toggle) {
            const icon = toggle.querySelector('.icon');
            if (icon) {
                icon.textContent = theme === 'dark' ? '☀️' : '🌙';
            }
        }

        // Notify server (optional)
        if (typeof fetch !== 'undefined') {
            fetch('/api/toggle-dark-mode', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ enabled: theme === 'dark' })
            }).catch(err => console.log('Theme sync failed:', err));
        }
    }

    // Toggle theme
    function toggleTheme() {
        const current = getCurrentTheme();
        const next = current === 'dark' ? 'light' : 'dark';
        applyTheme(next);

        // Add animation class
        document.body.classList.add('theme-transitioning');
        setTimeout(() => {
            document.body.classList.remove('theme-transitioning');
        }, 300);
    }

    // Initialize theme on page load
    function initTheme() {
        const theme = getCurrentTheme();
        applyTheme(theme);

        // Create toggle button if it doesn't exist
        if (!document.querySelector('.theme-toggle')) {
            createToggleButton();
        }

        // Listen for system theme changes
        if (window.matchMedia) {
            window.matchMedia('(prefers-color-scheme: dark)').addEventListener('change', e => {
                if (!localStorage.getItem('theme')) {
                    applyTheme(e.matches ? 'dark' : 'light');
                }
            });
        }
    }

    // Create floating toggle button
    function createToggleButton() {
        const button = document.createElement('button');
        button.className = 'theme-toggle';
        button.setAttribute('aria-label', 'Toggle dark mode');
        button.setAttribute('title', 'Toggle dark mode');

        const icon = document.createElement('span');
        icon.className = 'icon';
        icon.textContent = getCurrentTheme() === 'dark' ? '☀️' : '🌙';

        button.appendChild(icon);
        button.addEventListener('click', toggleTheme);

        document.body.appendChild(button);
    }

    // Keyboard shortcut (Ctrl/Cmd + Shift + D)
    document.addEventListener('keydown', (e) => {
        if ((e.ctrlKey || e.metaKey) && e.shiftKey && e.key === 'D') {
            e.preventDefault();
            toggleTheme();
        }
    });

    // Initialize when DOM is ready
    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', initTheme);
    } else {
        initTheme();
    }

    // Export for manual control
    window.KingPhisher = window.KingPhisher || {};
    window.KingPhisher.toggleTheme = toggleTheme;
    window.KingPhisher.setTheme = applyTheme;
    window.KingPhisher.getTheme = getCurrentTheme;

})();

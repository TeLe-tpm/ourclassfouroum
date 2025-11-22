document.addEventListener('DOMContentLoaded', function() {
    const themeToggle = document.getElementById('themeToggle');
    const html = document.documentElement;
    
    const savedTheme = localStorage.getItem('theme') || 'light';
    html.setAttribute('data-theme', savedTheme);
    updateThemeButton(savedTheme);
    
    if (themeToggle) {
        themeToggle.addEventListener('click', function() {
            const currentTheme = html.getAttribute('data-theme');
            const newTheme = currentTheme === 'light' ? 'dark' : 'light';
            
            html.setAttribute('data-theme', newTheme);
            localStorage.setItem('theme', newTheme);
            updateThemeButton(newTheme);
            
            if (typeof current_user !== 'undefined') {
                fetch('/update_theme', {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json',
                    },
                    body: JSON.stringify({ theme: newTheme })
                }).catch(error => {
                    console.error('Ошибка смены темы:', error);
                });
            }
        });
    }
    
    function updateThemeButton(theme) {
        if (themeToggle) {
            const themeIcon = themeToggle.querySelector('.theme-icon');
            themeIcon.textContent = theme === 'light' ? '🌙' : '☀️';
        }
    }
});
// myproject/myapp/static/js/theme.js (รวม darkMode.js และ animations.js)

// Theme Manager - รวมฟังก์ชันการจัดการธีมและภาพเคลื่อนไหว
const ThemeManager = {
    // ========== Dark Mode ==========
    initDarkMode: function() {
        // ตรวจสอบธีมที่บันทึกไว้
        const savedTheme = localStorage.getItem('theme');
        const userPrefersDark = window.matchMedia && window.matchMedia('(prefers-color-scheme: dark)').matches;
        
        // ตั้งค่าธีมเริ่มต้น
        if (savedTheme === 'dark' || (!savedTheme && userPrefersDark)) {
            document.documentElement.classList.add('dark');
            this.updateThemeToggle(true);
        } else {
            document.documentElement.classList.remove('dark');
            this.updateThemeToggle(false);
        }
        
        // ติดตั้งตัวจัดการเหตุการณ์
        this.attachThemeEventListeners();
    },
    
    attachThemeEventListeners: function() {
        // ตรวจสอบหาปุ่มสลับธีม
        const themeToggle = document.getElementById('theme-toggle');
        if (themeToggle) {
            themeToggle.addEventListener('click', () => this.toggleDarkMode());
        }
        
        // ติดตามการเปลี่ยนแปลงการตั้งค่าระบบ
        const mediaQuery = window.matchMedia('(prefers-color-scheme: dark)');
        mediaQuery.addEventListener('change', (e) => {
            if (!localStorage.getItem('theme')) {
                if (e.matches) {
                    document.documentElement.classList.add('dark');
                    this.updateThemeToggle(true);
                } else {
                    document.documentElement.classList.remove('dark');
                    this.updateThemeToggle(false);
                }
            }
        });
    },
    
    toggleDarkMode: function() {
        const isDark = document.documentElement.classList.toggle('dark');
        localStorage.setItem('theme', isDark ? 'dark' : 'light');
        this.updateThemeToggle(isDark);
    },
    
    updateThemeToggle: function(isDark) {
        const toggle = document.getElementById('theme-toggle');
        if (!toggle) return;
        
        if (isDark) {
            toggle.innerHTML = '<i class="fas fa-sun"></i>';
            toggle.setAttribute('title', 'Switch to Light Mode');
        } else {
            toggle.innerHTML = '<i class="fas fa-moon"></i>';
            toggle.setAttribute('title', 'Switch to Dark Mode');
        }
    },
    
    // ========== Animations ==========
    initAnimations: function() {
        this.setupScrollAnimations();
        this.setupLazyLoading();
    },
    
    setupScrollAnimations: function() {
        const animatedElements = document.querySelectorAll('.animate-on-scroll');
        
        const checkVisibility = () => {
            animatedElements.forEach(element => {
                const rect = element.getBoundingClientRect();
                const isVisible = (
                    rect.top <= (window.innerHeight || document.documentElement.clientHeight) * 0.8 &&
                    rect.bottom >= 0
                );
                
                if (isVisible) {
                    element.classList.add('visible');
                }
            });
        };
        
        // ตรวจสอบทันทีหลังโหลดเสร็จ
        checkVisibility();
        
        // ตรวจสอบเมื่อมีการเลื่อนหน้าจอ
        window.addEventListener('scroll', checkVisibility);
    },
    
    setupLazyLoading: function() {
        // ตรวจสอบหาภาพที่ต้องการโหลดแบบ lazy
        const lazyImages = document.querySelectorAll('.lazy-load');
        
        if ('IntersectionObserver' in window) {
            const imageObserver = new IntersectionObserver((entries, observer) => {
                entries.forEach(entry => {
                    if (entry.isIntersecting) {
                        const img = entry.target;
                        img.src = img.dataset.src;
                        img.classList.remove('lazy-load');
                        imageObserver.unobserve(img);
                    }
                });
            });
            
            lazyImages.forEach(img => {
                imageObserver.observe(img);
            });
        } else {
            // Fallback สำหรับเบราว์เซอร์เก่า
            let lazyLoadThrottleTimeout;
            
            function lazyLoad() {
                if (lazyLoadThrottleTimeout) {
                    clearTimeout(lazyLoadThrottleTimeout);
                }
                
                lazyLoadThrottleTimeout = setTimeout(() => {
                    const scrollTop = window.pageYOffset;
                    
                    lazyImages.forEach(img => {
                        if (img.offsetTop < window.innerHeight + scrollTop) {
                            img.src = img.dataset.src;
                            img.classList.remove('lazy-load');
                        }
                    });
                    
                    if (lazyImages.length === 0) {
                        document.removeEventListener('scroll', lazyLoad);
                        window.removeEventListener('resize', lazyLoad);
                        window.removeEventListener('orientationChange', lazyLoad);
                    }
                }, 20);
            }
            
            document.addEventListener('scroll', lazyLoad);
            window.addEventListener('resize', lazyLoad);
            window.addEventListener('orientationChange', lazyLoad);
        }
    }
};

// เริ่มต้นใช้งานเมื่อโหลดเสร็จ
document.addEventListener('DOMContentLoaded', () => {
    ThemeManager.initDarkMode();
    ThemeManager.initAnimations();
});
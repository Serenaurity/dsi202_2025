// Static/js/animations.js

// Handle Scroll Animations
document.addEventListener('DOMContentLoaded', function() {
    // Scroll animation for elements
    const animatedElements = document.querySelectorAll('.animate-on-scroll');
    
    const observer = new IntersectionObserver((entries) => {
        entries.forEach(entry => {
            if (entry.isIntersecting) {
                entry.target.classList.add('visible');
                observer.unobserve(entry.target);
            }
        });
    }, {
        threshold: 0.15,
        rootMargin: '0px 0px -50px 0px'
    });
    
    animatedElements.forEach(element => {
        observer.observe(element);
    });
    
    // Custom cursor
    const cursor = document.querySelector('.custom-cursor');
    if (cursor) {
        document.addEventListener('mousemove', (e) => {
            cursor.style.left = `${e.clientX}px`;
            cursor.style.top = `${e.clientY}px`;
        });
        
        // Change cursor size on interactive elements
        const interactiveElements = document.querySelectorAll('a, button, input, select, textarea, [role="button"]');
        interactiveElements.forEach(el => {
            el.addEventListener('mouseenter', () => {
                cursor.style.width = '40px';
                cursor.style.height = '40px';
                cursor.style.backgroundColor = 'rgba(255, 158, 122, 0.5)';
            });
            
            el.addEventListener('mouseleave', () => {
                cursor.style.width = '20px';
                cursor.style.height = '20px';
                cursor.style.backgroundColor = 'rgba(58, 189, 184, 0.5)';
            });
        });
        
        // Scale cursor on mousedown/mouseup
        document.addEventListener('mousedown', () => {
            cursor.style.transform = 'translate(-50%, -50%) scale(0.8)';
        });
        
        document.addEventListener('mouseup', () => {
            cursor.style.transform = 'translate(-50%, -50%) scale(1)';
        });
    }
    
    // Animate counters when they enter viewport
    const counters = document.querySelectorAll('[data-count]');
    const counterObserver = new IntersectionObserver((entries) => {
        entries.forEach(entry => {
            if (entry.isIntersecting) {
                const counter = entry.target;
                const target = parseInt(counter.getAttribute('data-count'));
                const duration = 2000; // milliseconds
                const increment = target / (duration / 16);
                let current = 0;
                
                const updateCounter = () => {
                    current += increment;
                    if (current < target) {
                        counter.textContent = Math.ceil(current);
                        requestAnimationFrame(updateCounter);
                    } else {
                        counter.textContent = target;
                    }
                };
                
                updateCounter();
                counterObserver.unobserve(counter);
            }
        });
    }, { threshold: 0.5 });
    
    counters.forEach(counter => {
        counterObserver.observe(counter);
    });
    
    // Initialize AlpineJS components
    // This will be handled by AlpineJS automatically, just ensuring it's working
    if (typeof Alpine !== 'undefined') {
        console.log('AlpineJS is loaded and ready');
    }
});
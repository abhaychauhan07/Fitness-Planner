console.log('Sporty UI ready');
// Chart rendering helper (expects canvas id and data)
function renderLineChart(id, labels, data, labelText){
    const ctx = document.getElementById(id);
    if(!ctx) return;
    const chartColors = {
        backgroundColor: 'rgba(125, 227, 178, 0.1)',
        borderColor: '#7DE3B2',
        pointBackgroundColor: '#7DE3B2',
        pointBorderColor: '#042018',
        pointHoverBackgroundColor: '#FF7A59',
        pointHoverBorderColor: '#fff'
    };
    new Chart(ctx, {
        type: 'line',
        data: {
            labels: labels,
            datasets: [{
                label: labelText,
                data: data,
                fill: true,
                tension: 0.4,
                backgroundColor: chartColors.backgroundColor,
                borderColor: chartColors.borderColor,
                borderWidth: 2,
                pointRadius: 4,
                pointBackgroundColor: chartColors.pointBackgroundColor,
                pointBorderColor: chartColors.pointBorderColor,
                pointBorderWidth: 2,
                pointHoverRadius: 6,
                pointHoverBackgroundColor: chartColors.pointHoverBackgroundColor,
                pointHoverBorderColor: chartColors.pointHoverBorderColor
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: true,
            plugins: {
                legend: {
                    display: false
                },
                tooltip: {
                    backgroundColor: 'rgba(15, 23, 36, 0.95)',
                    titleColor: '#7DE3B2',
                    bodyColor: '#e6eef8',
                    borderColor: '#7DE3B2',
                    borderWidth: 1,
                    padding: 12,
                    displayColors: false,
                    cornerRadius: 8
                }
            },
            scales: {
                y: {
                    beginAtZero: true,
                    grid: {
                        color: 'rgba(255, 255, 255, 0.05)',
                        drawBorder: false
                    },
                    ticks: {
                        color: '#9AA6B2',
                        font: {
                            size: 11
                        }
                    }
                },
                x: {
                    grid: {
                        color: 'rgba(255, 255, 255, 0.05)',
                        drawBorder: false
                    },
                    ticks: {
                        color: '#9AA6B2',
                        font: {
                            size: 11
                        }
                    }
                }
            },
            animation: {
                duration: 1500,
                easing: 'easeOutQuart'
            },
            interaction: {
                intersect: false,
                mode: 'index'
            }
        }
    });
}

// Enhanced form validation and feedback
document.addEventListener('DOMContentLoaded', function() {
    // Auto-hide flash messages after 5 seconds
    const flashMessages = document.querySelectorAll('.flashes li');
    flashMessages.forEach(msg => {
        setTimeout(() => {
            msg.style.transition = 'all 0.3s ease-out';
            msg.style.opacity = '0';
            msg.style.transform = 'translateX(20px)';
            setTimeout(() => msg.remove(), 300);
        }, 5000);
    });

    // Enhanced form inputs with validation feedback
    const formInputs = document.querySelectorAll('.form input, .form textarea, .form select');
    formInputs.forEach(input => {
        // Add focus/blur animations
        input.addEventListener('focus', function() {
            this.parentElement?.classList.add('focused');
        });
        input.addEventListener('blur', function() {
            this.parentElement?.classList.remove('focused');
            // Validate on blur
            if (this.hasAttribute('required') && !this.value.trim()) {
                this.style.borderColor = 'rgba(255, 122, 89, 0.5)';
            } else if (this.value.trim()) {
                this.style.borderColor = 'rgba(125, 227, 178, 0.5)';
            }
        });

        // Real-time validation for email
        if (input.type === 'email') {
            input.addEventListener('input', function() {
                const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
                if (this.value && !emailRegex.test(this.value)) {
                    this.style.borderColor = 'rgba(255, 122, 89, 0.5)';
                } else if (this.value) {
                    this.style.borderColor = 'rgba(125, 227, 178, 0.5)';
                }
            });
        }

        // Number inputs with increment/decrement hints
        if (input.type === 'number') {
            input.addEventListener('input', function() {
                if (this.value && parseFloat(this.value) > 0) {
                    this.style.borderColor = 'rgba(125, 227, 178, 0.5)';
                }
            });
        }
    });

    // Form submission with loading state
    const forms = document.querySelectorAll('form');
    forms.forEach(form => {
        form.addEventListener('submit', function(e) {
            const submitBtn = form.querySelector('button[type="submit"], .btn[type="submit"]');
            if (submitBtn) {
                const originalText = submitBtn.innerHTML;
                submitBtn.innerHTML = '<span class="spinner"></span> Submitting...';
                submitBtn.disabled = true;
                submitBtn.style.opacity = '0.7';
                submitBtn.style.cursor = 'not-allowed';
                
                // Re-enable if form fails to submit (client-side validation)
                setTimeout(() => {
                    if (!form.checkValidity()) {
                        submitBtn.innerHTML = originalText;
                        submitBtn.disabled = false;
                        submitBtn.style.opacity = '1';
                        submitBtn.style.cursor = 'pointer';
                    }
                }, 100);
            }
        });
    });

    // Smooth scroll for anchor links
    document.querySelectorAll('a[href^="#"]').forEach(anchor => {
        anchor.addEventListener('click', function(e) {
            const href = this.getAttribute('href');
            if (href !== '#' && href.length > 1) {
                const target = document.querySelector(href);
                if (target) {
                    e.preventDefault();
                    target.scrollIntoView({
                        behavior: 'smooth',
                        block: 'start'
                    });
                }
            }
        });
    });

    // Add click ripple effect to buttons
    document.querySelectorAll('.btn').forEach(btn => {
        btn.addEventListener('click', function(e) {
            const ripple = document.createElement('span');
            const rect = this.getBoundingClientRect();
            const size = Math.max(rect.width, rect.height);
            const x = e.clientX - rect.left - size / 2;
            const y = e.clientY - rect.top - size / 2;
            
            ripple.style.width = ripple.style.height = size + 'px';
            ripple.style.left = x + 'px';
            ripple.style.top = y + 'px';
            ripple.classList.add('ripple');
            
            this.appendChild(ripple);
            
            setTimeout(() => ripple.remove(), 600);
        });
    });

    // Animate cards on scroll (if IntersectionObserver is supported)
    if ('IntersectionObserver' in window) {
        const observerOptions = {
            threshold: 0.1,
            rootMargin: '0px 0px -50px 0px'
        };

        const observer = new IntersectionObserver((entries) => {
            entries.forEach(entry => {
                if (entry.isIntersecting) {
                    entry.target.style.opacity = '1';
                    entry.target.style.transform = 'translateY(0)';
                    observer.unobserve(entry.target);
                }
            });
        }, observerOptions);

        // Observe cards for scroll animation
        document.querySelectorAll('.card').forEach((card, index) => {
            card.style.opacity = '0';
            card.style.transform = 'translateY(20px)';
            card.style.transition = `opacity 0.5s ease-out ${index * 0.1}s, transform 0.5s ease-out ${index * 0.1}s`;
            observer.observe(card);
        });
    }

    // Enhanced list item interactions
    document.querySelectorAll('.list li').forEach(item => {
        item.addEventListener('mouseenter', function() {
            this.style.transition = 'all 0.2s ease';
        });
    });

    // Stats hover effect enhancement
    document.querySelectorAll('.stat').forEach(stat => {
        stat.addEventListener('mouseenter', function() {
            const value = this.querySelector('div[style*="font-weight:800"]');
            if (value) {
                value.style.transform = 'scale(1.1)';
                value.style.transition = 'transform 0.2s ease';
            }
        });
        stat.addEventListener('mouseleave', function() {
            const value = this.querySelector('div[style*="font-weight:800"]');
            if (value) {
                value.style.transform = 'scale(1)';
            }
        });
    });

    // Date input enhancement - set today as default if empty
    const dateInputs = document.querySelectorAll('input[type="date"]');
    dateInputs.forEach(input => {
        if (!input.value) {
            const today = new Date().toISOString().split('T')[0];
            input.value = today;
        }
    });

    // Add character counter for textareas
    const textareas = document.querySelectorAll('textarea[placeholder]');
    textareas.forEach(textarea => {
        const maxLength = textarea.getAttribute('maxlength') || 500;
        const counter = document.createElement('div');
        counter.className = 'small';
        counter.style.textAlign = 'right';
        counter.style.marginTop = '-8px';
        counter.style.marginBottom = '8px';
        textarea.parentNode.insertBefore(counter, textarea.nextSibling);
        
        function updateCounter() {
            const remaining = maxLength - textarea.value.length;
            counter.textContent = `${textarea.value.length}/${maxLength}`;
            counter.style.color = remaining < 50 ? '#FF7A59' : '#9AA6B2';
        }
        
        textarea.addEventListener('input', updateCounter);
        updateCounter();
    });

    // Navbar scroll effect
    let lastScroll = 0;
    const navbar = document.querySelector('.topbar');
    if (navbar) {
        window.addEventListener('scroll', () => {
            const currentScroll = window.pageYOffset;
            if (currentScroll > 100) {
                navbar.style.background = 'rgba(11, 15, 20, 0.95)';
                navbar.style.boxShadow = '0 2px 10px rgba(0, 0, 0, 0.3)';
            } else {
                navbar.style.background = 'rgba(11, 15, 20, 0.8)';
                navbar.style.boxShadow = 'none';
            }
            lastScroll = currentScroll;
        });
    }

    // Console welcome message
    console.log('%c🎯 FitPlanner Enhanced UI', 'color: #7DE3B2; font-size: 16px; font-weight: bold;');
    console.log('%cInteractive features loaded successfully!', 'color: #9AA6B2; font-size: 12px;');
});

// Ripple effect styles (injected dynamically)
const rippleStyle = document.createElement('style');
rippleStyle.textContent = `
    .btn {
        position: relative;
        overflow: hidden;
    }
    .ripple {
        position: absolute;
        border-radius: 50%;
        background: rgba(255, 255, 255, 0.3);
        transform: scale(0);
        animation: ripple-animation 0.6s ease-out;
        pointer-events: none;
    }
    @keyframes ripple-animation {
        to {
            transform: scale(4);
            opacity: 0;
        }
    }
`;
document.head.appendChild(rippleStyle);

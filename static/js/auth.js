// Authentication pages JavaScript functionality

document.addEventListener('DOMContentLoaded', function() {
    
    // Password strength checker
    const passwordInputs = document.querySelectorAll('input[type="password"]');
    
    passwordInputs.forEach(input => {
        if (input.name === 'password1' || input.name === 'password') {
            addPasswordStrengthChecker(input);
        }
    });
    
    // Form validation
    const forms = document.querySelectorAll('.auth-form');
    forms.forEach(form => {
        addFormValidation(form);
    });
    
    // Loading states for buttons
    const submitButtons = document.querySelectorAll('button[type="submit"]');
    submitButtons.forEach(button => {
        addLoadingState(button);
    });
    
    // Auto-focus first input
    const firstInput = document.querySelector('.auth-form input:first-of-type');
    if (firstInput) {
        firstInput.focus();
    }
});

function addPasswordStrengthChecker(input) {
    // Create strength indicator
    const strengthDiv = document.createElement('div');
    strengthDiv.className = 'password-strength';
    strengthDiv.innerHTML = '<div class="password-strength-bar"></div>';
    
    const strengthText = document.createElement('small');
    strengthText.className = 'form-text password-strength-text';
    strengthText.style.marginTop = '0.25rem';
    
    input.parentNode.appendChild(strengthDiv);
    input.parentNode.appendChild(strengthText);
    
    const strengthBar = strengthDiv.querySelector('.password-strength-bar');
    
    input.addEventListener('input', function() {
        const password = this.value;
        const strength = calculatePasswordStrength(password);
        
        // Remove previous strength classes
        strengthBar.classList.remove('password-strength-weak', 'password-strength-fair', 'password-strength-good', 'password-strength-strong');
        
        if (password.length === 0) {
            strengthBar.style.width = '0%';
            strengthText.textContent = '';
            return;
        }
        
        switch(strength.level) {
            case 1:
                strengthBar.classList.add('password-strength-weak');
                strengthText.textContent = 'Parolă slabă';
                strengthText.style.color = '#e53e3e';
                break;
            case 2:
                strengthBar.classList.add('password-strength-fair');
                strengthText.textContent = 'Parolă acceptabilă';
                strengthText.style.color = '#ed8936';
                break;
            case 3:
                strengthBar.classList.add('password-strength-good');
                strengthText.textContent = 'Parolă bună';
                strengthText.style.color = '#ecc94b';
                break;
            case 4:
                strengthBar.classList.add('password-strength-strong');
                strengthText.textContent = 'Parolă puternică';
                strengthText.style.color = '#48bb78';
                break;
        }
    });
}

function calculatePasswordStrength(password) {
    let score = 0;
    const checks = {
        length: password.length >= 8,
        lowercase: /[a-z]/.test(password),
        uppercase: /[A-Z]/.test(password),
        numbers: /\d/.test(password),
        special: /[^A-Za-z0-9]/.test(password)
    };
    
    // Length bonus
    if (password.length >= 8) score++;
    if (password.length >= 12) score++;
    
    // Character variety
    if (checks.lowercase) score++;
    if (checks.uppercase) score++;
    if (checks.numbers) score++;
    if (checks.special) score++;
    
    const level = Math.min(Math.max(Math.floor(score / 1.5), 1), 4);
    
    return { score, level, checks };
}

function addFormValidation(form) {
    const inputs = form.querySelectorAll('input[required]');
    
    inputs.forEach(input => {
        input.addEventListener('blur', function() {
            validateField(this);
        });
        
        input.addEventListener('input', function() {
            if (this.classList.contains('is-invalid')) {
                validateField(this);
            }
        });
    });
    
    form.addEventListener('submit', function(e) {
        let isValid = true;
        
        inputs.forEach(input => {
            if (!validateField(input)) {
                isValid = false;
            }
        });
        
        // Check password confirmation
        const password1 = form.querySelector('input[name="password1"]');
        const password2 = form.querySelector('input[name="password2"]');
        
        if (password1 && password2) {
            if (password1.value !== password2.value) {
                showFieldError(password2, 'Parolele nu se potrivesc');
                isValid = false;
            }
        }
        
        if (!isValid) {
            e.preventDefault();
        }
    });
}

function validateField(field) {
    const value = field.value.trim();
    let isValid = true;
    
    // Clear previous errors
    clearFieldError(field);
    
    if (field.hasAttribute('required') && !value) {
        showFieldError(field, 'Acest câmp este obligatoriu');
        isValid = false;
    } else if (field.type === 'email' && value && !isValidEmail(value)) {
        showFieldError(field, 'Adresa de email nu este validă');
        isValid = false;
    } else if (field.name === 'password1' && value && value.length < 8) {
        showFieldError(field, 'Parola trebuie să aibă cel puțin 8 caractere');
        isValid = false;
    }
    
    if (isValid) {
        field.classList.remove('is-invalid');
        field.classList.add('is-valid');
    }
    
    return isValid;
}

function showFieldError(field, message) {
    field.classList.add('is-invalid');
    field.classList.remove('is-valid');
    
    let errorDiv = field.parentNode.querySelector('.field-errors');
    if (!errorDiv) {
        errorDiv = document.createElement('div');
        errorDiv.className = 'field-errors';
        field.parentNode.appendChild(errorDiv);
    }
    
    errorDiv.innerHTML = `<span>${message}</span>`;
}

function clearFieldError(field) {
    const errorDiv = field.parentNode.querySelector('.field-errors');
    if (errorDiv) {
        errorDiv.remove();
    }
    field.classList.remove('is-invalid', 'is-valid');
}

function isValidEmail(email) {
    const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
    return emailRegex.test(email);
}

function addLoadingState(button) {
    const form = button.closest('form');
    
    form.addEventListener('submit', function() {
        button.classList.add('loading');
        button.disabled = true;
        
        // Re-enable button after 5 seconds as fallback
        setTimeout(() => {
            button.classList.remove('loading');
            button.disabled = false;
        }, 5000);
    });
}

// Show/hide password functionality
function togglePasswordVisibility(inputId) {
    const input = document.getElementById(inputId);
    const icon = input.parentNode.querySelector('.password-toggle-icon');
    
    if (input.type === 'password') {
        input.type = 'text';
        icon.classList.remove('fa-eye');
        icon.classList.add('fa-eye-slash');
    } else {
        input.type = 'password';
        icon.classList.remove('fa-eye-slash');
        icon.classList.add('fa-eye');
    }
}

// Auto-hide messages after 5 seconds
document.addEventListener('DOMContentLoaded', function() {
    const messages = document.querySelectorAll('.auth-messages .auth-message');
    messages.forEach(message => {
        setTimeout(() => {
            message.style.transition = 'opacity 0.5s ease';
            message.style.opacity = '0';
            setTimeout(() => message.remove(), 500);
        }, 5000);
    });
});

// static/js/react-login.js - React Login Component
const { useState, useEffect } = React;

// Login Component
const LoginComponent = () => {
    const [formData, setFormData] = useState({
        identifier: '',
        password: ''
    });
    const [loading, setLoading] = useState(false);
    const [error, setError] = useState('');
    const [showPassword, setShowPassword] = useState(false);

    const handleSubmit = async (e) => {
        e.preventDefault();
        setLoading(true);
        setError('');

        try {
            const response = await fetch('/api/auth/login/', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'X-CSRFToken': getCookie('csrftoken')
                },
                body: JSON.stringify(formData)
            });

            const data = await response.json();

            if (data.success) {
                // Redirect to dashboard or membership page
                window.location.href = '/dashboard/';
            } else {
                setError(data.message);
            }
        } catch (err) {
            setError('Network error. Please try again.');
        } finally {
            setLoading(false);
        }
    };

    const handleInputChange = (e) => {
        setFormData({
            ...formData,
            [e.target.name]: e.target.value
        });
    };

    const handleGoogleLogin = () => {
        window.location.href = '/auth/login/google-oauth2/';
    };

    return React.createElement('div', { className: 'auth-container' },
        React.createElement('div', { className: 'auth-card' },
            // Header
            React.createElement('div', { className: 'auth-header' },
                React.createElement('h2', null,
                    React.createElement('i', { className: 'fas fa-user-circle me-2' }),
                    'Welcome Back'
                ),
                React.createElement('p', null, 'Sign in to your BMR Membership account')
            ),

            // Error Alert
            error && React.createElement('div', {
                className: 'alert alert-danger alert-dismissible fade show',
                role: 'alert'
            },
                error,
                React.createElement('button', {
                    type: 'button',
                    className: 'btn-close',
                    onClick: () => setError('')
                })
            ),

            // Login Form
            React.createElement('form', { onSubmit: handleSubmit },
                React.createElement('div', { className: 'mb-3' },
                    React.createElement('label', {
                        htmlFor: 'identifier',
                        className: 'form-label'
                    },
                        React.createElement('i', { className: 'fas fa-user me-2' }),
                        'Username or Email'
                    ),
                    React.createElement('input', {
                        type: 'text',
                        className: 'form-control',
                        id: 'identifier',
                        name: 'identifier',
                        placeholder: 'Enter your username or email',
                        value: formData.identifier,
                        onChange: handleInputChange,
                        required: true,
                        autoFocus: true
                    })
                ),

                React.createElement('div', { className: 'mb-3' },
                    React.createElement('label', {
                        htmlFor: 'password',
                        className: 'form-label'
                    },
                        React.createElement('i', { className: 'fas fa-lock me-2' }),
                        'Password'
                    ),
                    React.createElement('div', { className: 'position-relative' },
                        React.createElement('input', {
                            type: showPassword ? 'text' : 'password',
                            className: 'form-control',
                            id: 'password',
                            name: 'password',
                            placeholder: 'Enter your password',
                            value: formData.password,
                            onChange: handleInputChange,
                            required: true
                        }),
                        React.createElement('button', {
                            type: 'button',
                            className: 'btn btn-link position-absolute end-0 top-50 translate-middle-y',
                            onClick: () => setShowPassword(!showPassword)
                        },
                            React.createElement('i', {
                                className: showPassword ? 'fas fa-eye-slash' : 'fas fa-eye'
                            })
                        )
                    )
                ),

                React.createElement('button', {
                    type: 'submit',
                    className: 'btn btn-primary w-100 mb-3',
                    disabled: loading
                },
                    loading ? React.createElement('span', null,
                        React.createElement('i', { className: 'fas fa-spinner fa-spin me-2' }),
                        'Signing in...'
                    ) : React.createElement('span', null,
                        React.createElement('i', { className: 'fas fa-sign-in-alt me-2' }),
                        'Sign In'
                    )
                )
            ),

            // Divider
            React.createElement('div', { className: 'divider' },
                React.createElement('span', null, 'or')
            ),

            // Google Login
            React.createElement('button', {
                type: 'button',
                className: 'btn btn-outline-danger w-100 mb-3',
                onClick: handleGoogleLogin
            },
                React.createElement('i', { className: 'fab fa-google me-2' }),
                'Continue with Google'
            ),

            // Links
            React.createElement('div', { className: 'auth-links' },
                React.createElement('p', null,
                    "Don't have an account? ",
                    React.createElement('a', { href: '/auth/register/' }, 'Register here')
                ),
                React.createElement('p', null,
                    React.createElement('a', { href: '/auth/forgot-password/' }, 'Forgot your password?')
                )
            )
        )
    );
};

// Register Component
const RegisterComponent = () => {
    const [formData, setFormData] = useState({
        username: '',
        email: '',
        password: '',
        confirm_password: ''
    });
    const [loading, setLoading] = useState(false);
    const [error, setError] = useState('');
    const [showPassword, setShowPassword] = useState(false);
    const [showConfirmPassword, setShowConfirmPassword] = useState(false);
    const [passwordStrength, setPasswordStrength] = useState(0);

    const calculatePasswordStrength = (password) => {
        let strength = 0;
        if (password.length >= 8) strength++;
        if (/[A-Z]/.test(password)) strength++;
        if (/[0-9]/.test(password)) strength++;
        if (/[^A-Za-z0-9]/.test(password)) strength++;
        return strength;
    };

    const handleSubmit = async (e) => {
        e.preventDefault();
        setLoading(true);
        setError('');

        if (formData.password !== formData.confirm_password) {
            setError('Passwords do not match');
            setLoading(false);
            return;
        }

        try {
            const response = await fetch('/api/auth/register/', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'X-CSRFToken': getCookie('csrftoken')
                },
                body: JSON.stringify(formData)
            });

            const data = await response.json();

            if (data.success) {
                // Redirect to OTP verification
                window.location.href = '/auth/verify-otp/';
            } else {
                setError(data.message);
            }
        } catch (err) {
            setError('Network error. Please try again.');
        } finally {
            setLoading(false);
        }
    };

    const handleInputChange = (e) => {
        const { name, value } = e.target;
        setFormData({
            ...formData,
            [name]: value
        });

        if (name === 'password') {
            setPasswordStrength(calculatePasswordStrength(value));
        }
    };

    const getStrengthColor = () => {
        if (passwordStrength < 2) return 'strength-weak';
        if (passwordStrength < 4) return 'strength-medium';
        return 'strength-strong';
    };

    const getStrengthText = () => {
        if (passwordStrength < 2) return 'Weak';
        if (passwordStrength < 4) return 'Medium';
        return 'Strong';
    };

    return React.createElement('div', { className: 'auth-container' },
        React.createElement('div', { className: 'auth-card' },
            // Header
            React.createElement('div', { className: 'auth-header' },
                React.createElement('h2', null,
                    React.createElement('i', { className: 'fas fa-user-plus me-2' }),
                    'Create Account'
                ),
                React.createElement('p', null, 'Join BMR Membership today')
            ),

            // Error Alert
            error && React.createElement('div', {
                className: 'alert alert-danger alert-dismissible fade show',
                role: 'alert'
            },
                error,
                React.createElement('button', {
                    type: 'button',
                    className: 'btn-close',
                    onClick: () => setError('')
                })
            ),

            // Registration Form
            React.createElement('form', { onSubmit: handleSubmit },
                // Username
                React.createElement('div', { className: 'mb-3' },
                    React.createElement('label', {
                        htmlFor: 'username',
                        className: 'form-label'
                    },
                        React.createElement('i', { className: 'fas fa-user me-2' }),
                        'Username'
                    ),
                    React.createElement('input', {
                        type: 'text',
                        className: 'form-control',
                        id: 'username',
                        name: 'username',
                        placeholder: 'Choose a username',
                        value: formData.username,
                        onChange: handleInputChange,
                        pattern: '^[a-zA-Z0-9]*,
                        required: true
                    }),
                    React.createElement('small', { className: 'text-muted' },
                        'Letters and numbers only, no spaces or special characters.'
                    )
                ),

                // Email
                React.createElement('div', { className: 'mb-3' },
                    React.createElement('label', {
                        htmlFor: 'email',
                        className: 'form-label'
                    },
                        React.createElement('i', { className: 'fas fa-envelope me-2' }),
                        'Email'
                    ),
                    React.createElement('input', {
                        type: 'email',
                        className: 'form-control',
                        id: 'email',
                        name: 'email',
                        placeholder: 'Enter your email',
                        value: formData.email,
                        onChange: handleInputChange,
                        required: true
                    })
                ),

                // Password
                React.createElement('div', { className: 'mb-3' },
                    React.createElement('label', {
                        htmlFor: 'password',
                        className: 'form-label'
                    },
                        React.createElement('i', { className: 'fas fa-lock me-2' }),
                        'Password'
                    ),
                    React.createElement('div', { className: 'position-relative' },
                        React.createElement('input', {
                            type: showPassword ? 'text' : 'password',
                            className: 'form-control',
                            id: 'password',
                            name: 'password',
                            placeholder: 'Create a password',
                            value: formData.password,
                            onChange: handleInputChange,
                            required: true
                        }),
                        React.createElement('button', {
                            type: 'button',
                            className: 'btn btn-link position-absolute end-0 top-50 translate-middle-y',
                            onClick: () => setShowPassword(!showPassword)
                        },
                            React.createElement('i', {
                                className: showPassword ? 'fas fa-eye-slash' : 'fas fa-eye'
                            })
                        )
                    ),
                    React.createElement('div', { className: 'strength-meter' },
                        React.createElement('div', {
                            className: `strength-bar ${getStrengthColor()}`,
                            style: { width: `${(passwordStrength / 4) * 100}%` }
                        })
                    ),
                    React.createElement('small', { className: 'text-muted' },
                        `Password strength: ${getStrengthText()}`
                    )
                ),

                // Confirm Password
                React.createElement('div', { className: 'mb-3' },
                    React.createElement('label', {
                        htmlFor: 'confirm_password',
                        className: 'form-label'
                    },
                        React.createElement('i', { className: 'fas fa-lock me-2' }),
                        'Confirm Password'
                    ),
                    React.createElement('div', { className: 'position-relative' },
                        React.createElement('input', {
                            type: showConfirmPassword ? 'text' : 'password',
                            className: 'form-control',
                            id: 'confirm_password',
                            name: 'confirm_password',
                            placeholder: 'Confirm your password',
                            value: formData.confirm_password,
                            onChange: handleInputChange,
                            required: true
                        }),
                        React.createElement('button', {
                            type: 'button',
                            className: 'btn btn-link position-absolute end-0 top-50 translate-middle-y',
                            onClick: () => setShowConfirmPassword(!showConfirmPassword)
                        },
                            React.createElement('i', {
                                className: showConfirmPassword ? 'fas fa-eye-slash' : 'fas fa-eye'
                            })
                        )
                    ),
                    formData.confirm_password && React.createElement('small', {
                        className: formData.password === formData.confirm_password ? 'text-success' : 'text-danger'
                    },
                        formData.password === formData.confirm_password ? '✓ Passwords match' : '✗ Passwords do not match'
                    )
                ),

                React.createElement('button', {
                    type: 'submit',
                    className: 'btn btn-primary w-100 mb-3',
                    disabled: loading
                },
                    loading ? React.createElement('span', null,
                        React.createElement('i', { className: 'fas fa-spinner fa-spin me-2' }),
                        'Creating Account...'
                    ) : React.createElement('span', null,
                        React.createElement('i', { className: 'fas fa-user-plus me-2' }),
                        'Create Account'
                    )
                )
            ),

            // Divider
            React.createElement('div', { className: 'divider' },
                React.createElement('span', null, 'or')
            ),

            // Google Registration
            React.createElement('a', {
                href: '/auth/login/google-oauth2/',
                className: 'btn btn-outline-danger w-100 mb-3'
            },
                React.createElement('i', { className: 'fab fa-google me-2' }),
                'Sign up with Google'
            ),

            // Links
            React.createElement('div', { className: 'auth-links' },
                React.createElement('p', null,
                    "Already have an account? ",
                    React.createElement('a', { href: '/auth/login/' }, 'Sign in here')
                )
            )
        )
    );
};

// Utility function to get CSRF token
function getCookie(name) {
    let cookieValue = null;
    if (document.cookie && document.cookie !== '') {
        const cookies = document.cookie.split(';');
        for (let i = 0; i < cookies.length; i++) {
            const cookie = cookies[i].trim();
            if (cookie.substring(0, name.length + 1) === (name + '=')) {
                cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
                break;
            }
        }
    }
    return cookieValue;
}

// Render functions
function renderReactLogin() {
    const container = document.getElementById('react-login-container');
    if (container) {
        ReactDOM.render(React.createElement(LoginComponent), container);
    }
}

function renderReactRegister() {
    const container = document.getElementById('react-register-container');
    if (container) {
        ReactDOM.render(React.createElement(RegisterComponent), container);
    }
}

// Auto-initialize if containers exist
document.addEventListener('DOMContentLoaded', function() {
    if (document.getElementById('react-login-container')) {
        renderReactLogin();
    }
    if (document.getElementById('react-register-container')) {
        renderReactRegister();
    }
});
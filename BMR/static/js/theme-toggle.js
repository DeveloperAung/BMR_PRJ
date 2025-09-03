// Dark/Light mode toggle logic
(function() {
  const body = document.body;
  const toggleBtn = document.getElementById('theme-toggle');
  const icon = document.getElementById('theme-toggle-icon');
  const darkClass = 'dark-mode';

  // Set icon according to mode
  function setIcon(isDark) {
    if (isDark) {
      icon.classList.remove('fa-moon');
      icon.classList.add('fa-sun');
    } else {
      icon.classList.remove('fa-sun');
      icon.classList.add('fa-moon');
    }
  }

  // Load mode from localStorage
  function loadMode() {
    const mode = localStorage.getItem('theme-mode');
    if (mode === 'dark') {
      body.classList.add(darkClass);
      setIcon(true);
    } else {
      body.classList.remove(darkClass);
      setIcon(false);
    }
  }

  // Toggle mode
  function toggleMode() {
    const isDark = body.classList.toggle(darkClass);
    localStorage.setItem('theme-mode', isDark ? 'dark' : 'light');
    setIcon(isDark);
  }

  if (toggleBtn && icon) {
    toggleBtn.addEventListener('click', toggleMode);
    loadMode();
  }
})();

// For list-products.html dark mode toggle
(function() {
  const body = document.body;
  const darkToggle = document.querySelector('.dark-mode');
  const darkClass = 'dark-mode';

  function setMode(isDark) {
    if (isDark) {
      body.classList.add(darkClass);
    } else {
      body.classList.remove(darkClass);
    }
  }

  // Load mode from localStorage
  function loadMode() {
    const mode = localStorage.getItem('theme-mode');
    setMode(mode === 'dark');
  }

  // Toggle mode
  function toggleMode() {
    const isDark = !body.classList.contains(darkClass);
    setMode(isDark);
    localStorage.setItem('theme-mode', isDark ? 'dark' : 'light');
  }

  if (darkToggle) {
    darkToggle.addEventListener('click', function(e) {
      e.preventDefault();
      toggleMode();
    });
    loadMode();
  }
})(); 
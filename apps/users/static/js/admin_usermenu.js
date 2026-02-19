/**
 * Make the Admin top-right person icon go directly to the app profile page.
 * (The dropdown was navigating to #; this ensures a reliable link.)
 */
(function() {
  function init() {
    var nav = document.getElementById('jazzy-navbar');
    if (!nav) return;
    var userDropdown = nav.querySelector('.nav-item.dropdown .nav-link[data-toggle="dropdown"]');
    if (!userDropdown) return;
    userDropdown.removeAttribute('data-toggle');
    userDropdown.removeAttribute('aria-haspopup');
    userDropdown.removeAttribute('aria-expanded');
    userDropdown.href = '/profile/';
    userDropdown.title = 'Profile';
    userDropdown.setAttribute('role', 'link');
  }
  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', init);
  } else {
    init();
  }
})();

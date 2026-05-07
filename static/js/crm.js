/* EdTech CRM — Main JS */

// Sidebar toggle for mobile
function toggleSidebar() {
  document.querySelector('.sidebar').classList.toggle('open');
}

// Close sidebar when clicking outside on mobile
document.addEventListener('click', function (e) {
  const sidebar = document.querySelector('.sidebar');
  if (!sidebar) return;
  const toggle = document.querySelector('.sidebar-toggle');
  if (sidebar.classList.contains('open') &&
      !sidebar.contains(e.target) &&
      e.target !== toggle) {
    sidebar.classList.remove('open');
  }
});

// Auto-dismiss alerts after 5 seconds
document.addEventListener('DOMContentLoaded', function () {
  document.querySelectorAll('.alert').forEach(function (alert) {
    setTimeout(function () {
      alert.style.transition = 'opacity .4s';
      alert.style.opacity = '0';
      setTimeout(function () { alert.remove(); }, 400);
    }, 5000);
  });

  // Mark active sidebar link based on current path
  const path = window.location.pathname;
  document.querySelectorAll('.nav-links a').forEach(function (link) {
    if (link.getAttribute('href') === path) {
      link.classList.add('active');
    }
  });
});

/* Diario di Cantiere – main.js */

document.addEventListener('DOMContentLoaded', function () {

  // ── Sidebar mobile toggle ─────────────────────────────────────────────────
  const sidebar = document.getElementById('sidebar');
  const overlay = document.getElementById('sidebar-overlay');
  const toggleBtn = document.getElementById('sidebar-toggle');

  function openSidebar() {
    sidebar && sidebar.classList.add('show');
    overlay && overlay.classList.add('show');
  }

  function closeSidebar() {
    sidebar && sidebar.classList.remove('show');
    overlay && overlay.classList.remove('show');
  }

  toggleBtn && toggleBtn.addEventListener('click', openSidebar);
  overlay && overlay.addEventListener('click', closeSidebar);

  // ── Aggiornamento ambienti dinamico nel form giornata ─────────────────────
  const cantiereSelect = document.getElementById('id_cantiere');
  const ambientiContainer = document.getElementById('ambienti-checkboxes');

  if (cantiereSelect && ambientiContainer) {
    cantiereSelect.addEventListener('change', function () {
      const cantiereId = this.value;
      if (!cantiereId) {
        ambientiContainer.innerHTML = '<p class="text-muted small">Seleziona prima un cantiere.</p>';
        return;
      }
      fetch(`/diario/api/ambienti/?cantiere_id=${cantiereId}`)
        .then(r => r.json())
        .then(data => {
          if (data.ambienti.length === 0) {
            ambientiContainer.innerHTML = '<p class="text-muted small">Nessun ambiente registrato per questo cantiere.</p>';
            return;
          }
          // Ricostruisce i checkbox
          const checks = data.ambienti.map(a => `
            <div class="form-check form-check-inline">
              <input class="form-check-input" type="checkbox"
                     name="ambienti" value="${a.id}" id="amb_${a.id}">
              <label class="form-check-label" for="amb_${a.id}">
                ${a.nome}${a.piano_zona ? ' <small class="text-muted">(' + a.piano_zona + ')</small>' : ''}
              </label>
            </div>
          `).join('');
          ambientiContainer.innerHTML = checks;
        })
        .catch(() => {
          ambientiContainer.innerHTML = '<p class="text-danger small">Errore nel caricamento ambienti.</p>';
        });
    });
  }

  // ── Auto-dismiss messaggi flash ───────────────────────────────────────────
  setTimeout(function () {
    document.querySelectorAll('.alert-dismissible.auto-dismiss').forEach(el => {
      const bsAlert = bootstrap.Alert.getInstance(el) || new bootstrap.Alert(el);
      bsAlert.close();
    });
  }, 4000);

  // ── Conferma eliminazione ─────────────────────────────────────────────────
  document.querySelectorAll('[data-confirm]').forEach(btn => {
    btn.addEventListener('click', function (e) {
      if (!confirm(this.dataset.confirm || 'Confermi l\'eliminazione?')) {
        e.preventDefault();
      }
    });
  });

  // ── Toggle conferma attività (AJAX) ───────────────────────────────────────
  document.querySelectorAll('.btn-conferma-attivita').forEach(btn => {
    btn.addEventListener('click', function (e) {
      e.preventDefault();
      const url = this.dataset.url;
      const row = this.closest('tr');
      fetch(url, {
        method: 'POST',
        headers: {
          'X-CSRFToken': getCookie('csrftoken'),
          'X-Requested-With': 'XMLHttpRequest',
        }
      })
      .then(r => r.json())
      .then(data => {
        if (data.confermata) {
          this.classList.replace('btn-outline-success', 'btn-success');
          this.textContent = '✓ Confermata';
          row && row.classList.remove('table-warning');
        } else {
          this.classList.replace('btn-success', 'btn-outline-success');
          this.textContent = 'Conferma';
          row && row.classList.add('table-warning');
        }
      });
    });
  });

  function getCookie(name) {
    let cookieValue = null;
    if (document.cookie && document.cookie !== '') {
      document.cookie.split(';').forEach(cookie => {
        const c = cookie.trim();
        if (c.startsWith(name + '=')) {
          cookieValue = decodeURIComponent(c.substring(name.length + 1));
        }
      });
    }
    return cookieValue;
  }

});

/* Quick-create: "+" buttons open a child modal on top of the parent.
   On AJAX submit success, the new option is added to the parent dropdown. */
let quickCreateTarget = null;

function openQuickCreate(modalId, targetSelectId) {
  quickCreateTarget = targetSelectId;
  const modal = document.getElementById(modalId);
  const sel = modal.querySelector('select');
  if (sel) { sel.value = ''; sel.dispatchEvent(new Event('change')); }
  openModal(modalId);
}

function handleQuickCreateSubmit(form) {
  if (!quickCreateTarget) return true;

  const formData = new FormData(form);
  fetch(form.action, {
    method: 'POST',
    headers: { 'X-Requested-With': 'XMLHttpRequest' },
    body: formData
  })
  .then(r => r.json())
  .then(data => {
    if (data.success) {
      const select = document.getElementById(quickCreateTarget);
      const opt = new Option(data.name, data.id, true, true);
      select.appendChild(opt);
      closeModal(form.closest('.modal-backdrop'));
      quickCreateTarget = null;
    } else {
      alert('Error: ' + (data.message || 'Creation failed'));
    }
  })
  .catch(() => alert('Error creating item'));

  return false;
}

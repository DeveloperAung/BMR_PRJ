// static/assets/js/sweetalert/swal-table-actions.js
document.addEventListener('DOMContentLoaded', function() {
    // SweetAlert2 for delete/restore
    function sweetConfirm(form, title, text, icon) {
      event.preventDefault();
      Swal.fire({
        title: title,
        text: text,
        icon: icon,
        showCancelButton: true,
        confirmButtonColor: '#2e8e87',
        cancelButtonColor: '#C42A02',
        confirmButtonText: 'Yes',
        reverseButtons: true
      }).then((result) => {
        if (result.isConfirmed) {
          form.submit();
        }
      });
    }
    // Single delete
    document.querySelectorAll('.delete-form').forEach(form => {
      form.addEventListener('submit', function(event) {
        sweetConfirm(form, 'Are you sure?', "You won't be able to revert this!", 'warning');
      });
    });
    // Single restore
    document.querySelectorAll('.restore-form').forEach(form => {
      form.addEventListener('submit', function(event) {
        sweetConfirm(form, 'Restore?', "This will restore the item.", 'info');
      });
    });
    // Bulk action
    const bulkForm = document.getElementById('bulk-action-form');
    if (bulkForm) {
      bulkForm.addEventListener('submit', function(event) {
        const action = bulkForm.querySelector('select[name="action"]').value;
        if (!action) {
          event.preventDefault();
          Swal.fire('Please select an action!', '', 'warning');
          return;
        }
        const checked = bulkForm.querySelectorAll('.bulk-checkbox:checked');
        if (checked.length === 0) {
          event.preventDefault();
          Swal.fire('Please select at least one item!', '', 'warning');
          return;
        }
        let title = action === 'delete' ? 'Delete selected items?' : 'Restore selected items?';
        let text = action === 'delete' ? "You won't be able to revert this!" : "This will restore the selected items.";
        let icon = action === 'delete' ? 'warning' : 'info';
        sweetConfirm(bulkForm, title, text, icon);
      });
    }
  });
const activates = Array.from(document.getElementsByClassName("activate-card"))
activates.forEach(activate => {
  activate.addEventListener("click", e=> {
    const token = activate.id;
    $.ajax({
      url: `/api/confirm?token=${token}`,
      type: "GET",
      success: (response) => {
        showToast("Activated card", response);
      }, 
      error: (response) => {
        showToast("Card activation failed", response.response);
      }
    });
  })
});

const delete_buttons = Array.from(document.getElementsByClassName("delete-card"))
delete_buttons.forEach(btn => {
  btn.addEventListener("click", e => {
    const token = btn.getAttribute("data-card-uuid");
    $.ajax({
      url: `/api/card?uuid=${token}`,
      type: "DELETE",
      beforeSend: function(xhr) {
        xhr.setRequestHeader("X-CSRFToken", csrf_token);
      },
      success: (_response) => {
        showToast("Deleted card", "Card successfully deleted");
        const row = btn.parentElement.parentElement;
        row.parentElement.removeChild(row);
      }, 
      error: (response) => {
        showToast("Card deletion failed", response.response);
      }
    });
  })
});

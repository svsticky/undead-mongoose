const confirm_charge = document.getElementById("confirm-charge");
if (confirm_charge) {
  confirm_charge.addEventListener("click", e => {
    const amount = document.getElementById("amount").value;
    const user = document.getElementById("user").value;
    const type = document.getElementById("type").value;

    $.ajax({
      url: `/api/balance`,
      data: {
        "csrfmiddlewaretoken": csrf_token,
        "user": user,
        "type": type,
        "balance": amount
      },
      type: "POST",
      success: (response) => {
        showToast("Updated balance", response.msg);
      }, 
      error: (response) => {
        showToast("Updated balance - Failed", response.responseJSON.msg);
      }
    });
  });
}

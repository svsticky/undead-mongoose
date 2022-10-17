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

const csrf_token = document.getElementsByName("csrfmiddlewaretoken")[0].value;
const toast_element = document.querySelector('.toast');
const toast = new bootstrap.Toast(toast_element);
const modal_element = document.querySelector('#confirm-modal');
const modal = new bootstrap.Modal(modal_element);

// Set menu button to active
const route = window.location.pathname.split("/")[1];
document.querySelectorAll(`a[href='/${route}']`)[0].classList.add("active");

// Show toast
function showToast(title, body) {
  document.getElementById("toast-title").innerHTML = title
  document.getElementById("toast-body").innerHTML = body
  toast.show();
}

document.getElementById("confirm-func").addEventListener("click", e => {
  if (document.getElementById("confirm-title").innerHTML.indexOf("VAT") != -1)
    delete_vat(document.getElementById("confirm-title").name)
  else if (document.getElementById("confirm-title").innerHTML.indexOf("category") != -1)
    delete_category(document.getElementById("confirm-title").name)
  else if (document.getElementById("confirm-title").innerHTML.indexOf("product") != -1)
    delete_product(document.getElementById("confirm-title").name)

  modal.hide()
});

function showConfirmation(title, body, id) {
  document.getElementById("confirm-title").innerHTML = title
  document.getElementById("confirm-title").name = id
  document.getElementById("confirm-body").innerHTML = body
  modal.show();
}

// Show user page
const showUser = document.getElementById("show-user");
if (showUser) { 
  document.getElementById("show-user").addEventListener("click", e => {
    const name = document.getElementById("user").value;
    const user_options = document.getElementById("userOptions");
    const selected_user = user_options.querySelector(`[value='${name}']`);
    if (!selected_user) {
      showToast("Show user - Failed", "User not found");
    } else {
      const userId = selected_user.id;
      window.location = `/users/${userId}`;
    }
  });
}

const confirm_charge = document.getElementById("confirm-charge");
if (confirm_charge) {
  confirm_charge.addEventListener("click", e => {
    const amount = document.getElementById("amount").value;
    const user = document.getElementById("user").value || document.getElementById("user").innerHTML;
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

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

const edit_buttons = Array.from(document.getElementsByClassName("edit-card"));
edit_buttons.forEach(btn => {
  btn.addEventListener("click", () => {
    const uuid = btn.parentElement.parentElement.getAttribute("data-card-uuid");
    const td = document.querySelector(`tr[data-card-uuid="${uuid}"]`).querySelector(".edit-td");
    const card_name = td.getAttribute("card_name");

    const input = document.createElement("input");
    input.type = "text";
    input.value = card_name;
    input.style.maxWidth = "70px";

    td.innerHTML = "";
    td.appendChild(input);

    const par = btn.parentElement;
    par.removeChild(btn);
    const save = document.createElement("button");
    save.appendChild(document.createTextNode("Save"));
    save.className = "btn btn-success save-card";
    save.addEventListener("click", () => {
      td.innerHTML = input.value;

      $.ajax({
        url: `/api/cardname?card_uuid=${uuid}&name=${input.value}`,
        type: "POST",
        beforeSend: function(xhr) {
          xhr.setRequestHeader("X-CSRFToken", csrf_token);
        },
        success: (response) => {
          showToast("Renamed card", response);
        }, 
        error: (response) => {
          console.log(response);
          showToast("Card renaming failed", response.response);
        }
      });

      par.removeChild(save);
      par.appendChild(btn);
    })
    par.appendChild(save);
  });
});
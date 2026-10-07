const activationButtons = Array.from(document.getElementsByClassName("activate-card"));

activationButtons.forEach((activateButton) => {
  activateButton.addEventListener("click", () => {
    const token = activateButton.id;
    activateButton.disabled = true;

    $.ajax({
      url: `/api/confirm?token=${encodeURIComponent(token)}`,
      type: "GET",
      success: (response) => {
        showToast("Pas geactiveerd", response);
      },
      error: (response) => {
        activateButton.disabled = false;
        showToast("Activeren van pas mislukt", response.response);
      },
    });
  });
});

const cardsList = document.querySelector("[data-cards-list]");
const cardCount = document.querySelector("[data-card-count]");
const clientEmptyState = document.querySelector(".cards-empty-client");
const serverEmptyState = document.querySelector(".cards-empty-server");

function updateCardState() {
  const cards = cardsList
    ? Array.from(cardsList.querySelectorAll(".js-card-item"))
    : [];

  if (cardCount) {
    cardCount.textContent = String(cards.length);
  }

  if (clientEmptyState && !serverEmptyState) {
    clientEmptyState.classList.toggle("hidden-item", cards.length !== 0);
  }
}

const deleteButtons = Array.from(document.getElementsByClassName("delete-card"));

deleteButtons.forEach((button) => {
  button.addEventListener("click", () => {
    const card = button.closest("[data-card-uuid]");
    if (!card) {
      return;
    }

    const uuid = card.getAttribute("data-card-uuid");
    button.disabled = true;

    $.ajax({
      url: `/api/card?uuid=${encodeURIComponent(uuid)}`,
      type: "DELETE",
      beforeSend: (xhr) => {
        xhr.setRequestHeader("X-CSRFToken", csrf_token);
      },
      success: () => {
        showToast("Pas ontkoppeld", "De pas is succesvol ontkoppeld.");
        card.remove();
        updateCardState();
      },
      error: (response) => {
        button.disabled = false;
        showToast("Ontkoppelen mislukt", response.response);
      },
    });
  });
});

function createIcon(name) {
  const icon = document.createElement("span");
  icon.className = "material-symbols-outlined";
  icon.setAttribute("aria-hidden", "true");
  icon.textContent = name;
  return icon;
}

const editButtons = Array.from(document.getElementsByClassName("edit-card"));

editButtons.forEach((button) => {
  button.addEventListener("click", () => {
    const card = button.closest("[data-card-uuid]");
    if (!card || card.querySelector(".card-name-editor")) {
      return;
    }

    const uuid = card.getAttribute("data-card-uuid");
    const nameElement = card.querySelector(".js-card-name, .edit-td");
    const actions = card.querySelector(".linked-card__actions");
    const isLegacyCardRow = nameElement?.classList.contains("edit-td");

    if (!nameElement) {
      return;
    }

    const currentName =
      nameElement.getAttribute("data-card-name") ||
      nameElement.getAttribute("card_name") ||
      nameElement.textContent.trim();

    const editor = document.createElement("form");
    editor.className = isLegacyCardRow
      ? "card-name-editor card-name-editor--legacy"
      : "card-name-editor";

    const label = document.createElement("label");
    const inputId = `card-name-${uuid}`;
    label.className = "visually-hidden";
    label.setAttribute("for", inputId);
    label.textContent = "Naam van de pas";

    const input = document.createElement("input");
    input.id = inputId;
    input.className = "form-control";
    input.type = "text";
    input.value = currentName;
    input.maxLength = 100;
    input.required = true;
    input.autocomplete = "off";

    const saveButton = document.createElement("button");
    saveButton.className =
      "card-name-editor__button card-name-editor__button--save";
    saveButton.type = "submit";
    saveButton.setAttribute("aria-label", "Naam opslaan");
    saveButton.appendChild(createIcon("check"));

    const cancelButton = document.createElement("button");
    cancelButton.className = "card-name-editor__button";
    cancelButton.type = "button";
    cancelButton.setAttribute("aria-label", "Wijzigen annuleren");
    cancelButton.appendChild(createIcon("close"));

    editor.append(label, input, saveButton, cancelButton);
    nameElement.replaceChildren(editor);
    if (actions) {
      actions.hidden = true;
    } else {
      button.hidden = true;
    }
    input.focus();
    input.select();

    const restoreName = (name) => {
      nameElement.textContent = name || "Naamloze pas";
      if (actions) {
        actions.hidden = false;
      } else {
        button.hidden = false;
      }
      button.focus();
    };

    cancelButton.addEventListener("click", () => {
      restoreName(currentName);
    });

    editor.addEventListener("submit", (event) => {
      event.preventDefault();
      const nextName = input.value.trim();

      if (!nextName) {
        input.setCustomValidity("Vul een naam in.");
        input.reportValidity();
        return;
      }

      input.setCustomValidity("");
      input.disabled = true;
      saveButton.disabled = true;
      cancelButton.disabled = true;

      $.ajax({
        url: `/api/cardname?card_uuid=${encodeURIComponent(uuid)}&name=${encodeURIComponent(nextName)}`,
        type: "POST",
        beforeSend: (xhr) => {
          xhr.setRequestHeader("X-CSRFToken", csrf_token);
        },
        success: (response) => {
          nameElement.setAttribute("data-card-name", nextName);
          if (isLegacyCardRow) {
            nameElement.setAttribute("card_name", nextName);
          }
          restoreName(nextName);
          showToast("Pas hernoemd", response);
        },
        error: (response) => {
          input.disabled = false;
          saveButton.disabled = false;
          cancelButton.disabled = false;
          input.focus();
          showToast("Hernoemen mislukt", response.response);
        },
      });
    });
  });
});

const topUpForm = document.querySelector("[data-topup-form]");

if (topUpForm) {
  const amountInput = topUpForm.querySelector('input[name="amount"]');
  const presetButtons = Array.from(
    topUpForm.querySelectorAll("[data-topup-amount]"),
  );

  presetButtons.forEach((button) => {
    button.addEventListener("click", () => {
      if (!amountInput) {
        return;
      }

      amountInput.value = button.getAttribute("data-topup-amount");
      presetButtons.forEach((preset) => {
        preset.classList.toggle("is-selected", preset === button);
      });
      amountInput.focus();
    });
  });

  if (amountInput) {
    amountInput.addEventListener("input", () => {
      presetButtons.forEach((button) => {
        button.classList.toggle(
          "is-selected",
          button.getAttribute("data-topup-amount") === amountInput.value,
        );
      });
    });
  }
}

/*
 * Keep server-rendered pagination state independent and return to the section
 * that initiated navigation. This enhances links emitted by the shared
 * pagination_footer.html without depending on its page-parameter names.
 */
document
  .querySelectorAll("[data-pagination-anchor][id]")
  .forEach((section) => {
    const sectionId = section.getAttribute("id");
    const paginationLinks = section.querySelectorAll(
      '.portal-pagination a[href]:not([href^="#"])',
    );

    paginationLinks.forEach((link) => {
      const targetUrl = new URL(link.getAttribute("href"), window.location.href);
      const mergedParameters = new URLSearchParams(window.location.search);
      const targetParameterNames = new Set(targetUrl.searchParams.keys());

      targetParameterNames.forEach((name) => {
        mergedParameters.delete(name);
      });
      targetUrl.searchParams.forEach((value, name) => {
        mergedParameters.append(name, value);
      });

      targetUrl.search = mergedParameters.toString();
      targetUrl.hash = sectionId;
      link.setAttribute(
        "href",
        `${targetUrl.pathname}${targetUrl.search}${targetUrl.hash}`,
      );
    });
  });

updateCardState();

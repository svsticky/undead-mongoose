// Export transactions
const exportTransactions = document.getElementById("export-top-ups");
if (exportTransactions) {
  exportTransactions.addEventListener("click", e => {
    const from = document.getElementById("from-date").value;
    const to = document.getElementById("to-date").value;

    const export_dropdown = document.getElementById("export-type");
    const export_type = export_dropdown.options[export_dropdown.selectedIndex].value;

    const reponse_dropdown = document.getElementById("response-type");
    const response_type = reponse_dropdown.options[reponse_dropdown.selectedIndex].value;

    const url = `/transactions/export?type=${export_type}&start_date=${from}&end_date=${to}&response_type=${response_type}`;
    window.open(url, "_blank");
  });
}

if (window.location.pathname.includes("transactions")) {
  if (window.location.search.includes("top_ups")) {
    const top_ups = document.getElementById("top-ups");
    console.log(top_ups)
    if (top_ups) {
      document.getElementById("top-ups-tab").classList.add("active");
      top_ups.classList.add("show");
      top_ups.classList.add("active");
    }
  } else if (window.location.search.includes("ideal")) {
    const ideals = document.getElementById("ideal");
    if (ideals) {
      document.getElementById("ideal-tab").classList.add("active");
      ideals.classList.add("show");
      ideals.classList.add("active");
    }
  } else {
    const sales = document.getElementById("sales");
    if (sales) {
      document.getElementById("sales-tab").classList.add("active");
      sales.classList.add("show");
      sales.classList.add("active");
    }
  }
}


/* breakout.js — FINAL STABLE */

(function () {
  "use strict";

  const BREAKPOINT = 768;

  document.querySelectorAll("[data-breakout-toggle]").forEach(function (btn) {

    const tableWrap = btn.closest(".breakout-table-wrap");
    const rows = tableWrap.querySelectorAll("[data-breakout-row]");

    function getVisibleCount() {
      return window.innerWidth <= BREAKPOINT ? 3 : 5;
    }

    function collapseRows() {
      const visibleCount = getVisibleCount();

      rows.forEach((row, index) => {
        if (index >= visibleCount) {
          row.classList.add("is-hidden");
        } else {
          row.classList.remove("is-hidden");
        }
      });

      const hiddenCount = rows.length - visibleCount;
      btn.textContent = hiddenCount > 0 ? `Show ${hiddenCount} More` : "";
      btn.style.display = hiddenCount > 0 ? "inline-flex" : "none";

      btn.setAttribute("aria-expanded", "false");
    }

    function expandRows() {
      rows.forEach(row => row.classList.remove("is-hidden"));
      btn.textContent = "Show Less";
      btn.setAttribute("aria-expanded", "true");
    }

    collapseRows();

    btn.addEventListener("click", function () {
      const expanded = btn.getAttribute("aria-expanded") === "true";
      expanded ? collapseRows() : expandRows();
    });

    window.addEventListener("resize", collapseRows);
  });

})();
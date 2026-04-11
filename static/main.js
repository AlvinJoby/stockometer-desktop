const divider = document.getElementById("drag-divider");
const mainPanel = document.querySelector(".main-panel");
const returnsPanel = document.querySelector(".returns-panel");
const navbar = document.querySelector(".navbar");
const stickyMarketBar = document.getElementById("sticky-market-bar");
const pageLoadingOverlay = document.getElementById("page-loading-overlay");
const indicatorPicker = document.getElementById("indicator-picker");
const indicatorTrigger = document.getElementById("indicator-trigger");
const indicatorDropdown = document.getElementById("indicator-dropdown");
const indicatorLoadingOverlay = document.getElementById("indicator-loading-overlay");
const indicatorLoadingText = document.getElementById("indicator-loading-text");
const MINIMUM_PAGE_LOADER_MS = 3000;
const pageLoaderStartedAt = Date.now();

let isDragging = false;

function getPlotDiv() {
  return mainPanel?.querySelector(".js-plotly-plot") ?? null;
}

function syncMainChartLayout() {
  const plotDiv = getPlotDiv();
  if (!plotDiv || typeof Plotly === "undefined") return;

  const chartWidth = mainPanel?.getBoundingClientRect().width ?? window.innerWidth;
  const isMobile = chartWidth <= 768;

  Plotly.relayout(plotDiv, {
    autosize: true,
    margin: isMobile
      ? { l: 8, r: 44, t: 16, b: 32 }
      : { l: 10, r: 54, t: 20, b: 40 },
  });
}

function hidePageLoader() {
  if (!pageLoadingOverlay) return;
  pageLoadingOverlay.classList.add("is-hidden");
  pageLoadingOverlay.setAttribute("aria-hidden", "true");
}

function enterChartLoaderStage() {
  if (!pageLoadingOverlay) return;
  pageLoadingOverlay.classList.add("is-chart-stage");
}

function syncStickyMarketBar() {
  if (!stickyMarketBar || !mainPanel) return;

  const mainPanelRect = mainPanel.getBoundingClientRect();
  const shouldShow = mainPanelRect.bottom <= 32;

  stickyMarketBar.classList.toggle("is-visible", shouldShow);
  stickyMarketBar.setAttribute("aria-hidden", shouldShow ? "false" : "true");
}

function setupBreakoutMobileToggle() {
  const toggleButton = document.querySelector("[data-breakout-toggle]");
  const breakoutTableWrap = document.querySelector(".breakout-table-wrap");
  if (!toggleButton || !breakoutTableWrap) return;

  toggleButton.addEventListener("click", () => {
    const shouldExpand = !breakoutTableWrap.classList.contains("is-expanded");
    breakoutTableWrap.classList.toggle("is-expanded", shouldExpand);
    toggleButton.textContent = shouldExpand ? "Show Less" : "Show More";
    toggleButton.setAttribute("aria-expanded", shouldExpand ? "true" : "false");
  });
}

function toIndicatorLabel(indicator) {
  return indicator.replaceAll("_", " ");
}

function setupIndicatorPicker() {
  const selectableIndicators = window.__MAIN_CHART__?.selectableOverlayIndicators ?? [];
  if (!indicatorPicker || !indicatorTrigger || !indicatorDropdown || selectableIndicators.length === 0) return;
  let indicatorToggleTimer = null;

  indicatorDropdown.innerHTML = "";
  for (const indicator of selectableIndicators) {
    const option = document.createElement("label");
    option.className = "indicator-option";
    option.innerHTML = `
      <input type="checkbox" value="${indicator}" />
      <span>${toIndicatorLabel(indicator)}</span>
    `;
    indicatorDropdown.appendChild(option);
  }

  const traceNamesByIndicator = {
    SMA_20: ["SMA_20"],
    SMA_50: ["SMA_50"],
    SMA_100: ["SMA_100"],
    EMA_20: ["EMA_20"],
    EMA_50: ["EMA_50"],
    EMA_100: ["EMA_100"],
  };

  function applyIndicatorSelection(selected) {
    const plotDiv = getPlotDiv();
    if (!plotDiv || typeof Plotly === "undefined" || !Array.isArray(plotDiv.data)) return;

    for (const indicator of selectableIndicators) {
      const indicatorTraceNames = traceNamesByIndicator[indicator] ?? [];
      const shouldShow = selected.has(indicator);
      plotDiv.data.forEach((trace, index) => {
        if (indicatorTraceNames.includes(trace.name)) {
          Plotly.restyle(plotDiv, { visible: shouldShow }, [index]);
        }
      });
    }
  }

  function setIndicatorControlsDisabled(disabled) {
    indicatorTrigger.disabled = disabled;
    indicatorDropdown.querySelectorAll("input[type='checkbox']").forEach((input) => {
      input.disabled = disabled;
    });
  }

  function showIndicatorLoader(text = "") {
    if (!indicatorLoadingOverlay || !indicatorLoadingText) return;
    indicatorLoadingText.textContent = text;
    indicatorLoadingText.style.display = text ? "block" : "none";
    indicatorLoadingOverlay.classList.add("is-visible");
    indicatorLoadingOverlay.setAttribute("aria-hidden", "false");
  }

  function hideIndicatorLoader() {
    if (!indicatorLoadingOverlay || !indicatorLoadingText) return;
    indicatorLoadingOverlay.classList.remove("is-visible");
    indicatorLoadingOverlay.setAttribute("aria-hidden", "true");
    indicatorLoadingText.textContent = "";
  }

  indicatorDropdown.addEventListener("change", (event) => {
    if (event.target instanceof HTMLInputElement) {
      const selected = new Set(
        Array.from(indicatorDropdown.querySelectorAll("input[type='checkbox']:checked")).map((item) => item.value),
      );
      const actionText = event.target.checked ? `Adding ${toIndicatorLabel(event.target.value)}` : "";

      if (indicatorToggleTimer) {
        window.clearTimeout(indicatorToggleTimer);
      }

      setIndicatorControlsDisabled(true);
      showIndicatorLoader(actionText);

      indicatorToggleTimer = window.setTimeout(() => {
        applyIndicatorSelection(selected);
        hideIndicatorLoader();
        setIndicatorControlsDisabled(false);
      }, 2000);
    }
  });

  indicatorTrigger.addEventListener("click", () => {
    const shouldOpen = !indicatorDropdown.classList.contains("is-open");
    indicatorDropdown.classList.toggle("is-open", shouldOpen);
    indicatorDropdown.setAttribute("aria-hidden", shouldOpen ? "false" : "true");
    indicatorTrigger.setAttribute("aria-expanded", shouldOpen ? "true" : "false");
  });

  document.addEventListener("click", (event) => {
    if (!indicatorPicker.contains(event.target)) {
      indicatorDropdown.classList.remove("is-open");
      indicatorDropdown.setAttribute("aria-hidden", "true");
      indicatorTrigger.setAttribute("aria-expanded", "false");
    }
  });

  document.addEventListener("keydown", (event) => {
    if (event.key === "Escape") {
      indicatorDropdown.classList.remove("is-open");
      indicatorDropdown.setAttribute("aria-hidden", "true");
      indicatorTrigger.setAttribute("aria-expanded", "false");
    }
  });

  // Ensure optional overlay indicators are hidden by default on first load.
  applyIndicatorSelection(new Set());
}

if (divider) {
  divider.addEventListener("mousedown", () => {
    isDragging = true;
    document.body.style.cursor = "col-resize";
    document.body.style.userSelect = "none";
  });
}

document.addEventListener("mousemove", (e) => {
  if (!isDragging) return;

  const containerRect = document.querySelector(".front-layout").getBoundingClientRect();
  const totalWidth = containerRect.width;
  const offsetX = e.clientX - containerRect.left;

  const mainPct = Math.min(Math.max((offsetX / totalWidth) * 100, 70), 85);
  const returnsPct = 100 - mainPct - 0.4;

  mainPanel.style.flex = `0 0 ${mainPct}%`;
  returnsPanel.style.flex = `0 0 ${returnsPct}%`;
  syncMainChartLayout();
});

document.addEventListener("mouseup", () => {
  isDragging = false;
  document.body.style.cursor = "";
  document.body.style.userSelect = "";
});

window.addEventListener("load", () => {
  setupIndicatorPicker();
  syncMainChartLayout();
  syncStickyMarketBar();
  setupBreakoutMobileToggle();
  window.requestAnimationFrame(() => {
    window.requestAnimationFrame(() => {
      enterChartLoaderStage();
      const remainingTime = Math.max(0, MINIMUM_PAGE_LOADER_MS - (Date.now() - pageLoaderStartedAt));
      window.setTimeout(() => {
        hidePageLoader();
      }, remainingTime);
    });
  });
});
window.addEventListener("resize", syncMainChartLayout);
window.addEventListener("resize", syncStickyMarketBar);
window.addEventListener("scroll", syncStickyMarketBar, { passive: true });

document.addEventListener("DOMContentLoaded", function () {
    const appTitle = document.querySelector('.app-title');
    if (!appTitle) return;

    appTitle.addEventListener('click', function(e) {
        e.preventDefault();
        window.scrollTo({
            top: 0,
            behavior: 'smooth'
        });
    });
});

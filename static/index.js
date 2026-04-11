const input = document.getElementById("symbol-input");
const suggestions = document.getElementById("symbol-suggestions");
const formError = document.getElementById("form-error");
const analyzeForm = document.getElementById("analyze-form");
const loadingOverlay = document.getElementById("loading-overlay");
const loadingText = document.getElementById("loading-text");
const trendingList = document.getElementById("trending-list");
const popularRegionFilter = document.getElementById("popular-region-filter");
const errorState = document.body.dataset.errorState;
const ANALYZE_STARTED_AT_KEY = "stockometerAnalyzeStartedAt";
const LOADING_TEXT_FADE_MS = 380;
let loadingSequenceTimers = [];

const POPULAR_BY_REGION = {
  US: ["AAPL", "MSFT", "NVDA", "AMZN", "GOOGL", "META", "TSLA", "JPM", "BRK-B", "WMT"],
  EUROPE: ["ASML.AS", "SAP.DE", "NESN.SW", "MC.PA", "SIE.DE", "AIR.PA", "SHEL.L", "NOVO-B.CO", "SAN.PA", "OR.PA"],
  CHINA: ["BABA", "JD", "PDD", "NIO", "XPEV", "LI", "BIDU", "TCEHY", "9988.HK", "0700.HK"],
  INDIA: ["RELIANCE.NS", "TCS.NS", "HDFCBANK.NS", "ICICIBANK.NS", "INFY.NS", "SBIN.NS", "LT.NS", "ITC.NS", "BHARTIARTL.NS", "KOTAKBANK.NS"],
  UK: ["SHEL.L", "HSBA.L", "AZN.L", "BP.L", "GSK.L", "RIO.L", "ULVR.L", "DGE.L", "BARC.L", "LLOY.L"],
  KOREA: ["005930.KS", "000660.KS", "035420.KS", "005380.KS", "012330.KS", "068270.KS", "105560.KS", "035720.KS", "051910.KS", "207940.KS"],
};

const renderPopularSymbols = (region) => {
  if (!trendingList) return;

  const symbols = POPULAR_BY_REGION[region] || POPULAR_BY_REGION.US;
  trendingList.innerHTML = symbols
    .map((symbol) => `<button type="button" class="trend-item" data-symbol="${symbol}">${symbol}</button>`)
    .join("");
};

const showLoadingOverlay = () => {
  if (!loadingOverlay) {
    return;
  }
  loadingOverlay.classList.add("is-visible");
  loadingOverlay.setAttribute("aria-hidden", "false");
};

const hideLoadingOverlay = () => {
  if (!loadingOverlay) {
    return;
  }
  loadingOverlay.classList.remove("is-visible");
  loadingOverlay.setAttribute("aria-hidden", "true");
};

const clearAnalyzeState = () => {
  try {
    window.sessionStorage.removeItem(ANALYZE_STARTED_AT_KEY);
  } catch (_error) {
    // Ignore storage failures and fall back to immediate transitions.
  }
};

const clearLoadingSequence = () => {
  loadingSequenceTimers.forEach((timerId) => window.clearTimeout(timerId));
  loadingSequenceTimers = [];
};

const setLoadingText = (text) => {
  if (!loadingText) {
    return;
  }

  loadingText.classList.add("is-fading-out");
  const timerId = window.setTimeout(() => {
    loadingText.textContent = text;
    loadingText.classList.remove("is-fading-out");
  }, LOADING_TEXT_FADE_MS);
  loadingSequenceTimers.push(timerId);
};

const startLoadingSequence = () => {
  if (!loadingText) {
    return;
  }

  clearLoadingSequence();
  loadingText.textContent = "Checking the symbol...";
  loadingText.classList.remove("is-fading-out");

  loadingSequenceTimers.push(window.setTimeout(() => {
    setLoadingText("Downloading 8yrs of data...");
  }, 2000));

  loadingSequenceTimers.push(window.setTimeout(() => {
    setLoadingText("Analyzing...");
  }, 13000));
};

const shouldAdvanceLoadingText = async (symbol) => {
  if (!symbol) {
    return false;
  }

  const controller = new AbortController();
  const timeoutId = window.setTimeout(() => controller.abort(), 1200);

  try {
    const response = await fetch(`/api/symbols?q=${encodeURIComponent(symbol)}`, {
      signal: controller.signal,
    });
    if (!response.ok) {
      return true;
    }

    const data = await response.json();
    if (!Array.isArray(data) || data.length === 0) {
      return false;
    }

    const normalized = symbol.trim().toUpperCase();
    return data.some((item) => (item?.symbol || "").trim().toUpperCase() === normalized);
  } catch (_error) {
    return true;
  } finally {
    window.clearTimeout(timeoutId);
  }
};

const scheduleErrorDismiss = () => {
  if (!formError) {
    return;
  }

  window.setTimeout(() => {
    formError.classList.add("is-hidden");
    window.setTimeout(() => {
      formError.remove();
    }, 1200);
  }, 4000);
};

if (formError && loadingOverlay && errorState === "visible") {
  window.requestAnimationFrame(() => {
    window.setTimeout(() => {
      window.setTimeout(() => {
        hideLoadingOverlay();
        clearAnalyzeState();
        window.setTimeout(() => {
          formError.classList.add("is-visible");
          scheduleErrorDismiss();
        }, 220);
      }, 0);
    }, 120);
  });
} else if (formError) {
  clearAnalyzeState();
  formError.classList.add("is-visible");
  scheduleErrorDismiss();
} else {
  clearAnalyzeState();
  hideLoadingOverlay();
}

window.addEventListener("pageshow", () => {
  if (errorState !== "visible") {
    clearAnalyzeState();
    hideLoadingOverlay();
  }
});

if (popularRegionFilter) {
  popularRegionFilter.addEventListener("change", (event) => {
    if (!(event.target instanceof HTMLInputElement)) return;
    if (event.target.name !== "popular-region") return;
    renderPopularSymbols(event.target.value);
  });
}

if (trendingList) {
  trendingList.addEventListener("click", (event) => {
    const button = event.target.closest(".trend-item");
    if (!button || !input) return;
    input.value = button.dataset.symbol || button.textContent || "";
    input.focus();
  });
  renderPopularSymbols("US");
}

if (analyzeForm && loadingOverlay) {
  analyzeForm.addEventListener("submit", async (event) => {
    event.preventDefault();

    try {
      window.sessionStorage.setItem(ANALYZE_STARTED_AT_KEY, String(Date.now()));
    } catch (_error) {
      // Ignore storage failures and still show the overlay.
    }

    showLoadingOverlay();
    clearLoadingSequence();
    if (loadingText) {
      loadingText.textContent = "Checking the symbol...";
      loadingText.classList.remove("is-fading-out");
    }

    const symbol = (input?.value || "").trim();
    const advanceLoadingText = await shouldAdvanceLoadingText(symbol);
    if (advanceLoadingText) {
      startLoadingSequence();
    }

    analyzeForm.submit();
  });
}

if (input && suggestions) {
  let debounceTimer = null;
  let activeIndex = -1;
  let items = [];
  let requestId = 0;

  const closeSuggestions = () => {
    suggestions.hidden = true;
    suggestions.innerHTML = "";
    input.setAttribute("aria-expanded", "false");
    input.removeAttribute("aria-activedescendant");
    activeIndex = -1;
    items = [];
  };

  const setActiveIndex = (nextIndex) => {
    activeIndex = nextIndex;

    const options = suggestions.querySelectorAll(".suggestion");
    options.forEach((option, index) => {
      const isActive = index === activeIndex;
      option.classList.toggle("active", isActive);
      option.setAttribute("aria-selected", isActive ? "true" : "false");
      if (isActive) {
        input.setAttribute("aria-activedescendant", option.id);
        option.scrollIntoView({ block: "nearest" });
      }
    });

    if (activeIndex < 0) {
      input.removeAttribute("aria-activedescendant");
    }
  };

  const chooseSuggestion = (item) => {
    input.value = item.symbol;
    closeSuggestions();
    input.focus();
  };

  const renderStateRow = (message, stateClass) => {
    suggestions.hidden = false;
    input.setAttribute("aria-expanded", "true");
    suggestions.innerHTML = `<div class="suggestion-meta ${stateClass}">${message}</div>`;
    activeIndex = -1;
    items = [];
  };

  const renderSuggestions = (nextItems) => {
    items = nextItems;
    activeIndex = -1;

    if (!items.length) {
      renderStateRow("No matches found", "suggestion-empty");
      return;
    }

    suggestions.hidden = false;
    input.setAttribute("aria-expanded", "true");
    suggestions.innerHTML = items
      .map((item, index) => {
        const optionId = `symbol-suggestion-${index}`;
        const metaLabel = [item.exchange, item.type].filter(Boolean).join(" | ");
        return `
          <button
            id="${optionId}"
            type="button"
            class="suggestion"
            role="option"
            aria-selected="false"
            data-index="${index}"
          >
            <span class="suggestion-label">${item.name}</span>
            <span class="suggestion-symbol">${item.symbol}</span>
            ${metaLabel ? `<span class="suggestion-support">${metaLabel}</span>` : ""}
          </button>
        `;
      })
      .join("");
  };

  const fetchSuggestions = async (query) => {
    const trimmedQuery = query.trim();

    if (trimmedQuery.length < 2) {
      closeSuggestions();
      return;
    }

    const currentRequestId = ++requestId;
    renderStateRow("Searching...", "suggestion-loading");

    try {
      const response = await fetch(`/api/symbols?q=${encodeURIComponent(trimmedQuery)}`);
      const data = response.ok ? await response.json() : [];

      if (currentRequestId !== requestId) {
        return;
      }

      renderSuggestions(Array.isArray(data) ? data.slice(0, 8) : []);
    } catch (_error) {
      if (currentRequestId !== requestId) {
        return;
      }
      closeSuggestions();
    }
  };

  input.addEventListener("input", () => {
    clearTimeout(debounceTimer);
    debounceTimer = setTimeout(() => {
      fetchSuggestions(input.value);
    }, 250);
  });

  input.addEventListener("keydown", (event) => {
    if (suggestions.hidden || !items.length) {
      if (event.key === "Escape") {
        closeSuggestions();
      }
      return;
    }

    if (event.key === "ArrowDown") {
      event.preventDefault();
      setActiveIndex((activeIndex + 1) % items.length);
      return;
    }

    if (event.key === "ArrowUp") {
      event.preventDefault();
      setActiveIndex((activeIndex - 1 + items.length) % items.length);
      return;
    }

    if (event.key === "Enter" && activeIndex >= 0) {
      event.preventDefault();
      chooseSuggestion(items[activeIndex]);
      return;
    }

    if (event.key === "Escape") {
      event.preventDefault();
      closeSuggestions();
    }
  });

  suggestions.addEventListener("mousemove", (event) => {
    const option = event.target.closest(".suggestion");
    if (!option) {
      return;
    }

    setActiveIndex(Number(option.dataset.index));
  });

  suggestions.addEventListener("mousedown", (event) => {
    const option = event.target.closest(".suggestion");
    if (!option) {
      return;
    }

    event.preventDefault();
    chooseSuggestion(items[Number(option.dataset.index)]);
  });

  document.addEventListener("click", (event) => {
    if (!event.target.closest(".autocomplete")) {
      closeSuggestions();
    }
  });
}

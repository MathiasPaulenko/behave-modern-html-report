/* ============================================================
   Behave Modern Report — client behavior
   Navigation, search, filters, expand/collapse, lightbox, charts.
   ============================================================ */
(function () {
  "use strict";

  // ---- Data --------------------------------------------------
  var dataNode = document.getElementById("bmr-data");
  var DATA = {};
  try { DATA = JSON.parse(dataNode.textContent || "{}"); } catch (e) { DATA = {}; }

  var PALETTE = {};
  function refreshPalette() {
    PALETTE = {
      passed:    getCss("--c-passed",    "#22c55e"),
      failed:    getCss("--c-failed",    "#ef4444"),
      skipped:   getCss("--c-skipped",   "#94a3b8"),
      undefined: getCss("--c-undefined", "#f59e0b"),
      pending:   getCss("--c-pending",   "#8b5cf6"),
      untested:  getCss("--c-untested",  "#64748b"),
    };
  }

  function getCss(name, fallback) {
    var v = getComputedStyle(document.documentElement).getPropertyValue(name);
    return (v && v.trim()) || fallback;
  }

  // ---- Theme -------------------------------------------------
  var THEME_KEY = "bmr.theme";
  function applyTheme(theme) {
    document.documentElement.setAttribute("data-theme", theme);
    try { localStorage.setItem(THEME_KEY, theme); } catch (_) {}
  }
  (function initTheme() {
    var saved = null;
    try { saved = localStorage.getItem(THEME_KEY); } catch (_) {}
    if (saved) applyTheme(saved);
    refreshPalette();
    function effectiveTheme() {
      var theme = document.documentElement.getAttribute("data-theme") || "auto";
      if (theme !== "auto") return theme;
      return window.matchMedia && window.matchMedia("(prefers-color-scheme: light)").matches ? "light" : "dark";
    }
    var btn = document.getElementById("theme-toggle");
    if (btn) {
      btn.addEventListener("click", function () {
        var next = effectiveTheme() === "dark" ? "light" : "dark";
        var html = document.documentElement;
        // Disable transitions briefly so the theme switch is instant and charts measure a stable layout.
        html.classList.add("bmr-no-transition");
        applyTheme(next);
        // Force a synchronous reflow so the new theme is applied before removing the class.
        void html.offsetHeight;
        html.classList.remove("bmr-no-transition");
        // Redraw after the next paint once the layout has settled.
        requestAnimationFrame(function () {
          refreshPalette();
          renderCharts();
        });
      });
    }
  })();

  // ---- Navigation -------------------------------------------
  var navItems = document.querySelectorAll(".nav-item");
  var views = document.querySelectorAll(".view");
  function showView(route) {
    navItems.forEach(function (b) { b.classList.toggle("is-active", b.dataset.route === route); });
    views.forEach(function (v) { v.hidden = v.dataset.view !== route; });
    if (route === "statistics" || route === "dashboard" || route === "tags") renderCharts();
  }
  navItems.forEach(function (b) {
    b.addEventListener("click", function () { showView(b.dataset.route); });
  });

  // ---- Expand / collapse -------------------------------------
  function toggleSection(head, expanded) {
    var body;
    if (head.classList.contains("scenario-head")) {
      body = head.closest(".scenario").querySelector(".scenario-body");
    } else {
      body = head.nextElementSibling;
    }
    head.setAttribute("aria-expanded", String(expanded));
    if (body) body.hidden = !expanded;
  }
  document.addEventListener("click", function (e) {
    var expandBtn = e.target.closest("[data-expand-all]");
    var collapseBtn = e.target.closest("[data-collapse-all]");
    if (expandBtn) {
      document.querySelectorAll(expandBtn.dataset.expandAll).forEach(function (el) {
        var head = el.querySelector(".feature-head, .rule-head, .scenario-head");
        if (head) toggleSection(head, true);
      });
      return;
    }
    if (collapseBtn) {
      document.querySelectorAll(collapseBtn.dataset.collapseAll).forEach(function (el) {
        var head = el.querySelector(".feature-head, .rule-head, .scenario-head");
        if (head) toggleSection(head, false);
      });
      return;
    }
    var head = e.target.closest(".feature-head, .rule-head, .scenario-head");
    if (!head) return;
    var expanded = head.getAttribute("aria-expanded") === "true";
    toggleSection(head, !expanded);
  });

  // ---- View mode toggle (compact / detailed / result) --------
  var VIEW_MODE_KEY = "bmr.viewMode";
  function applyViewMode(mode) {
    var listIds = ["features-list", "rules-list", "scenarios-list"];
    listIds.forEach(function (id) {
      var el = document.getElementById(id);
      if (el) el.classList.toggle("detailed", mode === "detailed");
    });
    var scenariosList = document.getElementById("scenarios-list");
    var scenariosTable = document.getElementById("scenarios-table");
    if (scenariosList && scenariosTable) {
      scenariosList.hidden = mode === "result";
      scenariosTable.hidden = mode !== "result";
    }
    document.querySelectorAll("[data-view-mode]").forEach(function (btn) {
      btn.classList.toggle("is-active", btn.dataset.viewMode === mode);
      btn.setAttribute("aria-pressed", String(btn.dataset.viewMode === mode));
    });
    try { localStorage.setItem(VIEW_MODE_KEY, mode); } catch (_) {}
  }
  (function initViewMode() {
    var saved = "compact";
    try { saved = localStorage.getItem(VIEW_MODE_KEY) || "compact"; } catch (_) {}
    if (!["result", "compact", "detailed"].includes(saved)) saved = "compact";
    applyViewMode(saved);
    document.addEventListener("click", function (e) {
      var btn = e.target.closest("[data-view-mode]");
      if (!btn) return;
      applyViewMode(btn.dataset.viewMode);
    });
  })();

  // ---- Copy to clipboard -------------------------------------
  document.addEventListener("click", function (e) {
    var btn = e.target.closest(".copy-btn");
    if (!btn) return;
    var text;
    if (btn.dataset.copyText) {
      text = btn.dataset.copyText;
    } else {
      var target = document.querySelector(btn.dataset.copyTarget);
      if (!target) return;
      text = target.innerText || target.textContent || "";
    }
    var done = function () {
      var prev = btn.innerHTML;
      btn.innerHTML = '<svg class="ico"><use href="#i-check"/></svg>Copied';
      setTimeout(function () { btn.innerHTML = prev; }, 1400);
    };
    if (navigator.clipboard && navigator.clipboard.writeText) {
      navigator.clipboard.writeText(text).then(done, function () { fallbackCopy(text); done(); });
    } else { fallbackCopy(text); done(); }
  });
  function fallbackCopy(text) {
    var ta = document.createElement("textarea");
    ta.value = text; ta.style.position = "fixed"; ta.style.opacity = "0";
    document.body.appendChild(ta); ta.select();
    try { document.execCommand("copy"); } catch (_) {}
    document.body.removeChild(ta);
  }

  // ---- Lightbox ----------------------------------------------
  var lb = document.getElementById("lightbox");
  var lbContent = lb && lb.querySelector(".lightbox-content");
  document.addEventListener("click", function (e) {
    var t = e.target.closest("[data-attach-img]");
    if (t && lb && lbContent) {
      lbContent.innerHTML = '<img alt="" src="' + t.dataset.attachImg + '" />';
      lb.hidden = false;
      return;
    }
    if (lb && !lb.hidden && (e.target === lb || e.target.classList.contains("lightbox-close"))) {
      lb.hidden = true; lbContent.innerHTML = "";
    }
  });
  document.addEventListener("keydown", function (e) {
    if (e.key === "Escape" && lb && !lb.hidden) { lb.hidden = true; lbContent.innerHTML = ""; }
    if (e.key === "/" && document.activeElement && document.activeElement.tagName !== "INPUT") {
      var s = document.getElementById("global-search");
      if (s) { e.preventDefault(); s.focus(); }
    }
  });

  // ---- Search + Filters --------------------------------------
  var searchInput = document.getElementById("global-search");
  var filterChips = document.querySelectorAll("[data-filter-status]");
  var activeStatuses = new Set(Array.prototype.map.call(filterChips, function (c) { return c.dataset.filterStatus; }));
  var filtersToggle = document.getElementById("filters-toggle");
  var advancedFilters = document.getElementById("advanced-filters");
  var filterTags = document.getElementById("filter-tags");
  var filterMinDuration = document.getElementById("filter-min-duration");
  var filterErrorText = document.getElementById("filter-error-text");

  if (filtersToggle && advancedFilters) {
    filtersToggle.addEventListener("click", function () {
      var hidden = advancedFilters.hidden;
      advancedFilters.hidden = !hidden;
      filtersToggle.setAttribute("aria-expanded", String(hidden));
    });
  }

  function addFilterInput(el) {
    if (!el) return;
    el.addEventListener("input", function () { clearTimeout(t); t = setTimeout(applyFilters, 80); });
    if (el.type === "checkbox") {
      el.addEventListener("change", function () { clearTimeout(t); t = setTimeout(applyFilters, 80); });
    }
  }
  var t;
  addFilterInput(searchInput);
  addFilterInput(filterTags);
  addFilterInput(filterMinDuration);
  addFilterInput(filterErrorText);

  filterChips.forEach(function (chip) {
    chip.addEventListener("click", function () {
      var s = chip.dataset.filterStatus;
      if (activeStatuses.has(s)) { activeStatuses.delete(s); chip.setAttribute("aria-pressed", "false"); }
      else { activeStatuses.add(s); chip.setAttribute("aria-pressed", "true"); }
      applyFilters();
    });
  });

  function matchesScenario(el, q, tagFilter, minDuration, searchError) {
    var status = el.dataset.status;
    var name = el.dataset.name || "";
    var tags = el.dataset.tags || "";
    var feat = el.dataset.feature || "";
    var rule = el.dataset.rule || "";
    var duration = parseFloat(el.dataset.duration || "0") || 0;
    var error = el.dataset.error || "";
    var matchStatus = activeStatuses.has(status);
    var matchQuery = !q || name.indexOf(q) >= 0 || tags.indexOf(q) >= 0 || feat.indexOf(q) >= 0 || rule.indexOf(q) >= 0;
    if (searchError && q) matchQuery = matchQuery || error.indexOf(q) >= 0;
    var matchTags = !tagFilter.length || tagFilter.every(function (t) { return tags.indexOf(t) >= 0; });
    var matchDuration = duration >= minDuration;
    return matchStatus && matchQuery && matchTags && matchDuration;
  }

  function applyFilters() {
    var q = (searchInput ? searchInput.value : "").toLowerCase().trim();
    var tagFilter = (filterTags ? filterTags.value : "").toLowerCase().replace(/\s+/g, "").split(",").filter(Boolean);
    var minDuration = parseFloat(filterMinDuration ? filterMinDuration.value : "0") || 0;
    var searchError = filterErrorText && filterErrorText.checked;
    document.querySelectorAll(".scenario").forEach(function (el) {
      el.classList.toggle("is-hidden", !matchesScenario(el, q, tagFilter, minDuration, searchError));
    });
    document.querySelectorAll(".scenario-row").forEach(function (el) {
      el.classList.toggle("is-hidden", !matchesScenario(el, q, tagFilter, minDuration, searchError));
    });
    // Hide rule cards whose scenarios are all hidden.
    document.querySelectorAll(".rule.card").forEach(function (r) {
      var any = r.querySelectorAll(".scenario:not(.is-hidden)").length > 0;
      var ruleName = r.dataset.rule || "";
      var featName = r.dataset.feature || "";
      var ruleTags = r.dataset.tags || "";
      var matchRuleQuery = !q || ruleName.indexOf(q) >= 0 || featName.indexOf(q) >= 0 || ruleTags.indexOf(q) >= 0;
      var matchRuleTags = !tagFilter.length || tagFilter.every(function (t) { return ruleTags.indexOf(t) >= 0; });
      r.classList.toggle("is-hidden", !(any && matchRuleQuery && matchRuleTags));
    });
    // Hide nested rule containers whose scenarios are all hidden (features view).
    document.querySelectorAll(".rule:not(.card)").forEach(function (r) {
      var any = r.querySelectorAll(".scenario:not(.is-hidden)").length > 0;
      r.classList.toggle("is-hidden", !any);
    });
    // Hide features whose scenarios/rules are all hidden.
    document.querySelectorAll(".feature").forEach(function (f) {
      var anyScenario = f.querySelectorAll(".scenario:not(.is-hidden)").length > 0;
      var anyRule = f.querySelectorAll(".rule:not(.is-hidden)").length > 0;
      var status = f.dataset.status;
      var name = f.dataset.name || "";
      var tags = f.dataset.tags || "";
      var matchStatus = activeStatuses.has(status);
      var matchQuery = !q || name.indexOf(q) >= 0 || tags.indexOf(q) >= 0;
      f.classList.toggle("is-hidden", !(anyScenario || anyRule || (matchStatus && matchQuery)));
    });
  }

  // ---- Counts in chips ---------------------------------------
  (function counts() {
    var stats = (DATA.execution && DATA.execution.statistics && DATA.execution.statistics.by_status) || {};
    document.querySelectorAll("[data-count]").forEach(function (el) {
      el.textContent = String(stats[el.dataset.count] || 0);
    });
  })();

  // ---- Charts ------------------------------------------------
  function statusValues() {
    var s = (DATA.execution && DATA.execution.statistics && DATA.execution.statistics.by_status) || {};
    var order = ["passed", "failed", "skipped", "undefined", "pending"];
    return {
      labels: order.map(function (k) { return cap(k); }),
      values: order.map(function (k) { return s[k] || 0; }),
      colors: order.map(function (k) { return PALETTE[k]; }),
    };
  }

  function flatScenarios() {
    var feats = (DATA.execution && DATA.execution.features) || [];
    var out = [];
    feats.forEach(function (f) { (f.scenarios || []).forEach(function (sc) { out.push(sc); }); });
    return out;
  }

  function renderCharts() {
    var sv = statusValues();
    var pieEl = document.getElementById("chart-status");
    if (pieEl) BMRChart.pie(pieEl, sv);
    var pieEl2 = document.getElementById("chart-status-2");
    if (pieEl2) BMRChart.pie(pieEl2, sv);

    var tl = document.getElementById("chart-timeline");
    if (tl) {
      var pts = flatScenarios().map(function (s) {
        return { duration: s.duration || 0, status: s.status };
      });
      BMRChart.timeline(tl, { points: pts, palette: PALETTE });
    }

    var bk = document.getElementById("chart-buckets");
    if (bk) {
      var b = DATA.buckets || {};
      var labels = Object.keys(b);
      var values = labels.map(function (k) { return b[k]; });
      BMRChart.bar(bk, { labels: labels, values: values, color: PALETTE.passed });
    }

    var sl = document.getElementById("chart-slowest");
    if (sl) {
      var slow = (DATA.slowest || []).slice(0, 5);
      BMRChart.hbar(sl, {
        labels: slow.map(function (s) { return s.name || "(unnamed)"; }),
        values: slow.map(function (s) { return s.duration || 0; }),
        color: PALETTE.failed,
      });
    }

    var tg = document.getElementById("chart-tag-pass");
    if (tg) {
      var worstTags = (DATA.tags || [])
        .filter(function (t) { return t.count >= 1; })
        .sort(function (a, b) { return a.pass_rate - b.pass_rate; })
        .slice(0, 6);
      BMRChart.bar(tg, {
        labels: worstTags.map(function (t) { return "@" + t.name; }),
        values: worstTags.map(function (t) { return t.pass_rate || 0; }),
        colors: worstTags.map(function (t) { return t.pass_rate === 100 ? PALETTE.passed : PALETTE.failed; }),
      });
    }

    var er = document.getElementById("chart-errors");
    if (er) {
      var err = DATA.errors || {};
      var errLabels = Object.keys(err);
      var errValues = errLabels.map(function (k) { return err[k]; });
      BMRChart.bar(er, {
        labels: errLabels.map(function (k) { return k.length > 12 ? k.slice(0, 11) + "…" : k; }),
        values: errValues,
        color: PALETTE.failed,
      });
    }
  }
  function cap(s) { return s.charAt(0).toUpperCase() + s.slice(1); }

  // ---- Initial render ----------------------------------------
  showView("dashboard");
  // Charts need layout; defer to next frame.
  requestAnimationFrame(renderCharts);
  window.addEventListener("resize", debounce(renderCharts, 120));

  function debounce(fn, ms) {
    var t; return function () { clearTimeout(t); t = setTimeout(fn, ms); };
  }
})();

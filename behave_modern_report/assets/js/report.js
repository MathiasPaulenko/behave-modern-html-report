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

  var PALETTE = {
    passed:    getCss("--c-passed",    "#22c55e"),
    failed:    getCss("--c-failed",    "#ef4444"),
    skipped:   getCss("--c-skipped",   "#94a3b8"),
    undefined: getCss("--c-undefined", "#f59e0b"),
    pending:   getCss("--c-pending",   "#8b5cf6"),
    untested:  getCss("--c-untested",  "#64748b"),
  };

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
    var btn = document.getElementById("theme-toggle");
    if (btn) {
      btn.addEventListener("click", function () {
        var cur = document.documentElement.getAttribute("data-theme") || "auto";
        var next = cur === "dark" ? "light" : cur === "light" ? "auto" : "dark";
        applyTheme(next);
        // redraw charts on theme change
        renderCharts();
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
  document.addEventListener("click", function (e) {
    var head = e.target.closest(".feature-head, .scenario-head");
    if (!head) return;
    var body = head.nextElementSibling;
    var expanded = head.getAttribute("aria-expanded") === "true";
    head.setAttribute("aria-expanded", expanded ? "false" : "true");
    if (body) body.hidden = expanded;
  });

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
  filterChips.forEach(function (chip) {
    chip.addEventListener("click", function () {
      var s = chip.dataset.filterStatus;
      if (activeStatuses.has(s)) { activeStatuses.delete(s); chip.setAttribute("aria-pressed", "false"); }
      else { activeStatuses.add(s); chip.setAttribute("aria-pressed", "true"); }
      applyFilters();
    });
  });
  if (searchInput) {
    var t;
    searchInput.addEventListener("input", function () {
      clearTimeout(t); t = setTimeout(applyFilters, 80);
    });
  }
  function applyFilters() {
    var q = (searchInput ? searchInput.value : "").toLowerCase().trim();
    var scenarios = document.querySelectorAll(".scenario");
    scenarios.forEach(function (el) {
      var status = el.dataset.status;
      var name = el.dataset.name || "";
      var tags = el.dataset.tags || "";
      var feat = el.dataset.feature || "";
      var matchStatus = activeStatuses.has(status);
      var matchQuery = !q || name.indexOf(q) >= 0 || tags.indexOf(q) >= 0 || feat.indexOf(q) >= 0;
      el.classList.toggle("is-hidden", !(matchStatus && matchQuery));
    });
    // Hide features whose scenarios are all hidden (when filtering).
    document.querySelectorAll(".feature").forEach(function (f) {
      var any = f.querySelectorAll(".scenario:not(.is-hidden)").length > 0;
      var status = f.dataset.status;
      var name = f.dataset.name || "";
      var tags = f.dataset.tags || "";
      var matchStatus = activeStatuses.has(status);
      var matchQuery = !q || name.indexOf(q) >= 0 || tags.indexOf(q) >= 0;
      f.classList.toggle("is-hidden", !(any || (matchStatus && matchQuery)));
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
      var slow = (DATA.slowest || []).slice(0, 10);
      BMRChart.hbar(sl, {
        labels: slow.map(function (s) { return s.name || "(unnamed)"; }),
        values: slow.map(function (s) { return s.duration || 0; }),
        color: PALETTE.failed,
      });
    }

    var tg = document.getElementById("chart-tag-pass");
    if (tg) {
      var topTags = (DATA.tags || [])
        .sort(function (a, b) { return b.count - a.count; })
        .slice(0, 8);
      BMRChart.bar(tg, {
        labels: topTags.map(function (t) { return "@" + t.name; }),
        values: topTags.map(function (t) { return t.pass_rate || 0; }),
        color: PALETTE.passed,
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

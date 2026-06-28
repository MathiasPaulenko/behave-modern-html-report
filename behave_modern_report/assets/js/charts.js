/* ============================================================
   Behave Modern Report — tiny chart library
   Vanilla, zero-dependency Canvas charts: pie, bar, hbar.
   Exposes window.BMRChart with the small API the report needs.
   ============================================================ */
(function (global) {
  "use strict";

  function css(varName, fallback) {
    var v = getComputedStyle(document.documentElement).getPropertyValue(varName);
    return (v && v.trim()) || fallback;
  }

  function hidpi(canvas) {
    var dpr = window.devicePixelRatio || 1;
    var rect = canvas.getBoundingClientRect();
    var w = rect.width || canvas.width || 320;
    var h = canvas.height ? canvas.height : 200;
    canvas.width = Math.floor(w * dpr);
    canvas.height = Math.floor(h * dpr);
    canvas.style.width = w + "px";
    canvas.style.height = h + "px";
    var ctx = canvas.getContext("2d");
    ctx.setTransform(dpr, 0, 0, dpr, 0, 0);
    return { ctx: ctx, w: w, h: h };
  }

  function textColor()  { return css("--text", "#e5e7eb"); }
  function dimColor()   { return css("--text-dim", "#9ca3af"); }
  function gridColor()  { return css("--border", "#1f2937"); }

  // ----------------------------------------------------------
  // Pie / Donut
  // ----------------------------------------------------------
  function pie(canvas, opts) {
    var d = hidpi(canvas);
    var ctx = d.ctx, w = d.w, h = d.h;
    var labels = opts.labels || [];
    var values = opts.values || [];
    var colors = opts.colors || [];
    var total = values.reduce(function (a, b) { return a + b; }, 0);

    var cx = w * 0.36, cy = h / 2;
    var r = Math.min(w * 0.32, h * 0.42);
    var inner = r * 0.55;

    ctx.clearRect(0, 0, w, h);

    if (total === 0) {
      ctx.fillStyle = dimColor();
      ctx.font = "13px " + css("--font", "system-ui");
      ctx.textAlign = "center";
      ctx.fillText("No data", cx, cy);
      return;
    }

    var start = -Math.PI / 2;
    for (var i = 0; i < values.length; i++) {
      var v = values[i];
      if (!v) continue;
      var angle = (v / total) * Math.PI * 2;
      ctx.beginPath();
      ctx.moveTo(cx, cy);
      ctx.arc(cx, cy, r, start, start + angle);
      ctx.closePath();
      ctx.fillStyle = colors[i] || "#888";
      ctx.fill();
      start += angle;
    }
    // donut hole
    ctx.beginPath();
    ctx.arc(cx, cy, inner, 0, Math.PI * 2);
    ctx.fillStyle = css("--bg-elev", "#111827");
    ctx.fill();

    // center total
    ctx.fillStyle = textColor();
    ctx.font = "700 20px " + css("--font", "system-ui");
    ctx.textAlign = "center";
    ctx.textBaseline = "middle";
    ctx.fillText(String(total), cx, cy - 6);
    ctx.font = "11px " + css("--font", "system-ui");
    ctx.fillStyle = dimColor();
    ctx.fillText("scenarios", cx, cy + 12);

    // legend
    var lx = w * 0.7, ly = 18, line = 22;
    ctx.textAlign = "left";
    ctx.textBaseline = "middle";
    ctx.font = "12px " + css("--font", "system-ui");
    for (var j = 0; j < labels.length; j++) {
      var y = ly + j * line;
      ctx.fillStyle = colors[j] || "#888";
      ctx.fillRect(lx, y - 6, 12, 12);
      ctx.fillStyle = textColor();
      ctx.fillText(labels[j], lx + 18, y);
      ctx.fillStyle = dimColor();
      var pct = total ? ((values[j] / total) * 100).toFixed(1) : "0.0";
      ctx.fillText(values[j] + "  (" + pct + "%)", lx + 18, y + 14);
      ly += 14;
    }
  }

  // ----------------------------------------------------------
  // Bar (vertical)
  // ----------------------------------------------------------
  function bar(canvas, opts) {
    var d = hidpi(canvas);
    var ctx = d.ctx, w = d.w, h = d.h;
    var labels = opts.labels || [];
    var values = opts.values || [];
    var colors = opts.colors;
    var color = opts.color || css("--primary", "#60a5fa");
    var padL = 36, padR = 14, padT = 14, padB = 36;
    var innerW = w - padL - padR, innerH = h - padT - padB;
    var max = Math.max.apply(null, values.concat([1]));

    ctx.clearRect(0, 0, w, h);

    // gridlines
    ctx.strokeStyle = gridColor();
    ctx.fillStyle = dimColor();
    ctx.font = "11px " + css("--font", "system-ui");
    ctx.textAlign = "right";
    ctx.textBaseline = "middle";
    for (var t = 0; t <= 4; t++) {
      var gy = padT + innerH - (innerH * t) / 4;
      ctx.beginPath();
      ctx.moveTo(padL, gy); ctx.lineTo(w - padR, gy);
      ctx.stroke();
      ctx.fillText(String(Math.round((max * t) / 4)), padL - 6, gy);
    }

    if (!values.length) return;
    var gap = 8;
    var bw = (innerW - gap * (values.length - 1)) / values.length;

    ctx.textAlign = "center";
    ctx.textBaseline = "top";
    for (var i = 0; i < values.length; i++) {
      var v = values[i];
      var bh = max > 0 ? (v / max) * innerH : 0;
      var x = padL + i * (bw + gap);
      var y = padT + innerH - bh;
      ctx.fillStyle = (colors && colors[i]) || color;
      roundRect(ctx, x, y, bw, bh, 6);
      ctx.fill();
      ctx.fillStyle = dimColor();
      ctx.fillText(labels[i] || "", x + bw / 2, padT + innerH + 6);
    }
  }

  // ----------------------------------------------------------
  // Horizontal bar
  // ----------------------------------------------------------
  function hbar(canvas, opts) {
    var d = hidpi(canvas);
    var ctx = d.ctx, w = d.w, h = d.h;
    var labels = opts.labels || [];
    var values = opts.values || [];
    var color = opts.color || css("--primary", "#60a5fa");
    var padL = 160, padR = 60, padT = 8, padB = 8;
    var innerW = w - padL - padR;
    var rowH = (h - padT - padB) / Math.max(values.length, 1);
    var max = Math.max.apply(null, values.concat([0.001]));

    ctx.clearRect(0, 0, w, h);
    ctx.font = "12px " + css("--font", "system-ui");
    ctx.textBaseline = "middle";

    for (var i = 0; i < values.length; i++) {
      var v = values[i];
      var y = padT + i * rowH + rowH / 2;
      var bw = max > 0 ? (v / max) * innerW : 0;

      ctx.fillStyle = dimColor();
      ctx.textAlign = "right";
      var label = labels[i] || "";
      if (label.length > 26) label = label.slice(0, 25) + "…";
      ctx.fillText(label, padL - 8, y);

      ctx.fillStyle = color;
      roundRect(ctx, padL, y - rowH * 0.32, Math.max(bw, 2), rowH * 0.64, 4);
      ctx.fill();

      ctx.fillStyle = textColor();
      ctx.textAlign = "left";
      ctx.fillText(formatDuration(v), padL + bw + 6, y);
    }
  }

  // ----------------------------------------------------------
  // Timeline (sequential scenarios by index, colored by status)
  // ----------------------------------------------------------
  function timeline(canvas, opts) {
    var d = hidpi(canvas);
    var ctx = d.ctx, w = d.w, h = d.h;
    var points = opts.points || []; // [{duration, status}]
    var palette = opts.palette || {};
    var padL = 32, padR = 12, padT = 12, padB = 24;
    var innerW = w - padL - padR, innerH = h - padT - padB;
    var max = Math.max.apply(null, points.map(function (p) { return p.duration; }).concat([0.001]));

    ctx.clearRect(0, 0, w, h);

    // baseline
    ctx.strokeStyle = gridColor();
    ctx.beginPath(); ctx.moveTo(padL, padT + innerH); ctx.lineTo(w - padR, padT + innerH); ctx.stroke();

    if (!points.length) {
      ctx.fillStyle = dimColor();
      ctx.font = "13px " + css("--font", "system-ui");
      ctx.textAlign = "center";
      ctx.fillText("No scenarios", w / 2, h / 2);
      return;
    }

    var bw = Math.max(2, innerW / points.length - 1);
    for (var i = 0; i < points.length; i++) {
      var p = points[i];
      var bh = max > 0 ? (p.duration / max) * innerH : 0;
      var x = padL + (i / points.length) * innerW;
      var y = padT + innerH - bh;
      ctx.fillStyle = palette[p.status] || css("--text-faint", "#64748b");
      ctx.fillRect(x, y, bw, Math.max(bh, 2));
    }
  }

  // ----------------------------------------------------------
  // Helpers
  // ----------------------------------------------------------
  function roundRect(ctx, x, y, w, h, r) {
    r = Math.min(r, w / 2, h / 2);
    ctx.beginPath();
    ctx.moveTo(x + r, y);
    ctx.arcTo(x + w, y, x + w, y + h, r);
    ctx.arcTo(x + w, y + h, x, y + h, r);
    ctx.arcTo(x, y + h, x, y, r);
    ctx.arcTo(x, y, x + w, y, r);
    ctx.closePath();
  }

  function formatDuration(s) {
    if (s < 1) return Math.round(s * 1000) + "ms";
    if (s < 60) return s.toFixed(2) + "s";
    var m = Math.floor(s / 60), sec = Math.round(s - m * 60);
    return m + "m " + sec + "s";
  }

  global.BMRChart = { pie: pie, bar: bar, hbar: hbar, timeline: timeline };
})(window);

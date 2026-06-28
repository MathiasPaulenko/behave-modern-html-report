# Architecture

`behave-modern-report` follows a strict layered architecture.
Each layer has a single responsibility and depends only on the layers above it.

```text
┌──────────────────────────────────────────┐
│  formatter.py   (Behave adapter)         │  ← only this layer knows about Behave
├──────────────────────────────────────────┤
│  collector.py   (event → model builder)  │
├──────────────────────────────────────────┤
│  models.py      (pure dataclasses)       │  ← no I/O, no framework imports
│  statistics.py  (aggregations)           │
├──────────────────────────────────────────┤
│  renderer.py    (Jinja2 → single HTML)   │
│  assets.py      (CSS/JS bundling)        │
│  templates/     (HTML components)        │
│  assets/        (CSS / JS / icons)       │
└──────────────────────────────────────────┘
```

## Why this matters

- **Testability** — every layer can be tested in isolation.
  The collector accepts duck-typed objects, so we test it with `SimpleNamespace`
  stubs (see `tests/test_collector.py`). The renderer accepts an `Execution`
  object, so we test it without ever running Behave.
- **Reusability** — anyone with a JSON Behave report (or any execution data)
  can build an `Execution` and render the same beautiful HTML.
- **Future-proofing** — adding features like PDF export, report comparison,
  or a plugin system only touches one layer.

## Data flow

1. Behave invokes the formatter for each feature/scenario/step result.
2. The formatter delegates to a `Collector`, which builds an
   `Execution` tree of dataclasses.
3. On `close()`, the formatter calls `Collector.finalize()` which runs
   `statistics.compute()` to derive aggregates.
4. A `Renderer` loads Jinja2 templates and the bundled CSS/JS, embeds
   everything (and the execution as JSON for client-side rendering),
   and writes a single `.html` file.

## Single-file guarantee

The renderer never references external URLs. CSS, JS, icons (inline SVG sprite),
attachments (base64) and the execution payload (JSON `<script>`) are all
embedded. The output file works offline forever.

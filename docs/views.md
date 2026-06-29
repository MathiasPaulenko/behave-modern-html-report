# Report views

The generated report is a single-page application with a sidebar navigation menu.
Each view shows a different slice of the execution data.

## Dashboard

High-level summary: total scenarios, pass rate, status distribution, duration
histogram, slowest scenarios, tag pass rate, and error distribution. It also
includes a one-click copy summary for Slack or other chat tools.

## Features

List of all features with status badges, tags, description, and duration. Expand
a feature to see its scenarios. Use the Compact/Detailed toggle to show or hide
rule and scenario details.

## Rules

All Gherkin `Rule` groups across every feature in one place. Each rule shows its
scenarios and aggregated status. Behave 1.3.x is required for `Rule` support.

## Scenarios

All scenarios as collapsible cards with steps, attachments, error traces, and
background steps. The Compact/Detailed toggle hides or shows background,
scenario outline banners and examples tables.

## Results

A compact table of all scenarios with status, feature, rule, duration, and tags.
Useful for quickly scanning outcomes without expanding individual scenarios.

## Tags

Per-tag analytics: scenario count, pass rate, accumulated duration, and a
sortable table. There is no separate chart; the pass rate is shown inline in
the table with color-coded bars.

## Statistics

Raw metrics and distribution tables: status distribution, duration percentiles
(min, avg, p50, p90, p95, max), per-feature summary, and error distribution by
exception type.

## Environment

Host and runtime information captured at execution time: Python and Behave
versions, platform, hostname, user, CPU count, memory, git branch/commit/remote,
selected environment variables, and custom extra fields.

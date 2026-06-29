# Configuration

All reporter options are read from `behave`'s `userdata` section. They can be set
in `behave.ini`, `setup.cfg`, or programmatically from `environment.py`.

## Options

- `bmr.title` — default `Behave Modern Report`. Report title shown in the sidebar, header and browser tab.
- `bmr.company` — default empty. Company name shown under the title in the sidebar.
- `bmr.theme` — default `auto`. Choose `light`, `dark` or `auto`.
- `bmr.logo` — default empty. URL or base64 data URI for a logo image in the sidebar.
- `bmr.custom_css` — default empty. Path to a custom CSS file to embed into the report.
- `bmr.custom_js` — default empty. Path to a custom JavaScript file to embed into the report.
- `bmr.json_sidecar` — default `false`. Also write a `.json` file next to the HTML report.

## Example `behave.ini`

```ini
[behave]
format = modern
outfiles = report.html
show_skipped = true
show_timings = true

[behave.formatters]
modern = behave_modern_html_report.formatter:ModernHTMLFormatter

[behave.userdata]
bmr.title = My Suite
bmr.company = Acme Inc.
bmr.theme = auto
bmr.json_sidecar = true
```

## Setting options from `environment.py`

```python
from behave import use_fixture

def before_all(context):
    context.config.userdata.set("bmr.title", "API Tests")
    context.config.userdata.set("bmr.company", "Acme Inc.")
    context.config.userdata.set("bmr.theme", "dark")
```

## Custom CSS / JS

The reporter embeds the contents of the given files into the final HTML. This
is useful for company branding or small UI tweaks. The files must be readable
from the working directory where Behave runs.

```ini
[behave.userdata]
bmr.custom_css = assets/branding.css
bmr.custom_js = assets/monitoring.js
```

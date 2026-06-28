from behave_modern_html_report.renderer import Renderer, RenderOptions


def test_renderer_produces_single_html_file(tmp_path, sample_execution):
    r = Renderer(RenderOptions(title="Demo", company="Acme", theme="dark"))
    out = r.render_to_file(sample_execution, tmp_path / "report.html")

    html = out.read_text(encoding="utf-8")
    assert html.startswith("<!doctype html>")
    # Title and company appear
    assert "Demo" in html
    assert "Acme" in html
    # Assets are inlined (no external references that would need network).
    assert "<link " not in html
    assert "src=\"http" not in html
    # Embedded JSON payload present.
    assert "bmr-data" in html
    # Scenario name is present.
    assert "Customer buys a book" in html
    # Failing scenario traceback present.
    assert "Card expired" in html


def test_renderer_supports_custom_css_js(tmp_path, sample_execution):
    r = Renderer(RenderOptions(custom_css=".bmr-x{color:red}", custom_js="window.__bmr=1;"))
    html = r.render(sample_execution)
    assert ".bmr-x{color:red}" in html
    assert "window.__bmr=1;" in html


def test_renderer_handles_empty_execution(tmp_path):
    from behave_modern_html_report.models import Execution

    html = Renderer().render(Execution())
    assert "<!doctype html>" in html


def test_renderer_includes_tags_page(sample_execution):
    html = Renderer().render(sample_execution)
    assert "Tags" in html
    assert "chart-tag-pass" in html
    assert "data-view=\"tags\"" in html


def test_renderer_json_sidecar(sample_execution, tmp_path):
    r = Renderer(RenderOptions(json_sidecar=True))
    out = r.render_to_file(sample_execution, tmp_path / "report.html")
    json_path = out.with_suffix(".json")
    assert json_path.exists()
    text = json_path.read_text(encoding="utf-8")
    assert "execution" in text
    assert "tags" in text


def test_renderer_json_method(sample_execution):
    json_text = Renderer().render_json(sample_execution)
    assert "\"tags\"" in json_text
    assert "\"execution\"" in json_text

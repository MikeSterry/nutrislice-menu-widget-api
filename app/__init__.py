from __future__ import annotations
from flask import current_app

def include(path: str) -> str:
    # Render an SVG file from templates/icons
    from flask import render_template
    return render_template(path)

def register_template_helpers(app):
    @app.context_processor
    def _inject():
        return {"include": include}

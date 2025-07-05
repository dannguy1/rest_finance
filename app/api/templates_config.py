"""
Templates configuration for the application.
"""
from fastapi.templating import Jinja2Templates
from pathlib import Path

# Setup templates
templates_path = Path(__file__).parent.parent / "templates"
templates = Jinja2Templates(
    directory=str(templates_path),
    auto_reload=True,
    autoescape=True,
    trim_blocks=True,
    lstrip_blocks=True
) 
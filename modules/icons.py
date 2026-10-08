# ====================================================================
# modules/icons.py
# Lucide Icons SVG Utility for Varanasi Dashboard
# ====================================================================

LUCIDE_ICONS = {
    "layout-dashboard": """<svg xmlns="http://www.w3.org/2000/svg" width="{size}" height="{size}" viewBox="0 0 24 24" fill="none" stroke="{color}" stroke-width="{stroke_width}" stroke-linecap="round" stroke-linejoin="round" class="lucide lucide-layout-dashboard" style="{style}"><rect width="7" height="9" x="3" y="3" rx="1"/><rect width="7" height="5" x="14" y="3" rx="1"/><rect width="7" height="9" x="14" y="12" rx="1"/><rect width="7" height="5" x="3" y="16" rx="1"/></svg>""",
    
    "home": """<svg xmlns="http://www.w3.org/2000/svg" width="{size}" height="{size}" viewBox="0 0 24 24" fill="none" stroke="{color}" stroke-width="{stroke_width}" stroke-linecap="round" stroke-linejoin="round" class="lucide lucide-home" style="{style}"><path d="m3 9 9-7 9 7v11a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2z"/><polyline points="9 22 9 12 15 12 15 22"/></svg>""",
    
    "map": """<svg xmlns="http://www.w3.org/2000/svg" width="{size}" height="{size}" viewBox="0 0 24 24" fill="none" stroke="{color}" stroke-width="{stroke_width}" stroke-linecap="round" stroke-linejoin="round" class="lucide lucide-map" style="{style}"><polygon points="3 6 9 3 15 6 21 3 21 18 15 21 9 18 3 21"/><line x1="9" x2="9" y1="3" y2="18"/><line x1="15" x2="15" y1="6" y2="21"/></svg>""",
    
    "bar-chart-3": """<svg xmlns="http://www.w3.org/2000/svg" width="{size}" height="{size}" viewBox="0 0 24 24" fill="none" stroke="{color}" stroke-width="{stroke_width}" stroke-linecap="round" stroke-linejoin="round" class="lucide lucide-bar-chart-3" style="{style}"><path d="M3 3v18h18"/><path d="M18 17V9"/><path d="M13 17V5"/><path d="M8 17v-3"/></svg>""",
    
    "leaf": """<svg xmlns="http://www.w3.org/2000/svg" width="{size}" height="{size}" viewBox="0 0 24 24" fill="none" stroke="{color}" stroke-width="{stroke_width}" stroke-linecap="round" stroke-linejoin="round" class="lucide lucide-leaf" style="{style}"><path d="M11 20A7 7 0 0 1 9.8 6.1C15.5 5 17 4.48 19 2c1 2 2 4.18 2 8 0 5.5-4.78 10-10 10Z"/><path d="M2 21c0-3 1.85-5.36 5.08-6C9.5 14.52 12 13 13 12"/></svg>""",

    "panel-left": """<svg xmlns="http://www.w3.org/2000/svg" width="{size}" height="{size}" viewBox="0 0 24 24" fill="none" stroke="{color}" stroke-width="{stroke_width}" stroke-linecap="round" stroke-linejoin="round" class="lucide lucide-panel-left" style="{style}"><rect width="18" height="18" x="3" y="3" rx="2"/><path d="M9 3v18"/></svg>""",
    "panel_left": """<svg xmlns="http://www.w3.org/2000/svg" width="{size}" height="{size}" viewBox="0 0 24 24" fill="none" stroke="{color}" stroke-width="{stroke_width}" stroke-linecap="round" stroke-linejoin="round" class="lucide lucide-panel-left" style="{style}"><rect width="18" height="18" x="3" y="3" rx="2"/><path d="M9 3v18"/></svg>""",
    "PanelLeft": """<svg xmlns="http://www.w3.org/2000/svg" width="{size}" height="{size}" viewBox="0 0 24 24" fill="none" stroke="{color}" stroke-width="{stroke_width}" stroke-linecap="round" stroke-linejoin="round" class="lucide lucide-panel-left" style="{style}"><rect width="18" height="18" x="3" y="3" rx="2"/><path d="M9 3v18"/></svg>"""
}

def get_lucide_icon(name="layout-dashboard", size=24, color="currentColor", stroke_width=2, style="vertical-align: middle; display: inline-block;"):
    """
    Returns an inline SVG string for the requested Lucide icon.
    """
    svg_template = LUCIDE_ICONS.get(name, LUCIDE_ICONS["layout-dashboard"])
    return svg_template.format(size=size, color=color, stroke_width=stroke_width, style=style)

"""
SVG Vector Icon Library for InterviewIQ.
Provides 40+ zero-dependency, resolution-independent vector icons
(Lucide / Feather SVG standard).
Eliminates inconsistent cross-platform emoji rendering and supports
CSS currentColor inheritance.
"""

from typing import Dict, Optional


class IconLibrary:
    """
    Zero-dependency inline SVG vector icon repository.
    Renders identically across Windows, macOS, Linux, and Mobile browsers.
    """

    ICONS: Dict[str, str] = {
        # Core Navigation & Placement
        "target": """<circle cx="12" cy="12" r="10"></circle><circle cx="12" cy="12" r="6"></circle><circle cx="12" cy="12" r="2"></circle>""",
        "file_text": """<path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"></path><polyline points="14 2 14 8 20 8"></polyline><line x1="16" y1="13" x2="8" y2="13"></line><line x1="16" y1="17" x2="8" y2="17"></line><polyline points="10 9 9 9 8 9"></polyline>""",
        "briefcase": """<rect x="2" y="7" width="20" height="14" rx="2" ry="2"></rect><path d="M16 21V5a2 2 0 0 0-2-2h-4a2 2 0 0 0-2 2v16"></path>""",
        "award": """<circle cx="12" cy="8" r="7"></circle><polyline points="8.21 13.89 7 23 12 20 17 23 15.79 13.88"></polyline>""",
        "bot": """<rect x="3" y="11" width="18" height="10" rx="2"></rect><circle cx="12" cy="5" r="2"></circle><path d="M12 7v4"></path><line x1="8" y1="16" x2="8" y2="16"></line><line x1="16" y1="16" x2="16" y2="16"></line>""",
        "bar_chart": """<line x1="18" y1="20" x2="18" y2="10"></line><line x1="12" y1="20" x2="12" y2="4"></line><line x1="6" y1="20" x2="6" y2="14"></line>""",
        "calendar": """<rect x="3" y="4" width="18" height="18" rx="2" ry="2"></rect><line x1="16" y1="2" x2="16" y2="6"></line><line x1="8" y1="2" x2="8" y2="6"></line><line x1="3" y1="10" x2="21" y2="10"></line>""",
        "dollar_sign": """<line x1="12" y1="1" x2="12" y2="23"></line><path d="M17 5H9.5a3.5 3.5 0 0 0 0 7h5a3.5 3.5 0 0 1 0 7H6"></path>""",
        "shield": """<path d="M12 22s8-4 8-10V5l-8-3-8 3v7c0 6 8 10 8 10z"></path>""",
        "users": """<path d="M17 21v-2a4 4 0 0 0-4-4H5a4 4 0 0 0-4 4v2"></path><circle cx="9" cy="7" r="4"></circle><path d="M23 21v-2a4 4 0 0 0-3-3.87"></path><path d="M16 3.13a4 4 0 0 1 0 7.75"></path>""",

        # Audio, Speech & Controls
        "mic": """<path d="M12 1a3 3 0 0 0-3 3v8a3 3 0 0 0 6 0V4a3 3 0 0 0-3-3z"></path><path d="M19 10v2a7 7 0 0 1-14 0v-2"></path><line x1="12" y1="19" x2="12" y2="23"></line><line x1="8" y1="23" x2="16" y2="23"></line>""",
        "volume_2": """<polygon points="11 5 6 9 2 9 2 15 6 15 11 19 11 5"></polygon><path d="M19.07 4.93a10 10 0 0 1 0 14.14M15.54 8.46a5 5 0 0 1 0 7.07"></path>""",
        "play": """<polygon points="5 3 19 12 5 21 5 3"></polygon>""",
        "square": """<rect x="3" y="3" width="18" height="18" rx="2" ry="2"></rect>""",
        "clock": """<circle cx="12" cy="12" r="10"></circle><polyline points="12 6 12 12 16 14"></polyline>""",
        "download": """<path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4"></path><polyline points="7 10 12 15 17 10"></polyline><line x1="12" y1="15" x2="12" y2="3"></line>""",
        "refresh": """<polyline points="23 4 23 10 17 10"></polyline><polyline points="1 20 1 14 7 14"></polyline><path d="M3.51 9a9 9 0 0 1 14.85-3.36L23 10M1 14l4.64 4.36A9 9 0 0 0 20.49 15"></path>""",
        "external_link": """<path d="M18 13v6a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2V8a2 2 0 0 1 2-2h6"></path><polyline points="15 3 21 3 21 9"></polyline><line x1="10" y1="14" x2="21" y2="3"></line>""",

        # Status & Diagnostics
        "check_circle": """<path d="M22 11.08V12a10 10 0 1 1-5.93-9.14"></path><polyline points="22 4 12 14.01 9 11.01"></polyline>""",
        "check": """<polyline points="20 6 9 17 4 12"></polyline>""",
        "alert_triangle": """<path d="M10.29 3.86L1.82 18a2 2 0 0 0 1.71 3h16.94a2 2 0 0 0 1.71-3L13.71 3.86a2 2 0 0 0-3.42 0z"></path><line x1="12" y1="9" x2="12" y2="13"></line><line x1="12" y1="17" x2="12.01" y2="17"></line>""",
        "x_circle": """<circle cx="12" cy="12" r="10"></circle><line x1="15" y1="9" x2="9" y2="15"></line><line x1="9" y1="9" x2="15" y2="15"></line>""",
        "info": """<circle cx="12" cy="12" r="10"></circle><line x1="12" y1="16" x2="12" y2="12"></line><line x1="12" y1="8" x2="12.01" y2="8"></line>""",
        "trending_up": """<polyline points="23 6 13.5 15.5 8.5 10.5 1 18"></polyline><polyline points="17 6 23 6 23 12"></polyline>""",
        "activity": """<polyline points="22 12 18 12 15 21 9 3 6 12 2 12"></polyline>""",

        # Security & Identity
        "key": """<path d="M21 2l-2 2m-1.5 1.5L14 9l-1.5-1.5L11 9l-1.5-1.5L8 9 2 15v7h7l6-6 1.5 1.5 1.5-1.5 1.5 1.5 1.5-1.5 2-2z"></path>""",
        "lock": """<rect x="3" y="11" width="18" height="11" rx="2" ry="2"></rect><path d="M7 11V7a5 5 0 0 1 10 0v4"></path>""",
        "unlock": """<rect x="3" y="11" width="18" height="11" rx="2" ry="2"></rect><path d="M7 11V7a5 5 0 0 1 9.9-1"></path>""",

        # Tech, Learning & Execution
        "zap": """<polygon points="13 2 3 14 12 14 11 22 21 10 12 10 13 2"></polygon>""",
        "sparkles": """<path d="M12 3l1.912 5.885L20 10.5l-5.088 1.615L13 18l-1.912-5.885L6 10.5l5.088-1.615L12 3z"></path>""",
        "cpu": """<rect x="4" y="4" width="16" height="16" rx="2" ry="2"></rect><rect x="9" y="9" width="6" height="6"></rect><line x1="9" y1="1" x2="9" y2="4"></line><line x1="15" y1="1" x2="15" y2="4"></line><line x1="9" y1="20" x2="9" y2="23"></line><line x1="15" y1="20" x2="15" y2="23"></line><line x1="20" y1="9" x2="23" y2="9"></line><line x1="20" y1="14" x2="23" y2="14"></line><line x1="1" y1="9" x2="4" y2="9"></line><line x1="1" y1="14" x2="4" y2="14"></line>""",
        "database": """<ellipse cx="12" cy="5" rx="9" ry="3"></ellipse><path d="M21 12c0 1.66-4 3-9 3s-9-1.34-9-3"></path><path d="M3 5v14c0 1.66 4 3 9 3s9-1.34 9-3V5"></path>""",
        "book_open": """<path d="M2 3h6a4 4 0 0 1 4 4v14a3 3 0 0 0-3-3H2z"></path><path d="M22 3h-6a4 4 0 0 0-4 4v14a3 3 0 0 1 3-3h7z"></path>""",
        "graduation_cap": """<path d="M22 10v6M2 10l10-5 10 5-10 5z"></path><path d="M6 12v5c3 3 9 3 12 0v-5"></path>""",
        "message_square": """<path d="M21 15a2 2 0 0 1-2 2H7l-4 4V5a2 2 0 0 1 2-2h14a2 2 0 0 1 2 2z"></path>""",
        "chevron_right": """<polyline points="9 18 15 12 9 6"></polyline>""",
        "arrow_right": """<line x1="5" y1="12" x2="19" y2="12"></line><polyline points="12 5 19 12 12 19"></polyline>""",

        # Devices & Viewports
        "smartphone": """<rect x="5" y="2" width="14" height="20" rx="2" ry="2"></rect><line x1="12" y1="18" x2="12.01" y2="18"></line>""",
        "tablet": """<rect x="4" y="2" width="16" height="20" rx="2" ry="2"></rect><line x1="12" y1="18" x2="12.01" y2="18"></line>""",
        "monitor": """<rect x="2" y="3" width="20" height="14" rx="2" ry="2"></rect><line x1="8" y1="21" x2="16" y2="21"></line><line x1="12" y1="17" x2="12" y2="21"></line>"""
    }

    @classmethod
    def get(
        cls,
        name: str,
        size: int = 18,
        color: str = "currentColor",
        stroke_width: float = 2.0,
        class_name: str = "",
        style: str = ""
    ) -> str:
        """
        Renders an inline SVG icon with customizable size, stroke, and color.
        Defaults to 'target' icon if requested name is unrecognized.
        """
        key = name.lower().replace("-", "_")
        body = cls.ICONS.get(key, cls.ICONS["target"])
        classes = f" class='ui-svg-icon {class_name}'" if class_name else " class='ui-svg-icon'"
        extra_style = f" {style}" if style else ""

        return (
            f"<svg xmlns='http://www.w3.org/2000/svg' width='{size}' height='{size}' "
            f"viewBox='0 0 24 24' fill='none' stroke='{color}' stroke-width='{stroke_width}' "
            f"stroke-linecap='round' stroke-linejoin='round'{classes} style='display:inline-block; vertical-align:middle;{extra_style}'>"
            f"{body}</svg>"
        )


def icon(name: str, size: int = 18, color: str = "currentColor", stroke_width: float = 2.0, class_name: str = "", style: str = "") -> str:
    """Convenience helper to render SVG vector icons."""
    return IconLibrary.get(name, size=size, color=color, stroke_width=stroke_width, class_name=class_name, style=style)

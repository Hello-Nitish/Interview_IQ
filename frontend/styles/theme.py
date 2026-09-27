"""
Design Tokens & Centralized Theme Engine for InterviewIQ.
Provides a single source of truth for colors, typography, elevations,
border radii, and micro-interaction timings.
Enables future-proof global style adjustments and dark mode readiness.
"""

from typing import Dict, Any


class Theme:
    """
    Design System Tokens for InterviewIQ Executive B2B Platform.
    Adheres to high-contrast WCAG AAA readability and Neumorphic Glass aesthetics.
    """

    # 1. Color Palette
    COLORS: Dict[str, str] = {
        # Primary Brand Accents
        "primary": "#2563EB",            # Executive Blue
        "primary_hover": "#1D4ED8",      # Darker Blue
        "primary_light": "#EFF6FF",      # Soft Tint
        "primary_border": "#BFDBFE",     # Border Tint
        "primary_gradient": "linear-gradient(135deg, #2563EB 0%, #1D4ED8 100%)",

        # Secondary / Tech Accent
        "secondary": "#6366F1",          # Indigo
        "secondary_light": "#EEF2FF",

        # Neutral Backgrounds & Canvas
        "bg_canvas": "#F8FAFC",          # Slate 50
        "bg_surface": "#FFFFFF",         # Pure White
        "bg_surface_hover": "#FAFCFF",   # Hover Surface
        "bg_recessed": "#F1F5F9",        # Slate 100 Inset
        "bg_sidebar": "#FFFFFF",

        # Borders & Dividers
        "border_light": "#E2E8F0",       # Slate 200
        "border_medium": "#CBD5E1",      # Slate 300
        "border_focus": "#2563EB",

        # High-Contrast Typography
        "text_heading": "#0F172A",       # Slate 900 (Guaranteed high-contrast)
        "text_body": "#1E293B",          # Slate 800
        "text_muted": "#64748B",         # Slate 500
        "text_subtle": "#94A3B8",        # Slate 400
        "text_inverse": "#FFFFFF",       # Pure White for dark buttons

        # Semantic Status Indicators
        "success": "#10B981",            # Emerald
        "success_bg": "#ECFDF5",
        "success_border": "#A7F3D0",

        "warning": "#F59E0B",            # Amber
        "warning_bg": "#FFFBEB",
        "warning_border": "#FDE68A",

        "danger": "#EF4444",             # Rose / Red
        "danger_bg": "#FEF2F2",
        "danger_border": "#FECACA",

        "info": "#3B82F6",               # Sky Blue
        "info_bg": "#EFF6FF",
        "info_border": "#BFDBFE"
    }

    # 2. Elevation & Shadow Tokens
    SHADOWS: Dict[str, str] = {
        "none": "none",
        "sm": "0 1px 2px 0 rgba(15, 23, 42, 0.05)",
        "card": "0 4px 20px -2px rgba(15, 23, 42, 0.06), 0 2px 6px -1px rgba(15, 23, 42, 0.02)",
        "card_hover": "0 10px 25px -4px rgba(15, 23, 42, 0.09), 0 4px 10px -2px rgba(15, 23, 42, 0.03)",
        "modal": "0 20px 25px -5px rgba(15, 23, 42, 0.1), 0 10px 10px -5px rgba(15, 23, 42, 0.04)",
        "inset": "inset 0 2px 4px 0 rgba(15, 23, 42, 0.05)",
        "glow_primary": "0 0 14px rgba(37, 99, 235, 0.35)",
        "glow_success": "0 0 14px rgba(16, 185, 129, 0.35)"
    }

    # 3. Border Radii
    RADII: Dict[str, str] = {
        "xs": "4px",
        "sm": "6px",
        "md": "10px",
        "lg": "14px",
        "xl": "18px",
        "2xl": "24px",
        "full": "9999px"
    }

    # 4. Spacing Scale (8px Grid Standard)
    SPACING: Dict[str, str] = {
        "2xs": "2px",
        "xs": "4px",
        "sm": "8px",
        "md": "12px",
        "lg": "16px",
        "xl": "20px",
        "2xl": "24px",
        "3xl": "32px",
        "4xl": "48px"
    }

    # 5. Transitions & Micro-Interaction Timings
    TRANSITIONS: Dict[str, str] = {
        "fast": "all 0.15s cubic-bezier(0.4, 0, 0.2, 1)",
        "normal": "all 0.2s cubic-bezier(0.4, 0, 0.2, 1)",
        "smooth": "all 0.3s cubic-bezier(0.4, 0, 0.2, 1)",
        "bounce": "all 0.25s cubic-bezier(0.175, 0.885, 0.32, 1.275)"
    }

    # 6. Typography Stacks
    FONTS: Dict[str, str] = {
        "sans": "'Inter', -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Helvetica, Arial, sans-serif",
        "mono": "ui-monospace, SFMono-Regular, Menlo, Monaco, Consolas, 'Liberation Mono', monospace"
    }

    @classmethod
    def generate_css_variables(cls) -> str:
        """
        Generates the standard CSS :root variables block from design tokens.
        Ensures 100% synchronization between Python constants and frontend CSS.
        """
        lines = [":root {"]
        for key, val in cls.COLORS.items():
            lines.append(f"  --color-{key.replace('_', '-')}: {val};")
        for key, val in cls.SHADOWS.items():
            lines.append(f"  --shadow-{key.replace('_', '-')}: {val};")
        for key, val in cls.RADII.items():
            lines.append(f"  --radius-{key}: {val};")
        for key, val in cls.SPACING.items():
            lines.append(f"  --space-{key}: {val};")
        for key, val in cls.TRANSITIONS.items():
            lines.append(f"  --transition-{key}: {val};")
        lines.append(f"  --font-sans: {cls.FONTS['sans']};")
        lines.append(f"  --font-mono: {cls.FONTS['mono']};")
        lines.append("}")
        return "\n".join(lines)

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

    # 7. Responsive Breakpoints
    BREAKPOINTS: Dict[str, str] = {
        "mobile_sm": "360px",
        "mobile": "480px",
        "tablet": "768px",
        "tablet_lg": "1024px",
        "desktop": "1200px"
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
        for key, val in cls.BREAKPOINTS.items():
            lines.append(f"  --breakpoint-{key.replace('_', '-')}: {val};")
        lines.append(f"  --font-sans: {cls.FONTS['sans']};")
        lines.append(f"  --font-mono: {cls.FONTS['mono']};")
        lines.append("}")
        return "\n".join(lines)

    @classmethod
    def get_view_mode_css(cls, mode: str) -> str:
        """
        Generates dynamic viewport constraint CSS for simulating Mobile, Tablet,
        or Desktop modes directly within desktop browsers, with forced column stacking
        and device frame rendering.
        """
        norm_mode = (mode or "").lower()
        if "mobile" in norm_mode:
            return """
            /* === Simulated Mobile Viewport Frame (iPhone/Android ~390px) === */
            [data-testid="stAppViewContainer"] > .main {
                background: #E2E8F0 !important;
                background-image: radial-gradient(#CBD5E1 1.2px, transparent 1.2px) !important;
                background-size: 16px 16px !important;
            }
            .main .block-container,
            [data-testid="stMainBlockContainer"] {
                max-width: min(420px, calc(100vw - 20px)) !important;
                width: 100% !important;
                margin: 20px auto 40px auto !important;
                padding: 20px 14px 36px 14px !important;
                background: #F8FAFC !important;
                border-radius: 36px !important;
                border: 3px solid #0F172A !important;
                box-shadow: 0 25px 50px -12px rgba(15, 23, 42, 0.35), 0 0 0 1px rgba(15, 23, 42, 0.1) !important;
                box-sizing: border-box !important;
                position: relative !important;
                transition: all 0.25s cubic-bezier(0.4, 0, 0.2, 1) !important;
            }
            .main .block-container::before,
            [data-testid="stMainBlockContainer"]::before {
                content: "📱 Mobile Preview (390 × 844 px)" !important;
                display: block !important;
                text-align: center !important;
                font-size: 0.7rem !important;
                font-weight: 700 !important;
                letter-spacing: 0.04em !important;
                color: #475569 !important;
                background: #E2E8F0 !important;
                border: 1px solid #CBD5E1 !important;
                border-radius: 9999px !important;
                padding: 4px 14px !important;
                margin: 0 auto 16px auto !important;
                width: fit-content !important;
            }
            .main .block-container::after,
            [data-testid="stMainBlockContainer"]::after {
                content: "" !important;
                display: block !important;
                width: 120px !important;
                height: 4px !important;
                background: #0F172A !important;
                border-radius: 9999px !important;
                margin: 28px auto 6px auto !important;
                opacity: 0.5 !important;
            }
            /* Force single-column stacking in mobile simulation */
            [data-testid="stHorizontalBlock"] {
                flex-direction: column !important;
                gap: 12px !important;
            }
            [data-testid="stHorizontalBlock"] > [data-testid="column"] {
                width: 100% !important;
                min-width: 100% !important;
                flex: 1 1 100% !important;
                margin-bottom: 6px !important;
            }
            h1, .stMarkdown h1, [data-testid="stMarkdownContainer"] h1 {
                font-size: 1.35rem !important;
                line-height: 1.25 !important;
            }
            h2, .stMarkdown h2, [data-testid="stMarkdownContainer"] h2 {
                font-size: 1.15rem !important;
                line-height: 1.3 !important;
            }
            h3, .stMarkdown h3, [data-testid="stMarkdownContainer"] h3 {
                font-size: 1.05rem !important;
            }
            p, span, label, [data-testid="stMarkdownContainer"] p {
                font-size: 0.88rem !important;
                line-height: 1.45 !important;
            }
            .neuro-card {
                padding: 14px 14px !important;
                margin-bottom: 12px !important;
                border-radius: 12px !important;
            }
            .neuro-inset {
                padding: 12px 12px !important;
                margin-bottom: 10px !important;
                border-radius: 10px !important;
            }
            .stButton > button, [data-testid="stFormSubmitButton"] button {
                width: 100% !important;
                min-height: 44px !important;
                padding: 10px 14px !important;
                font-size: 0.88rem !important;
            }
            .culture-grid {
                grid-template-columns: 1fr !important;
            }
            """
        elif "tablet" in norm_mode:
            return """
            /* === Simulated Tablet Viewport Frame (iPad ~820px) === */
            [data-testid="stAppViewContainer"] > .main {
                background: #F1F5F9 !important;
                background-image: radial-gradient(#CBD5E1 1.2px, transparent 1.2px) !important;
                background-size: 18px 18px !important;
            }
            .main .block-container,
            [data-testid="stMainBlockContainer"] {
                max-width: min(820px, calc(100vw - 32px)) !important;
                width: 100% !important;
                margin: 24px auto 40px auto !important;
                padding: 24px 22px 36px 22px !important;
                background: #F8FAFC !important;
                border-radius: 24px !important;
                border: 2px solid #334155 !important;
                box-shadow: 0 20px 45px -10px rgba(15, 23, 42, 0.22), 0 0 0 1px rgba(15, 23, 42, 0.08) !important;
                box-sizing: border-box !important;
                position: relative !important;
                transition: all 0.25s cubic-bezier(0.4, 0, 0.2, 1) !important;
            }
            .main .block-container::before,
            [data-testid="stMainBlockContainer"]::before {
                content: "📟 Tablet Preview (820 × 1180 px)" !important;
                display: block !important;
                text-align: center !important;
                font-size: 0.72rem !important;
                font-weight: 700 !important;
                letter-spacing: 0.04em !important;
                color: #475569 !important;
                background: #E2E8F0 !important;
                border: 1px solid #CBD5E1 !important;
                border-radius: 9999px !important;
                padding: 4px 14px !important;
                margin: 0 auto 18px auto !important;
                width: fit-content !important;
            }
            [data-testid="stHorizontalBlock"] {
                flex-wrap: wrap !important;
                gap: 14px !important;
            }
            [data-testid="stHorizontalBlock"] > [data-testid="column"] {
                min-width: calc(50% - 14px) !important;
                flex: 1 1 calc(50% - 14px) !important;
            }
            h1, .stMarkdown h1, [data-testid="stMarkdownContainer"] h1 {
                font-size: 1.65rem !important;
            }
            h2, .stMarkdown h2, [data-testid="stMarkdownContainer"] h2 {
                font-size: 1.35rem !important;
            }
            h3, .stMarkdown h3, [data-testid="stMarkdownContainer"] h3 {
                font-size: 1.15rem !important;
            }
            .neuro-card {
                padding: 18px 20px !important;
                margin-bottom: 14px !important;
            }
            .stButton > button {
                min-height: 42px !important;
            }
            .culture-grid {
                grid-template-columns: 1fr !important;
            }
            """
        elif "desktop" in norm_mode:
            return """
            /* === Desktop Wide Mode === */
            .main .block-container,
            [data-testid="stMainBlockContainer"] {
                max-width: 1400px !important;
                width: 100% !important;
                margin-left: auto !important;
                margin-right: auto !important;
                padding: 2.5rem 3rem !important;
                background: transparent !important;
                border: none !important;
                border-radius: 0 !important;
                box-shadow: none !important;
                transition: all 0.25s ease !important;
            }
            [data-testid="stAppViewContainer"] > .main {
                background-color: var(--bg-color) !important;
                background-image: none !important;
            }
            """
        else:
            # "🖥️ Auto (Responsive)" Default
            return """
            /* === Auto Responsive (Default) === */
            .main .block-container,
            [data-testid="stMainBlockContainer"] {
                max-width: 100% !important;
                width: 100% !important;
                margin-left: auto !important;
                margin-right: auto !important;
                transition: all 0.25s ease !important;
            }
            """

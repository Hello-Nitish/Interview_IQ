"""
Reusable UI Component Kit for InterviewIQ.
Decouples UI markup and styling from application logic in frontend/app.py.
Provides standardized Neumorphic cards, metric wells, badges, callouts,
progress bars, and SVG icon integration.
Future style changes are made here once and instantly propagate platform-wide.
"""

from typing import Optional, List, Dict, Any
from frontend.components.icons import icon
from frontend.styles.theme import Theme


class UI:
    """
    Standardized Component Generator for InterviewIQ Executive B2B Interface.
    Produces high-contrast, WCAG-compliant HTML5 markup.
    """

    @classmethod
    def badge(cls, text: str, variant: str = "primary", icon_name: Optional[str] = None) -> str:
        """Renders a standardized executive badge with optional SVG icon."""
        variant_styles = {
            "primary": f"background:{Theme.COLORS['primary_light']}; color:{Theme.COLORS['primary']}; border:1px solid {Theme.COLORS['primary_border']};",
            "success": f"background:{Theme.COLORS['success_bg']}; color:{Theme.COLORS['success']}; border:1px solid {Theme.COLORS['success_border']};",
            "warning": f"background:{Theme.COLORS['warning_bg']}; color:{Theme.COLORS['warning']}; border:1px solid {Theme.COLORS['warning_border']};",
            "danger": f"background:{Theme.COLORS['danger_bg']}; color:{Theme.COLORS['danger']}; border:1px solid {Theme.COLORS['danger_border']};",
            "info": f"background:{Theme.COLORS['info_bg']}; color:{Theme.COLORS['info']}; border:1px solid {Theme.COLORS['info_border']};",
            "neutral": f"background:{Theme.COLORS['bg_recessed']}; color:{Theme.COLORS['text_muted']}; border:1px solid {Theme.COLORS['border_light']};"
        }
        style = variant_styles.get(variant, variant_styles["primary"])
        svg_html = f"{icon(icon_name, size=13, stroke_width=2.2)} " if icon_name else ""

        return (
            f"<span style='display:inline-flex; align-items:center; gap:4px; font-size:0.75rem; "
            f"font-weight:700; padding:3px 9px; border-radius:9999px; text-transform:uppercase; "
            f"letter-spacing:0.02em; {style}'>{svg_html}{text}</span>"
        )

    @classmethod
    def card(
        cls,
        content: str,
        title: Optional[str] = None,
        subtitle: Optional[str] = None,
        badge_text: Optional[str] = None,
        badge_variant: str = "primary",
        icon_name: Optional[str] = None,
        class_name: str = ""
    ) -> str:
        """
        Renders a standardized Neumorphic raised card with optional header, icon, and badge.
        """
        header_html = ""
        if title or badge_text:
            icon_html = f"{icon(icon_name, size=20, color=Theme.COLORS['primary'])} " if icon_name else ""
            badge_html = cls.badge(badge_text, variant=badge_variant) if badge_text else ""
            sub_html = f"<div style='font-size:0.83rem; color:{Theme.COLORS['text_muted']}; margin-top:2px;'>{subtitle}</div>" if subtitle else ""

            header_html = f"""
            <div style='display:flex; justify-content:space-between; align-items:center; margin-bottom:14px; flex-wrap:wrap; gap:8px;'>
              <div>
                <h4 style='color:{Theme.COLORS['text_heading']}; margin:0; display:flex; align-items:center; gap:8px; font-weight:700;'>
                  {icon_html}{title}
                </h4>
                {sub_html}
              </div>
              {badge_html}
            </div>
            """

        return f"""
        <div class='neuro-card {class_name}' style='
          background:{Theme.COLORS['bg_surface']};
          border:1px solid {Theme.COLORS['border_light']};
          border-radius:{Theme.RADII['lg']};
          padding:20px 22px;
          margin-bottom:16px;
          box-shadow:{Theme.SHADOWS['card']};
        '>
          {header_html}
          {content}
        </div>
        """

    @classmethod
    def metric_card(
        cls,
        label: str,
        value: Any,
        delta: Optional[str] = None,
        icon_name: Optional[str] = None,
        color: Optional[str] = None
    ) -> str:
        """Renders an executive high-contrast metric card with icon and delta."""
        val_color = color or Theme.COLORS["text_heading"]
        icon_html = f"<div style='margin-bottom:6px;'>{icon(icon_name, size=20, color=val_color)}</div>" if icon_name else ""
        delta_html = f"<div style='font-size:0.75rem; color:{Theme.COLORS['text_muted']}; margin-top:3px; font-weight:600;'>{delta}</div>" if delta else ""

        return f"""
        <div class='neuro-card' style='
          background:{Theme.COLORS['bg_surface']};
          border:1px solid {Theme.COLORS['border_light']};
          border-radius:{Theme.RADII['md']};
          padding:16px 18px;
          text-align:center;
          box-shadow:{Theme.SHADOWS['card']};
        '>
          {icon_html}
          <div style='font-size:0.75rem; text-transform:uppercase; font-weight:700; color:{Theme.COLORS['text_muted']}; letter-spacing:0.04em;'>
            {label}
          </div>
          <div style='font-size:1.8rem; font-weight:900; color:{val_color}; line-height:1.2; margin-top:4px;'>
            {value}
          </div>
          {delta_html}
        </div>
        """

    @classmethod
    def callout(
        cls,
        message: str,
        title: Optional[str] = None,
        variant: str = "info",
        icon_name: Optional[str] = None
    ) -> str:
        """Renders an executive callout alert banner with accent border."""
        styles = {
            "info": (Theme.COLORS["info_bg"], Theme.COLORS["info"], "info"),
            "warning": (Theme.COLORS["warning_bg"], Theme.COLORS["warning"], "alert_triangle"),
            "success": (Theme.COLORS["success_bg"], Theme.COLORS["success"], "check_circle"),
            "danger": (Theme.COLORS["danger_bg"], Theme.COLORS["danger"], "x_circle")
        }
        bg, border_col, default_icon = styles.get(variant, styles["info"])
        chosen_icon = icon_name or default_icon
        title_html = f"<strong style='color:{border_col}; font-size:0.85rem; display:block; margin-bottom:2px;'>{title}</strong>" if title else ""

        return f"""
        <div style='
          background:{bg};
          border-left:4px solid {border_col};
          border-radius:{Theme.RADII['sm']};
          padding:12px 16px;
          margin:12px 0;
          display:flex;
          align-items:flex-start;
          gap:10px;
        '>
          <div style='color:{border_col}; margin-top:1px;'>{icon(chosen_icon, size=18, color=border_col)}</div>
          <div style='flex:1; font-size:0.88rem; color:{Theme.COLORS['text_body']}; line-height:1.45;'>
            {title_html}{message}
          </div>
        </div>
        """

    @classmethod
    def progress_bar(cls, value_pct: float, color: Optional[str] = None, height: int = 8) -> str:
        """Renders an animated, rounded progress bar."""
        clamped = max(0.0, min(100.0, value_pct))
        bar_color = color or Theme.COLORS["primary"]
        return f"""
        <div style='
          width:100%;
          background:{Theme.COLORS['bg_recessed']};
          border-radius:9999px;
          height:{height}px;
          overflow:hidden;
          border:1px solid {Theme.COLORS['border_light']};
        '>
          <div class='shimmer-progress' style='
            width:{clamped}%;
            background:{bar_color};
            height:100%;
            border-radius:9999px;
            transition:{Theme.TRANSITIONS['smooth']};
          '></div>
        </div>
        """

    @classmethod
    def hero_header(cls, title: str, subtitle: str, badge_text: Optional[str] = None, icon_name: str = "target") -> str:
        """Renders the master top-of-page executive hero header."""
        badge_html = f"<div style='margin-bottom:8px;'>{cls.badge(badge_text, variant='primary', icon_name='sparkles')}</div>" if badge_text else ""
        return f"""
        <div style='
          background:linear-gradient(135deg, #FFFFFF 0%, #F8FAFC 100%);
          border:1px solid {Theme.COLORS['border_light']};
          border-radius:{Theme.RADII['xl']};
          padding:24px 28px;
          margin-bottom:22px;
          box-shadow:{Theme.SHADOWS['card']};
          display:flex;
          justify-content:space-between;
          align-items:center;
          flex-wrap:wrap;
          gap:14px;
        '>
          <div>
            {badge_html}
            <h1 style='color:{Theme.COLORS['text_heading']}; margin:0; font-size:1.85rem; font-weight:800; letter-spacing:-0.02em; display:flex; align-items:center; gap:10px;'>
              {icon(icon_name, size=28, color=Theme.COLORS['primary'])} {title}
            </h1>
            <p style='color:{Theme.COLORS['text_muted']}; margin:6px 0 0 0; font-size:0.95rem;'>
              {subtitle}
            </p>
          </div>
        </div>
        """

    @classmethod
    def status_pill(cls, status: str) -> str:
        """Standardized candidate status badge with semantic color mapping."""
        s = status.upper().strip()
        if "STRONG HIRE" in s or "SELECTED" in s or "READY" in s:
            return cls.badge(status, variant="success", icon_name="check_circle")
        elif "SHORTLIST" in s or "MODERATE" in s or "DEVELOPING" in s:
            return cls.badge(status, variant="primary", icon_name="award")
        elif "FURTHER" in s or "PREPARATION" in s or "COACHING" in s or "WEAK" in s:
            return cls.badge(status, variant="warning", icon_name="alert_triangle")
        else:
            return cls.badge(status, variant="neutral", icon_name="info")

    @classmethod
    def empty_state(
        cls,
        title: str,
        description: str,
        icon_name: str = "alert_triangle",
        action_hint: Optional[str] = None
    ) -> str:
        """Renders an executive empty state card with icon, description, and guidance."""
        hint_html = f"<div style='margin-top:12px; font-size:0.85rem; color:{Theme.COLORS['primary']}; font-weight:600;'>👉 {action_hint}</div>" if action_hint else ""
        return f"""
        <div class='neuro-card' style='
          background:{Theme.COLORS['bg_surface']};
          border:1px dashed {Theme.COLORS['border_medium']};
          border-radius:{Theme.RADII['xl']};
          padding:36px 28px;
          text-align:center;
          margin:20px 0;
          box-shadow:{Theme.SHADOWS['card']};
        '>
          <div style='margin-bottom:12px; display:inline-flex; align-items:center; justify-content:center; width:52px; height:52px; border-radius:50%; background:{Theme.COLORS['primary_light']}; color:{Theme.COLORS['primary']};'>
            {icon(icon_name, size=26, color=Theme.COLORS['primary'])}
          </div>
          <h3 style='margin:0 0 6px 0; color:{Theme.COLORS['text_heading']}; font-weight:800; font-size:1.2rem;'>{title}</h3>
          <p style='margin:0 auto; max-width:480px; color:{Theme.COLORS['text_muted']}; font-size:0.9rem; line-height:1.5;'>{description}</p>
          {hint_html}
        </div>
        """

    @classmethod
    def stepper(cls, current_step: int, total_steps: int = 6) -> str:
        """Renders a sleek 6-stage candidate pipeline progress stepper."""
        steps = [
            ("1", "Onboarding", "01_upload"),
            ("2", "Fit Report", "02_fit_report"),
            ("3", "Question Bank", "03_question_bank"),
            ("4", "Online Test", "04_online_test"),
            ("5", "Diagnostics", "05_results"),
            ("6", "Curriculum", "06_curriculum"),
        ]
        items_html = []
        for idx, (num, name, _) in enumerate(steps, 1):
            if idx < current_step:
                # Completed
                circle = f"<span style='width:24px; height:24px; border-radius:50%; background:{Theme.COLORS['success']}; color:#FFFFFF; display:inline-flex; align-items:center; justify-content:center; font-size:0.75rem; font-weight:700;'>✓</span>"
                label_color = Theme.COLORS["text_heading"]
                border_color = Theme.COLORS["success"]
            elif idx == current_step:
                # Active
                circle = f"<span style='width:24px; height:24px; border-radius:50%; background:{Theme.COLORS['primary']}; color:#FFFFFF; display:inline-flex; align-items:center; justify-content:center; font-size:0.75rem; font-weight:800; box-shadow:{Theme.SHADOWS['glow_primary']};'>{num}</span>"
                label_color = Theme.COLORS["primary"]
                border_color = Theme.COLORS["primary"]
            else:
                # Upcoming
                circle = f"<span style='width:24px; height:24px; border-radius:50%; background:{Theme.COLORS['bg_recessed']}; color:{Theme.COLORS['text_muted']}; display:inline-flex; align-items:center; justify-content:center; font-size:0.75rem; font-weight:600; border:1px solid {Theme.COLORS['border_light']};'>{num}</span>"
                label_color = Theme.COLORS["text_muted"]
                border_color = Theme.COLORS["border_light"]

            connector = f"<div style='flex:1; height:2px; background:{border_color}; margin:0 8px;'></div>" if idx < len(steps) else ""
            items_html.append(f"""
            <div style='display:flex; align-items:center; {"flex:1;" if idx < len(steps) else ""}'>
              <div style='display:flex; align-items:center; gap:6px;'>
                {circle}
                <span style='font-size:0.8rem; font-weight:700; color:{label_color}; white-space:nowrap;'>{name}</span>
              </div>
              {connector}
            </div>
            """)

        return f"""
        <div class='neuro-card' style='
          background:{Theme.COLORS['bg_surface']};
          border:1px solid {Theme.COLORS['border_light']};
          border-radius:{Theme.RADII['lg']};
          padding:12px 20px;
          margin-bottom:18px;
          display:flex;
          align-items:center;
          justify-content:space-between;
          box-shadow:{Theme.SHADOWS['sm']};
          overflow-x:auto;
        '>
          {''.join(items_html)}
        </div>
        """

    @classmethod
    def badge_group(cls, items: List[str], variant: str = "primary") -> str:
        """Renders an inline flex group of badges."""
        if not items:
            return ""
        badges = [cls.badge(item, variant=variant) for item in items]
        return f"<div style='display:flex; flex-wrap:wrap; gap:6px; margin:6px 0;'>{''.join(badges)}</div>"

    @classmethod
    def stat_card(
        cls,
        label: str,
        value: Any,
        subtext: Optional[str] = None,
        icon_name: Optional[str] = None,
        color: Optional[str] = None,
        trend: Optional[str] = None
    ) -> str:
        """Renders an executive high-contrast stat card with trend indicator."""
        val_color = color or Theme.COLORS["text_heading"]
        icon_html = f"<div style='width:36px; height:36px; border-radius:8px; background:{Theme.COLORS['primary_light']}; display:inline-flex; align-items:center; justify-content:center; margin-bottom:8px;'>{icon(icon_name, size=18, color=val_color)}</div>" if icon_name else ""
        sub_html = f"<div style='font-size:0.75rem; color:{Theme.COLORS['text_muted']}; margin-top:4px;'>{subtext}</div>" if subtext else ""
        trend_html = f"<span style='font-size:0.75rem; font-weight:700; color:{Theme.COLORS['success']}; margin-left:6px;'>{trend}</span>" if trend else ""

        return f"""
        <div class='neuro-card' style='
          background:{Theme.COLORS['bg_surface']};
          border:1px solid {Theme.COLORS['border_light']};
          border-radius:{Theme.RADII['md']};
          padding:18px 20px;
          text-align:left;
          box-shadow:{Theme.SHADOWS['card']};
        '>
          <div style='display:flex; justify-content:space-between; align-items:flex-start;'>
            <div style='font-size:0.75rem; text-transform:uppercase; font-weight:800; color:{Theme.COLORS['text_muted']}; letter-spacing:0.04em;'>
              {label}
            </div>
            {icon_html}
          </div>
          <div style='font-size:1.85rem; font-weight:900; color:{val_color}; line-height:1.1; margin-top:2px;'>
            {value}{trend_html}
          </div>
          {sub_html}
        </div>
        """

    @classmethod
    def about_developer_card(cls) -> str:
        """Renders an executive Developer Attribution & About Us card."""
        return f"""
        <div style='
          margin-top:30px;
          margin-bottom:12px;
          padding:16px 22px;
          background:{Theme.COLORS['bg_surface']};
          border:1px solid {Theme.COLORS['border_light']};
          border-left:4px solid {Theme.COLORS['secondary']};
          border-radius:{Theme.RADII['lg']};
          display:flex;
          align-items:center;
          gap:14px;
          box-shadow:{Theme.SHADOWS['sm']};
        '>
          <div style='flex-shrink:0;'>
            {icon('code', size=20, color=Theme.COLORS['secondary'])}
          </div>
          <div style='font-size:0.85rem; color:{Theme.COLORS['text_body']}; line-height:1.5;'>
            <strong style='color:{Theme.COLORS['text_heading']}; font-size:0.9rem;'>About the Developers / About Us:</strong>
            Developed by your frd Nitish and Jeevana
          </div>
        </div>
        """

    @classmethod
    def disclaimer_footer(cls) -> str:
        """Renders an executive, high-contrast advisory disclaimer and terms of use notice."""
        return f"""
        <div style='
          margin-top:40px;
          margin-bottom:20px;
          padding:16px 22px;
          background:{Theme.COLORS['bg_recessed']};
          border:1px solid {Theme.COLORS['border_medium']};
          border-left:4px solid {Theme.COLORS['primary']};
          border-radius:{Theme.RADII['lg']};
          display:flex;
          align-items:flex-start;
          gap:14px;
          box-shadow:{Theme.SHADOWS['sm']};
        '>
          <div style='margin-top:2px; flex-shrink:0;'>
            {icon('shield', size=20, color=Theme.COLORS['primary'])}
          </div>
          <div style='font-size:0.8rem; color:{Theme.COLORS['text_muted']}; line-height:1.55;'>
            <strong style='color:{Theme.COLORS['text_heading']}; font-size:0.84rem; text-transform:uppercase; letter-spacing:0.03em;'>
              Advisory Disclaimer & Terms of Use
            </strong><br>
            InterviewIQ is an AI-assisted diagnostic evaluation platform. Outputs, analyses, match ratios, and questions are generated via probabilistic large language models and heuristic algorithms. Outputs may occasionally contain approximations, inaccuracies, or false positives. All diagnostic recommendations should be reviewed with independent judgment. <b>Use of this system is at your own risk.</b> Continued use and engagement with this application constitutes full acceptance of our terms, operational limitations, and conditions.
          </div>
        </div>
        """


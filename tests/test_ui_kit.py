"""
Unit Tests for UI Kit, Theme Engine, and SVG Icon System.
Verifies design token generation, SVG rendering integrity, and component helpers.
"""

import unittest
from frontend.styles.theme import Theme
from frontend.components.icons import IconLibrary, icon
from frontend.components.ui_kit import UI


class TestUIKitAndTheme(unittest.TestCase):

    def test_theme_css_variables_generation(self):
        """Verify Theme.generate_css_variables produces valid :root CSS block."""
        css_vars = Theme.generate_css_variables()
        self.assertTrue(css_vars.startswith(":root {"))
        self.assertTrue(css_vars.endswith("}"))
        self.assertIn("--color-primary: #2563EB;", css_vars)
        self.assertIn("--color-bg-canvas: #F8FAFC;", css_vars)
        self.assertIn("--color-text-heading: #0F172A;", css_vars)
        self.assertIn("--shadow-card:", css_vars)
        self.assertIn("--radius-lg:", css_vars)

    def test_icon_library_completeness_and_validity(self):
        """Verify all 30+ icons render well-formed SVG elements."""
        for icon_name in IconLibrary.ICONS.keys():
            svg_markup = IconLibrary.get(icon_name, size=20, color="#2563EB")
            self.assertTrue(svg_markup.startswith("<svg"))
            self.assertTrue(svg_markup.endswith("</svg>"))
            self.assertIn("viewBox='0 0 24 24'", svg_markup)
            self.assertIn("width='20'", svg_markup)
            self.assertIn("stroke='#2563EB'", svg_markup)

    def test_icon_fallback_to_target(self):
        """Verify unknown icon name safely falls back to default target icon."""
        fallback_svg = icon("completely_unknown_icon_name")
        self.assertTrue(fallback_svg.startswith("<svg"))
        self.assertTrue(fallback_svg.endswith("</svg>"))

    def test_ui_badge_generation(self):
        """Verify badge renders with appropriate semantic styles."""
        success_badge = UI.badge("Verified", variant="success", icon_name="check_circle")
        self.assertIn("Verified", success_badge)
        self.assertIn(Theme.COLORS["success"], success_badge)
        self.assertIn("<svg", success_badge)

    def test_ui_metric_card_generation(self):
        """Verify metric card embeds value, label, delta, and icon."""
        metric_html = UI.metric_card(
            label="Match Score",
            value="94%",
            delta="+12% Lift",
            icon_name="trending_up",
            color=Theme.COLORS["success"]
        )
        self.assertIn("Match Score", metric_html)
        self.assertIn("94%", metric_html)
        self.assertIn("+12% Lift", metric_html)
        self.assertIn(Theme.COLORS["success"], metric_html)

    def test_ui_callout_banner(self):
        """Verify callout banner renders message with accent border."""
        callout_html = UI.callout(
            message="Candidate demonstrated strong MECE structure.",
            title="Executive Note",
            variant="info",
            icon_name="info"
        )
        self.assertIn("Executive Note", callout_html)
        self.assertIn("Candidate demonstrated strong MECE structure.", callout_html)
        self.assertIn("<svg", callout_html)

    def test_ui_progress_bar_clamping(self):
        """Verify progress bar clamps percentages between 0 and 100."""
        bar_over = UI.progress_bar(125.0)
        self.assertIn("width:100.0%", bar_over)

        bar_under = UI.progress_bar(-15.0)
        self.assertIn("width:0.0%", bar_under)

    def test_status_pill_mapping(self):
        """Verify status pill maps standard candidate ratings to badges."""
        strong_pill = UI.status_pill("STRONG HIRE")
        self.assertIn("STRONG HIRE", strong_pill)
        self.assertIn(Theme.COLORS["success"], strong_pill)

        prep_pill = UI.status_pill("FURTHER PREPARATION")
        self.assertIn("FURTHER PREPARATION", prep_pill)
        self.assertIn(Theme.COLORS["warning"], prep_pill)

    def test_ui_empty_state(self):
        """Verify empty_state renders title, description, and action hint."""
        empty_html = UI.empty_state(
            title="No Results Found",
            description="Please submit an assessment to generate diagnostics.",
            icon_name="alert_triangle",
            action_hint="Click to begin"
        )
        self.assertIn("No Results Found", empty_html)
        self.assertIn("Please submit an assessment", empty_html)
        self.assertIn("Click to begin", empty_html)
        self.assertIn("<svg", empty_html)

    def test_ui_stepper(self):
        """Verify stepper renders all 6 pipeline stages with active status."""
        stepper_html = UI.stepper(current_step=3, total_steps=6)
        self.assertIn("Onboarding", stepper_html)
        self.assertIn("Fit Report", stepper_html)
        self.assertIn("Question Bank", stepper_html)
        self.assertIn("Online Test", stepper_html)
        self.assertIn("Diagnostics", stepper_html)
        self.assertIn("Curriculum", stepper_html)
        self.assertIn("✓", stepper_html)  # Completed checkmark for steps 1 and 2

    def test_ui_stat_card(self):
        """Verify stat_card renders label, value, subtext, and trend."""
        stat_html = UI.stat_card(
            label="Placement Readiness",
            value="88%",
            subtext="Calculated via strict formula",
            icon_name="award",
            trend="+5% Lift"
        )
        self.assertIn("Placement Readiness", stat_html)
        self.assertIn("88%", stat_html)
        self.assertIn("Calculated via strict formula", stat_html)
        self.assertIn("+5% Lift", stat_html)

    def test_ui_badge_group(self):
        """Verify badge_group renders flex list of badges."""
        group_html = UI.badge_group(["SQL", "Python", "Docker"], variant="primary")
        self.assertIn("SQL", group_html)
        self.assertIn("Python", group_html)
        self.assertIn("Docker", group_html)

    def test_hero_header_badges_removed(self):
        """Verify Institutional Grade and WCAG AAA Compliant badges are removed from hero_header."""
        header_html = UI.hero_header(
            title="Step 1: Upload",
            subtitle="Upload candidate files",
            badge_text="Candidate Diagnostics"
        )
        self.assertNotIn("Institutional Grade", header_html)
        self.assertNotIn("WCAG AAA Compliant", header_html)
        self.assertIn("Step 1: Upload", header_html)

    def test_disclaimer_footer_rendering(self):
        """Verify disclaimer footer renders advisory notice and terms of use."""
        footer_html = UI.disclaimer_footer()
        self.assertIn("Advisory Disclaimer & Terms of Use", footer_html)
        self.assertIn("at your own risk", footer_html.lower())
        self.assertIn("terms", footer_html.lower())
        self.assertIn("<svg", footer_html)

    def test_about_developer_card_rendering(self):
        """Verify developer card renders exact attribution text."""
        card_html = UI.about_developer_card()
        self.assertIn("About the Developers", card_html)
        self.assertIn("Developed by your frd Nitish and Jeevana", card_html)
        self.assertIn("<svg", card_html)


if __name__ == "__main__":
    unittest.main()



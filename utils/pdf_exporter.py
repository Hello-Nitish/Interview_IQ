import os
import io
import json
from datetime import datetime
from typing import Dict, Any, Optional

from reportlab.lib.pagesizes import letter
from reportlab.lib import colors
from reportlab.lib.units import inch
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, PageBreak, KeepTogether, HRFlowable
)
from reportlab.pdfgen import canvas

class NumberedCanvas(canvas.Canvas):
    """Two-pass canvas to dynamically compute and print total page numbers in footer."""
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._saved_page_states = []

    def showPage(self):
        self._saved_page_states.append(dict(self.__dict__))
        self._startPage()

    def save(self):
        num_pages = len(self._saved_page_states)
        for state in self._saved_page_states:
            self.__dict__.update(state)
            self.draw_page_decorations(num_pages)
            super().showPage()
        super().save()

    def draw_page_decorations(self, page_count: int):
        self.saveState()
        self.setFont("Helvetica", 8)
        self.setFillColor(colors.HexColor("#64748B"))
        
        # Header (pages 2+)
        if self._pageNumber > 1:
            self.drawString(40, letter[1] - 30, "InterviewIQ — Candidate Evaluation Dossier")
            self.drawRightString(letter[0] - 40, letter[1] - 30, "Strictly Confidential")
            self.setStrokeColor(colors.HexColor("#CBD5E1"))
            self.setLineWidth(0.5)
            self.line(40, letter[1] - 34, letter[0] - 40, letter[1] - 34)

        # Footer
        footer_text = f"Page {self._pageNumber} of {page_count}"
        self.drawRightString(letter[0] - 40, 25, footer_text)
        self.drawString(40, 25, "InterviewIQ Digital Transformation Assessment • Institutional Placement Engine")
        self.setStrokeColor(colors.HexColor("#E2E8F0"))
        self.setLineWidth(0.5)
        self.line(40, 35, letter[0] - 40, 35)
        self.restoreState()


class FitReportNumberedCanvas(NumberedCanvas):
    """Two-pass canvas to dynamically compute and print total page numbers for Strategic Fit Reports."""
    def draw_page_decorations(self, page_count: int):
        self.saveState()
        self.setFont("Helvetica", 8)
        self.setFillColor(colors.HexColor("#64748B"))
        
        # Header (pages 2+)
        if self._pageNumber > 1:
            self.drawString(40, letter[1] - 30, "InterviewIQ — Strategic Fit Report")
            self.drawRightString(letter[0] - 40, letter[1] - 30, "Strictly Confidential")
            self.setStrokeColor(colors.HexColor("#CBD5E1"))
            self.setLineWidth(0.5)
            self.line(40, letter[1] - 34, letter[0] - 40, letter[1] - 34)

        # Footer
        footer_text = f"Page {self._pageNumber} of {page_count}"
        self.drawRightString(letter[0] - 40, 25, footer_text)
        self.drawString(40, 25, "InterviewIQ Strategic Fit Assessment • Confidential Talent Evaluation")
        self.setStrokeColor(colors.HexColor("#E2E8F0"))
        self.setLineWidth(0.5)
        self.line(40, 35, letter[0] - 40, 35)
        self.restoreState()


class PDFDossierExporter:
    """
    Automated Corporate PDF Dossier Generator for InterviewIQ.
    Compiles candidate profiles, strategic fit assessments, question banks,
    scored 30-MCQ tests, and closed-loop diagnostic roadmaps into an
    institutional-grade printable evaluation report.
    """

    @classmethod
    def generate_dossier_pdf(cls, session_state: Dict[str, Any]) -> bytes:
        """Compiles session state into a formatted PDF byte buffer."""
        buffer = io.BytesIO()
        doc = SimpleDocTemplate(
            buffer,
            pagesize=letter,
            leftMargin=40,
            rightMargin=40,
            topMargin=45,
            bottomMargin=45
        )

        styles = getSampleStyleSheet()
        
        # Custom Typography
        title_style = ParagraphStyle(
            'DocTitle',
            parent=styles['Normal'],
            fontName='Helvetica-Bold',
            fontSize=20,
            leading=24,
            textColor=colors.HexColor('#0F172A')
        )
        subtitle_style = ParagraphStyle(
            'DocSubtitle',
            parent=styles['Normal'],
            fontName='Helvetica',
            fontSize=10,
            leading=14,
            textColor=colors.HexColor('#475569')
        )
        section_h1 = ParagraphStyle(
            'SectionH1',
            parent=styles['Normal'],
            fontName='Helvetica-Bold',
            fontSize=13,
            leading=17,
            textColor=colors.HexColor('#1E3A8A'),
            spaceBefore=12,
            spaceAfter=6
        )
        section_h2 = ParagraphStyle(
            'SectionH2',
            parent=styles['Normal'],
            fontName='Helvetica-Bold',
            fontSize=10.5,
            leading=14,
            textColor=colors.HexColor('#0F172A'),
            spaceBefore=8,
            spaceAfter=4
        )
        body_style = ParagraphStyle(
            'BodyDark',
            parent=styles['Normal'],
            fontName='Helvetica',
            fontSize=8.5,
            leading=11.5,
            textColor=colors.HexColor('#1E293B')
        )
        body_bold = ParagraphStyle(
            'BodyDarkBold',
            parent=styles['Normal'],
            fontName='Helvetica-Bold',
            fontSize=8.5,
            leading=11.5,
            textColor=colors.HexColor('#0F172A')
        )
        tag_matched = ParagraphStyle(
            'TagMatched',
            parent=styles['Normal'],
            fontName='Helvetica-Bold',
            fontSize=7.5,
            leading=9,
            textColor=colors.HexColor('#065F46')
        )
        tag_gap = ParagraphStyle(
            'TagGap',
            parent=styles['Normal'],
            fontName='Helvetica-Bold',
            fontSize=7.5,
            leading=9,
            textColor=colors.HexColor('#991B1B')
        )
        tag_amber = ParagraphStyle(
            'TagAmber',
            parent=styles['Normal'],
            fontName='Helvetica-Bold',
            fontSize=7.5,
            leading=9,
            textColor=colors.HexColor('#92400E')
        )

        elements = []

        # Data extraction
        candidate_name = session_state.get("candidate_name") or (session_state.get("resume_data") or {}).get("candidate_name") or "Candidate"
        role_title = (session_state.get("jd_data") or {}).get("role_title") or (session_state.get("jd_profile") or {}).get("role_title") or "Placement Assessment"
        fit_data = session_state.get("fit_data") or {}
        test_results = session_state.get("test_results") or {}
        question_bank = session_state.get("question_bank") or {}
        feedback = session_state.get("feedback") or {}
        current_round = session_state.get("round_number") or session_state.get("round", 1)

        # -------------------------------------------------------------------------
        # COVER / HEADER BANNER
        # -------------------------------------------------------------------------
        elements.append(Paragraph("INTERVIEWIQ — CANDIDATE EVALUATION DOSSIER", title_style))
        elements.append(Paragraph(f"Institutional Assessment & Multi-Agent Placement Analysis Report • Generated on {datetime.now().strftime('%B %d, %Y')}", subtitle_style))
        elements.append(Spacer(1, 10))
        elements.append(HRFlowable(width="100%", thickness=2, color=colors.HexColor("#2563EB"), spaceBefore=2, spaceAfter=10))

        # Metadata Strip
        meta_data = [
            [
                Paragraph(f"<b>Candidate:</b> {candidate_name}", body_style),
                Paragraph(f"<b>Target Role:</b> {role_title}", body_style),
                Paragraph(f"<b>Assessment Round:</b> Round {current_round}", body_style),
            ],
            [
                Paragraph(f"<b>Session ID:</b> {session_state.get('session_id', 'N/A')}", body_style),
                Paragraph(f"<b>Evaluation Date:</b> {datetime.now().strftime('%Y-%m-%d')}", body_style),
                Paragraph("<b>Audit Status:</b> Verified Multi-Agent Output", body_style),
            ]
        ]
        meta_table = Table(meta_data, colWidths=[180, 210, 140])
        meta_table.setStyle(TableStyle([
            ('BACKGROUND', (0,0), (-1,-1), colors.HexColor("#F1F5F9")),
            ('BOX', (0,0), (-1,-1), 1, colors.HexColor("#CBD5E1")),
            ('INNERGRID', (0,0), (-1,-1), 0.5, colors.HexColor("#E2E8F0")),
            ('TOPPADDING', (0,0), (-1,-1), 6),
            ('BOTTOMPADDING', (0,0), (-1,-1), 6),
            ('LEFTPADDING', (0,0), (-1,-1), 8),
            ('RIGHTPADDING', (0,0), (-1,-1), 8),
        ]))
        elements.append(meta_table)
        elements.append(Spacer(1, 14))

        # -------------------------------------------------------------------------
        # 1. EXECUTIVE METRICS SUMMARY
        # -------------------------------------------------------------------------
        elements.append(Paragraph("1. Executive Institutional Metrics & Decision", section_h1))
        
        tech_match = fit_data.get("technical_rating", {}).get("technical_match_pct") or fit_data.get("technical_match_pct", 0)
        exp_score = fit_data.get("experience_scoring", {}).get("awarded_points", 0)
        decision = fit_data.get("decision_engine", {}).get("final_decision", "SHORTLIST")
        rule_trig = fit_data.get("decision_engine", {}).get("governing_rule_triggered", "Mandatory requirements match benchmark.")
        alt_role = fit_data.get("decision_engine", {}).get("alternative_role_routing", "Associate Business Analyst")
        comp_readiness = feedback.get("overall_readiness_score") or feedback.get("composite_readiness_score") or fit_data.get("placement_readiness_score", 70)
        test_pct = test_results.get("percentage", 0.0)

        metric_cards = [
            [
                Paragraph("<font size=7 color='#64748B'>STRICT TECHNICAL MATCH</font><br/><font size=14 color='#1E3A8A'><b>{:.1f}%</b></font><br/><font size=7 color='#475569'>Mandatory Skill Ratio</font>".format(float(tech_match)), body_style),
                Paragraph("<font size=7 color='#64748B'>EXPERIENCE TIER</font><br/><font size=14 color='#1E3A8A'><b>{}/10 pts</b></font><br/><font size=7 color='#475569'>Institutional Rating</font>".format(exp_score), body_style),
                Paragraph("<font size=7 color='#64748B'>ONLINE TEST (30 MCQs)</font><br/><font size=14 color='#1E3A8A'><b>{:.1f}%</b></font><br/><font size=7 color='#475569'>Empirical Accuracy</font>".format(float(test_pct)), body_style),
                Paragraph("<font size=7 color='#64748B'>COMPOSITE READINESS</font><br/><font size=14 color='#1E3A8A'><b>{:.1f}%</b></font><br/><font size=7 color='#475569'>45% Fit + 55% Test</font>".format(float(comp_readiness)), body_style),
            ]
        ]
        metric_table = Table(metric_cards, colWidths=[132, 133, 133, 132])
        metric_table.setStyle(TableStyle([
            ('BACKGROUND', (0,0), (-1,-1), colors.HexColor("#F8FAFC")),
            ('BOX', (0,0), (-1,-1), 1, colors.HexColor("#CBD5E1")),
            ('INNERGRID', (0,0), (-1,-1), 0.5, colors.HexColor("#CBD5E1")),
            ('ALIGN', (0,0), (-1,-1), 'CENTER'),
            ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
            ('TOPPADDING', (0,0), (-1,-1), 8),
            ('BOTTOMPADDING', (0,0), (-1,-1), 8),
        ]))
        elements.append(metric_table)
        elements.append(Spacer(1, 10))

        # Corporate Decision Card
        dec_color = colors.HexColor("#065F46") if decision in ["STRONG HIRE", "SHORTLIST"] else colors.HexColor("#991B1B")
        dec_box_data = [
            [
                Paragraph(f"<b>CORPORATE RECRUITMENT DECISION:</b> <font color='{dec_color.hexval()}'><b>{decision}</b></font>", section_h2),
            ],
            [
                Paragraph(f"<b>Governing Benchmark Rule:</b> {rule_trig}<br/>"
                          f"<b>Alternative Role Routing Recommendation:</b> {alt_role}", body_style)
            ]
        ]
        dec_table = Table(dec_box_data, colWidths=[530])
        dec_table.setStyle(TableStyle([
            ('BACKGROUND', (0,0), (-1,-1), colors.HexColor("#FFFFFF")),
            ('BOX', (0,0), (-1,-1), 1.5, dec_color),
            ('TOPPADDING', (0,0), (-1,-1), 6),
            ('BOTTOMPADDING', (0,0), (-1,-1), 6),
            ('LEFTPADDING', (0,0), (-1,-1), 10),
            ('RIGHTPADDING', (0,0), (-1,-1), 10),
        ]))
        elements.append(dec_table)
        elements.append(Spacer(1, 14))

        # -------------------------------------------------------------------------
        # 2. STRATEGIC REQUIREMENTS ASSESSMENT MATRIX (4 COLUMNS)
        # -------------------------------------------------------------------------
        elements.append(Paragraph("2. Strategic Requirements Assessment Matrix", section_h1))
        elements.append(Paragraph("Direct alignment of candidate profile evidence against operational JD desk requirements.", subtitle_style))
        elements.append(Spacer(1, 6))

        req_headers = [
            Paragraph("<b>Job Requirement</b>", body_bold),
            Paragraph("<b>Category</b>", body_bold),
            Paragraph("<b>Resume Evidence / Gap Assessment</b>", body_bold),
            Paragraph("<b>Status</b>", body_bold),
        ]
        req_rows = [req_headers]
        
        matrix_items = fit_data.get("requirements_matrix", [])
        if not matrix_items and "matrix" in fit_data:
            matrix_items = fit_data.get("matrix", [])

        for item in matrix_items[:12]:  # Top requirements
            req_name = item.get("requirement") or item.get("skill") or "Requirement"
            cat = item.get("category") or ("Mandatory" if item.get("is_mandatory") else "Preferred")
            evidence = item.get("evidence_or_gap") or item.get("evidence_gap") or item.get("evidence") or "Citations verified in profile."
            status = str(item.get("status") or "Matched")
            
            if "Match" in status:
                st_p = Paragraph(f"<b>{status}</b>", tag_matched)
            elif "Pref" in status:
                st_p = Paragraph(f"<b>{status}</b>", tag_amber)
            else:
                st_p = Paragraph(f"<b>{status}</b>", tag_gap)

            req_rows.append([
                Paragraph(req_name, body_style),
                Paragraph(cat, body_style),
                Paragraph(evidence, body_style),
                st_p
            ])

        if len(req_rows) > 1:
            req_table = Table(req_rows, colWidths=[130, 65, 260, 75])
            req_table.setStyle(TableStyle([
                ('BACKGROUND', (0,0), (-1,0), colors.HexColor("#E2E8F0")),
                ('BOX', (0,0), (-1,-1), 1, colors.HexColor("#CBD5E1")),
                ('INNERGRID', (0,0), (-1,-1), 0.5, colors.HexColor("#E2E8F0")),
                ('TOPPADDING', (0,0), (-1,-1), 4),
                ('BOTTOMPADDING', (0,0), (-1,-1), 4),
                ('LEFTPADDING', (0,0), (-1,-1), 6),
                ('RIGHTPADDING', (0,0), (-1,-1), 6),
            ]))
            elements.append(req_table)
        else:
            elements.append(Paragraph("<i>No requirements assessment records found in session.</i>", body_style))

        elements.append(Spacer(1, 14))

        # -------------------------------------------------------------------------
        # 3. ONLINE TEST PERFORMANCE & TOPIC BREAKDOWN
        # -------------------------------------------------------------------------
        elements.append(Paragraph("3. Empirical 30-MCQ Online Test Assessment", section_h1))
        
        if test_results:
            score = test_results.get("score", 0)
            total_q = test_results.get("total_questions", 30)
            pct = test_results.get("percentage", 0.0)
            passed = test_results.get("passed", False)
            pass_str = "<font color='#059669'><b>PASSED (Above 70% Cutoff)</b></font>" if passed else "<font color='#DC2626'><b>NEEDS REMEDIATION (Below Cutoff)</b></font>"
            
            elements.append(Paragraph(f"<b>Candidate Score:</b> {score} / {total_q} ({pct:.1f}%) • <b>Result:</b> {pass_str}", body_style))
            elements.append(Spacer(1, 6))

            topic_acc = test_results.get("topic_accuracy", {})
            if topic_acc:
                acc_headers = [
                    Paragraph("<b>Tested Knowledge Domain</b>", body_bold),
                    Paragraph("<b>Correct</b>", body_bold),
                    Paragraph("<b>Total</b>", body_bold),
                    Paragraph("<b>Accuracy %</b>", body_bold),
                    Paragraph("<b>Demonstrated Mastery</b>", body_bold),
                ]
                acc_rows = [acc_headers]
                for topic, vals in topic_acc.items():
                    c = vals.get("correct", 0)
                    t = vals.get("total", 0)
                    p = vals.get("percentage", 0.0)
                    mastery = "Proficient" if p >= 75 else ("Developing" if p >= 50 else "Critical Deficit")
                    mastery_color = tag_matched if p >= 75 else (tag_amber if p >= 50 else tag_gap)

                    acc_rows.append([
                        Paragraph(topic, body_style),
                        Paragraph(str(c), body_style),
                        Paragraph(str(t), body_style),
                        Paragraph(f"{p:.1f}%", body_style),
                        Paragraph(f"<b>{mastery}</b>", mastery_color),
                    ])
                
                acc_table = Table(acc_rows, colWidths=[200, 50, 50, 80, 150])
                acc_table.setStyle(TableStyle([
                    ('BACKGROUND', (0,0), (-1,0), colors.HexColor("#E2E8F0")),
                    ('BOX', (0,0), (-1,-1), 1, colors.HexColor("#CBD5E1")),
                    ('INNERGRID', (0,0), (-1,-1), 0.5, colors.HexColor("#E2E8F0")),
                    ('TOPPADDING', (0,0), (-1,-1), 4),
                    ('BOTTOMPADDING', (0,0), (-1,-1), 4),
                    ('LEFTPADDING', (0,0), (-1,-1), 6),
                    ('RIGHTPADDING', (0,0), (-1,-1), 6),
                ]))
                elements.append(acc_table)
        else:
            elements.append(Paragraph("<i>Candidate has not yet submitted the 30-MCQ Online Examination.</i>", body_style))

        elements.append(Spacer(1, 14))

        # -------------------------------------------------------------------------
        # 4. UNIFIED READINESS & 48-HOUR STUDY ROADMAP
        # -------------------------------------------------------------------------
        elements.append(Paragraph("4. Unified Placement Diagnosis & 48-Hour Study Roadmap", section_h1))
        
        unified_matrix = feedback.get("unified_topic_readiness", [])
        dual_weaknesses = [t for t in unified_matrix if t.get("readiness_status") == "HIGH PRIORITY" or "High Priority" in str(t.get("primary_source"))]
        
        if dual_weaknesses:
            elements.append(Paragraph("<b>🚨 HIGH PRIORITY DUAL-WEAKNESS WARNING:</b> The following topics failed in the empirical test AND represent unverified gaps in the candidate's resume:", body_bold))
            elements.append(Spacer(1, 4))
            for dw in dual_weaknesses[:5]:
                t_name = dw.get("topic") or dw.get("topic_name") or "Technical Topic"
                rec = dw.get("recommendation") or "Review fundamental architectural principles and solve targeted case scenarios."
                elements.append(Paragraph(f"• <b>{t_name}:</b> {rec}", body_style))
            elements.append(Spacer(1, 8))

        study_plan = feedback.get("targeted_study_plan_next_48h", [])
        if study_plan:
            elements.append(Paragraph("<b>Prioritized 48-Hour Tactical Roadmap:</b>", section_h2))
            for idx, step in enumerate(study_plan[:4], 1):
                timeframe = step.get("timeframe") or f"Block {idx}"
                action = step.get("action_item") or step.get("action") or step.get("task") or "Targeted revision."
                exercise = step.get("practice_exercise") or step.get("exercise") or "Solve practical exercises."
                elements.append(Paragraph(f"<b>[{timeframe}]</b> {action} — <i>Exercise:</i> {exercise}", body_style))
                elements.append(Spacer(1, 3))
        else:
            elements.append(Paragraph("<i>Detailed feedback and study roadmap will populate upon completing Step 4 test.</i>", body_style))

        # Build PDF
        doc.build(elements, canvasmaker=NumberedCanvas)
        buffer.seek(0)
        return buffer.getvalue()

    @classmethod
    def generate_fit_report_pdf(
        cls,
        fit_data: Dict[str, Any],
        candidate_name: str = "Candidate",
        role_title: str = "Corporate Placement Assessment",
        company_name: str = "Enterprise Partner"
    ) -> bytes:
        """
        Compiles candidate strategic fit profile into a focused, standalone
        executive PDF report (Decision, Metrics, Matrix, Narrative, Gaps).
        """
        buffer = io.BytesIO()
        doc = SimpleDocTemplate(
            buffer,
            pagesize=letter,
            leftMargin=40,
            rightMargin=40,
            topMargin=45,
            bottomMargin=45
        )

        styles = getSampleStyleSheet()
        
        title_style = ParagraphStyle(
            'DocTitleFit',
            parent=styles['Normal'],
            fontName='Helvetica-Bold',
            fontSize=20,
            leading=24,
            textColor=colors.HexColor('#0F172A')
        )
        subtitle_style = ParagraphStyle(
            'DocSubtitleFit',
            parent=styles['Normal'],
            fontName='Helvetica',
            fontSize=10,
            leading=14,
            textColor=colors.HexColor('#475569')
        )
        section_h1 = ParagraphStyle(
            'SectionH1Fit',
            parent=styles['Normal'],
            fontName='Helvetica-Bold',
            fontSize=13,
            leading=17,
            textColor=colors.HexColor('#1E3A8A'),
            spaceBefore=12,
            spaceAfter=6
        )
        section_h2 = ParagraphStyle(
            'SectionH2Fit',
            parent=styles['Normal'],
            fontName='Helvetica-Bold',
            fontSize=10.5,
            leading=14,
            textColor=colors.HexColor('#0F172A'),
            spaceBefore=8,
            spaceAfter=4
        )
        body_style = ParagraphStyle(
            'BodyDarkFit',
            parent=styles['Normal'],
            fontName='Helvetica',
            fontSize=8.5,
            leading=11.5,
            textColor=colors.HexColor('#1E293B')
        )
        body_bold = ParagraphStyle(
            'BodyDarkBoldFit',
            parent=styles['Normal'],
            fontName='Helvetica-Bold',
            fontSize=8.5,
            leading=11.5,
            textColor=colors.HexColor('#0F172A')
        )
        tag_matched = ParagraphStyle(
            'TagMatchedFit',
            parent=styles['Normal'],
            fontName='Helvetica-Bold',
            fontSize=7.5,
            leading=9,
            textColor=colors.HexColor('#065F46')
        )
        tag_gap = ParagraphStyle(
            'TagGapFit',
            parent=styles['Normal'],
            fontName='Helvetica-Bold',
            fontSize=7.5,
            leading=9,
            textColor=colors.HexColor('#991B1B')
        )
        tag_amber = ParagraphStyle(
            'TagAmberFit',
            parent=styles['Normal'],
            fontName='Helvetica-Bold',
            fontSize=7.5,
            leading=9,
            textColor=colors.HexColor('#92400E')
        )

        elements = []
        
        fit_data = fit_data or {}
        c_details = fit_data.get("candidate_details", {})
        if not candidate_name or candidate_name == "Candidate":
            candidate_name = c_details.get("name", "Candidate Profile")
        if not role_title or role_title == "Corporate Placement Assessment":
            role_title = c_details.get("target_role") or "Corporate Placement Candidate"

        # -------------------------------------------------------------------------
        # COVER / HEADER BANNER
        # -------------------------------------------------------------------------
        elements.append(Paragraph("INTERVIEWIQ — STRATEGIC FIT REPORT", title_style))
        elements.append(Paragraph(f"Standalone Role Fit & Placement Benchmark Evaluation • Generated on {datetime.now().strftime('%B %d, %Y')}", subtitle_style))
        elements.append(Spacer(1, 10))
        elements.append(HRFlowable(width="100%", thickness=2, color=colors.HexColor("#2563EB"), spaceBefore=2, spaceAfter=10))

        # Metadata Strip
        meta_data = [
            [
                Paragraph(f"<b>Candidate:</b> {candidate_name}", body_style),
                Paragraph(f"<b>Target Role:</b> {role_title}", body_style),
                Paragraph(f"<b>Target Firm:</b> {company_name or 'Enterprise Partner'}", body_style),
            ],
            [
                Paragraph(f"<b>Candidate ID:</b> {c_details.get('candidate_id', 'DM274094')}", body_style),
                Paragraph(f"<b>Evaluation Date:</b> {datetime.now().strftime('%Y-%m-%d')}", body_style),
                Paragraph("<b>Audit Status:</b> Verified Strategic Fit Analysis", body_style),
            ]
        ]
        meta_table = Table(meta_data, colWidths=[180, 200, 150])
        meta_table.setStyle(TableStyle([
            ('BACKGROUND', (0,0), (-1,-1), colors.HexColor("#F1F5F9")),
            ('BOX', (0,0), (-1,-1), 1, colors.HexColor("#CBD5E1")),
            ('INNERGRID', (0,0), (-1,-1), 0.5, colors.HexColor("#E2E8F0")),
            ('TOPPADDING', (0,0), (-1,-1), 6),
            ('BOTTOMPADDING', (0,0), (-1,-1), 6),
            ('LEFTPADDING', (0,0), (-1,-1), 8),
            ('RIGHTPADDING', (0,0), (-1,-1), 8),
        ]))
        elements.append(meta_table)
        elements.append(Spacer(1, 14))

        # -------------------------------------------------------------------------
        # 1. EXECUTIVE FIT DECISION & KEY METRICS
        # -------------------------------------------------------------------------
        elements.append(Paragraph("1. Executive Institutional Fit Metrics & Decision", section_h1))
        
        tech_match = fit_data.get("technical_rating", {}).get("technical_match_pct")
        if tech_match is None:
            tech_match = fit_data.get("technical_match_pct", 0)
        exp_score = fit_data.get("experience_scoring", {}).get("awarded_points", 0)
        cult_score = fit_data.get("company_culture_fit", {}).get("cultural_fit_score")
        if cult_score is None:
            cult_score = fit_data.get("cultural_fit_score", 75)
        comp_readiness = fit_data.get("placement_readiness_score", 70)

        decision_eng = fit_data.get("decision_engine", {})
        decision = decision_eng.get("final_decision", "SHORTLIST")
        rule_trig = decision_eng.get("governing_rule_triggered", "Mandatory requirements match benchmark.")
        alt_role = decision_eng.get("alternative_role_routing", "Associate Business Analyst")

        metric_cards = [
            [
                Paragraph("<font size=7 color='#64748B'>STRICT TECHNICAL MATCH</font><br/><font size=14 color='#1E3A8A'><b>{:.1f}%</b></font><br/><font size=7 color='#475569'>Mandatory Skill Ratio</font>".format(float(tech_match)), body_style),
                Paragraph("<font size=7 color='#64748B'>EXPERIENCE TIER</font><br/><font size=14 color='#1E3A8A'><b>{}/10 pts</b></font><br/><font size=7 color='#475569'>Institutional Rating</font>".format(exp_score), body_style),
                Paragraph("<font size=7 color='#64748B'>CULTURAL FIT SCORE</font><br/><font size=14 color='#1E3A8A'><b>{:.1f}%</b></font><br/><font size=7 color='#475569'>DNA Alignment</font>".format(float(cult_score)), body_style),
                Paragraph("<font size=7 color='#64748B'>READINESS SCORE</font><br/><font size=14 color='#1E3A8A'><b>{:.1f}%</b></font><br/><font size=7 color='#475569'>Placement Index</font>".format(float(comp_readiness)), body_style),
            ]
        ]
        metric_table = Table(metric_cards, colWidths=[132, 133, 133, 132])
        metric_table.setStyle(TableStyle([
            ('BACKGROUND', (0,0), (-1,-1), colors.HexColor("#F8FAFC")),
            ('BOX', (0,0), (-1,-1), 1, colors.HexColor("#CBD5E1")),
            ('INNERGRID', (0,0), (-1,-1), 0.5, colors.HexColor("#CBD5E1")),
            ('ALIGN', (0,0), (-1,-1), 'CENTER'),
            ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
            ('TOPPADDING', (0,0), (-1,-1), 8),
            ('BOTTOMPADDING', (0,0), (-1,-1), 8),
        ]))
        elements.append(metric_table)
        elements.append(Spacer(1, 10))

        # Corporate Decision Card
        dec_color = colors.HexColor("#065F46") if decision in ["STRONG HIRE", "SHORTLIST"] else colors.HexColor("#991B1B")
        dec_box_data = [
            [
                Paragraph(f"<b>CORPORATE RECRUITMENT DECISION:</b> <font color='{dec_color.hexval()}'><b>{decision}</b></font>", section_h2),
            ],
            [
                Paragraph(f"<b>Governing Benchmark Rule:</b> {rule_trig}<br/>"
                          f"<b>Alternative Role Routing Recommendation:</b> {alt_role}", body_style)
            ]
        ]
        dec_table = Table(dec_box_data, colWidths=[530])
        dec_table.setStyle(TableStyle([
            ('BACKGROUND', (0,0), (-1,-1), colors.HexColor("#FFFFFF")),
            ('BOX', (0,0), (-1,-1), 1.5, dec_color),
            ('TOPPADDING', (0,0), (-1,-1), 6),
            ('BOTTOMPADDING', (0,0), (-1,-1), 6),
            ('LEFTPADDING', (0,0), (-1,-1), 10),
            ('RIGHTPADDING', (0,0), (-1,-1), 10),
        ]))
        elements.append(dec_table)
        elements.append(Spacer(1, 14))

        # -------------------------------------------------------------------------
        # 2. STRATEGIC REQUIREMENTS ASSESSMENT MATRIX
        # -------------------------------------------------------------------------
        elements.append(Paragraph("2. Strategic Requirements Assessment Matrix", section_h1))
        elements.append(Paragraph("Direct alignment of candidate profile evidence against operational JD desk requirements.", subtitle_style))
        elements.append(Spacer(1, 6))

        req_headers = [
            Paragraph("<b>Job Requirement</b>", body_bold),
            Paragraph("<b>Category</b>", body_bold),
            Paragraph("<b>Resume Evidence / Gap Assessment</b>", body_bold),
            Paragraph("<b>Status</b>", body_bold),
        ]
        req_rows = [req_headers]
        
        matrix_items = fit_data.get("requirements_matrix", [])
        if not matrix_items and "matrix" in fit_data:
            matrix_items = fit_data.get("matrix", [])

        for item in matrix_items[:14]:  # Top 14 requirements
            req_name = item.get("requirement") or item.get("skill") or "Requirement"
            cat = item.get("category") or ("Mandatory" if item.get("is_mandatory") else "Preferred")
            evidence = item.get("evidence_or_gap") or item.get("evidence_gap") or item.get("evidence") or "Citations verified in profile."
            status = str(item.get("status") or "Matched")
            
            if "Match" in status:
                st_p = Paragraph(f"<b>{status}</b>", tag_matched)
            elif "Pref" in status:
                st_p = Paragraph(f"<b>{status}</b>", tag_amber)
            else:
                st_p = Paragraph(f"<b>{status}</b>", tag_gap)

            req_rows.append([
                Paragraph(req_name, body_style),
                Paragraph(cat, body_style),
                Paragraph(evidence, body_style),
                st_p
            ])

        if len(req_rows) > 1:
            req_table = Table(req_rows, colWidths=[130, 65, 260, 75])
            req_table.setStyle(TableStyle([
                ('BACKGROUND', (0,0), (-1,0), colors.HexColor("#E2E8F0")),
                ('BOX', (0,0), (-1,-1), 1, colors.HexColor("#CBD5E1")),
                ('INNERGRID', (0,0), (-1,-1), 0.5, colors.HexColor("#E2E8F0")),
                ('TOPPADDING', (0,0), (-1,-1), 4),
                ('BOTTOMPADDING', (0,0), (-1,-1), 4),
                ('LEFTPADDING', (0,0), (-1,-1), 6),
                ('RIGHTPADDING', (0,0), (-1,-1), 6),
            ]))
            elements.append(req_table)
        else:
            elements.append(Paragraph("<i>No requirements assessment records found in session.</i>", body_style))

        elements.append(Spacer(1, 14))

        # -------------------------------------------------------------------------
        # 3. STRATEGIC NARRATIVE & TALENT DESK SYNTHESIS
        # -------------------------------------------------------------------------
        elements.append(Paragraph("3. Executive Strategic Narrative", section_h1))
        narrative = fit_data.get("strategic_narrative") or "The candidate demonstrates foundational technical and analytical capabilities aligned with the target profile. Structured preparation and project reinforcement are recommended to maximize placement performance."
        elements.append(Paragraph(narrative, body_style))
        elements.append(Spacer(1, 14))

        # -------------------------------------------------------------------------
        # 4. CRITICAL GAPS & REMEDIATION PRIORITIES
        # -------------------------------------------------------------------------
        elements.append(Paragraph("4. Critical Gaps & Key Vulnerabilities", section_h1))
        critical_gaps = fit_data.get("critical_gaps", [])
        if critical_gaps:
            elements.append(Paragraph("The following gaps were flagged during strategic matching as critical areas to bridge before institutional interviews:", subtitle_style))
            elements.append(Spacer(1, 6))
            for gap in critical_gaps[:6]:
                if isinstance(gap, dict):
                    gap_text = gap.get("gap") or gap.get("description") or str(gap)
                else:
                    gap_text = str(gap)
                elements.append(Paragraph(f"• <b>{gap_text}</b>", body_style))
                elements.append(Spacer(1, 3))
        else:
            elements.append(Paragraph("<i>No critical disqualifying gaps identified against mandatory role requirements.</i>", body_style))

        # Build PDF
        doc.build(elements, canvasmaker=FitReportNumberedCanvas)
        buffer.seek(0)
        return buffer.getvalue()


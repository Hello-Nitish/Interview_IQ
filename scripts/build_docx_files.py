"""
build_docx_files.py
Converts all 5 Markdown files in docs/ to executive-styled Microsoft Word (.docx) files.
"""

import os
import re
from docx import Document
from docx.shared import Inches, Pt, RGBColor
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.enum.table import WD_TABLE_ALIGNMENT, WD_ALIGN_VERTICAL
from docx.oxml import OxmlElement, parse_xml
from docx.oxml.ns import nsdecls, qn

DOCS_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "docs")

FILES_TO_CONVERT = [
    "PROJECT_LOG",
    "PROJECT_STATUS",
    "KT_DOCUMENT",
    "TECH_ARCHITECTURE",
    "BUSINESS_CASE",
    "GITHUB_DEPLOYMENT_AND_PUSH_STRATEGY",
    "MOBILE_AND_TAB_VIEW_GUIDE"
]

def set_cell_background(cell, fill_hex):
    tcPr = cell._element.get_or_add_tcPr()
    shd = parse_xml(f'<w:shd {nsdecls("w")} w:fill="{fill_hex}"/>')
    tcPr.append(shd)

def set_cell_margins(cell, top=100, bottom=100, left=150, right=150):
    tcPr = cell._element.get_or_add_tcPr()
    tcMar = parse_xml(f'''
        <w:tcMar {nsdecls("w")}>
            <w:top w:w="{top}" w:type="dxa"/>
            <w:bottom w:w="{bottom}" w:type="dxa"/>
            <w:left w:w="{left}" w:type="dxa"/>
            <w:right w:w="{right}" w:type="dxa"/>
        </w:tcMar>
    ''')
    tcPr.append(tcMar)

def set_table_borders(table, color="CBD5E1"):
    tblPr = table._element.xpath('w:tblPr')
    if tblPr:
        borders = parse_xml(f'''
            <w:tblBorders {nsdecls("w")}>
                <w:top w:val="single" w:sz="6" w:space="0" w:color="{color}"/>
                <w:left w:val="none"/>
                <w:bottom w:val="single" w:sz="6" w:space="0" w:color="{color}"/>
                <w:right w:val="none"/>
                <w:insideH w:val="single" w:sz="4" w:space="0" w:color="{color}"/>
                <w:insideV w:val="single" w:sz="4" w:space="0" w:color="{color}"/>
            </w:tblBorders>
        ''')
        tblPr[0].append(borders)

def add_inline_formatted_text(paragraph, text, base_font_size=10.5, is_bullet=False):
    # Regex splits on bold (**text**), inline code (`code`), or italic (*text*)
    tokens = re.split(r'(\*\*.*?\*\*|`.*?`|\*.*?\*)', text)
    for token in tokens:
        if not token:
            continue
        if token.startswith('**') and token.endswith('**') and len(token) >= 4:
            run = paragraph.add_run(token[2:-2])
            run.bold = True
            run.font.name = 'Calibri'
            run.font.size = Pt(base_font_size)
            run.font.color.rgb = RGBColor(0x0F, 0x17, 0x2A) # Dark slate
        elif token.startswith('`') and token.endswith('`') and len(token) >= 2:
            run = paragraph.add_run(token[1:-1])
            run.font.name = 'Consolas'
            run.font.size = Pt(base_font_size - 1)
            run.font.color.rgb = RGBColor(0x0F, 0x51, 0x82) # Dark teal/blue
        elif token.startswith('*') and token.endswith('*') and len(token) >= 2:
            run = paragraph.add_run(token[1:-1])
            run.italic = True
            run.font.name = 'Calibri'
            run.font.size = Pt(base_font_size)
            run.font.color.rgb = RGBColor(0x33, 0x41, 0x55)
        else:
            run = paragraph.add_run(token)
            run.font.name = 'Calibri'
            run.font.size = Pt(base_font_size)
            run.font.color.rgb = RGBColor(0x1E, 0x29, 0x3B)

def convert_md_to_docx(md_path, docx_path):
    print(f"Converting: {os.path.basename(md_path)} -> {os.path.basename(docx_path)}")
    with open(md_path, "r", encoding="utf-8") as f:
        lines = f.readlines()

    doc = Document()
    
    # Page setup: Standard letter, 0.8 inch margins
    sections = doc.sections
    for s in sections:
        s.top_margin = Inches(0.8)
        s.bottom_margin = Inches(0.8)
        s.left_margin = Inches(0.8)
        s.right_margin = Inches(0.8)

    i = 0
    in_code_block = False
    code_block_lines = []
    
    while i < len(lines):
        line = lines[i].rstrip('\r\n')
        stripped = line.strip()

        # Handle Code Block Start / End
        if stripped.startswith("```"):
            if in_code_block:
                # End of code block
                in_code_block = False
                code_text = "\n".join(code_block_lines)
                table = doc.add_table(rows=1, cols=1)
                table.alignment = WD_TABLE_ALIGNMENT.CENTER
                cell = table.cell(0, 0)
                set_cell_background(cell, "F1F5F9") # Slate-100
                set_cell_margins(cell, top=120, bottom=120, left=200, right=200)
                cp = cell.paragraphs[0]
                cp.paragraph_format.space_before = Pt(4)
                cp.paragraph_format.space_after = Pt(4)
                run = cp.add_run(code_text)
                run.font.name = "Consolas"
                run.font.size = Pt(9)
                run.font.color.rgb = RGBColor(0x0F, 0x17, 0x2A)
                # Spacing after code block table
                sp = doc.add_paragraph()
                sp.paragraph_format.space_after = Pt(6)
                code_block_lines = []
            else:
                in_code_block = True
                code_block_lines = []
            i += 1
            continue

        if in_code_block:
            code_block_lines.append(line)
            i += 1
            continue

        # Empty line
        if not stripped:
            i += 1
            continue

        # Markdown Horizontal Rule
        if stripped in ["---", "***", "___"]:
            p = doc.add_paragraph()
            p.paragraph_format.space_before = Pt(6)
            p.paragraph_format.space_after = Pt(6)
            pBorder = parse_xml(f'<w:pBdr {nsdecls("w")}><w:bottom w:val="single" w:sz="6" w:space="1" w:color="CBD5E1"/></w:pBdr>')
            p._element.get_or_add_pPr().append(pBorder)
            i += 1
            continue

        # Markdown Headings
        if stripped.startswith("# ") and not stripped.startswith("## "):
            p = doc.add_paragraph()
            p.paragraph_format.space_before = Pt(14)
            p.paragraph_format.space_after = Pt(6)
            run = p.add_run(stripped[2:].strip())
            run.font.name = 'Calibri'
            run.font.size = Pt(22)
            run.bold = True
            run.font.color.rgb = RGBColor(0x0F, 0x17, 0x2A) # Navy 900
            i += 1
            continue

        if stripped.startswith("## "):
            p = doc.add_paragraph()
            p.paragraph_format.space_before = Pt(12)
            p.paragraph_format.space_after = Pt(4)
            run = p.add_run(stripped[3:].strip())
            run.font.name = 'Calibri'
            run.font.size = Pt(15)
            run.bold = True
            run.font.color.rgb = RGBColor(0x1E, 0x3A, 0x8A) # Blue 900
            i += 1
            continue

        if stripped.startswith("### "):
            p = doc.add_paragraph()
            p.paragraph_format.space_before = Pt(10)
            p.paragraph_format.space_after = Pt(3)
            run = p.add_run(stripped[4:].strip())
            run.font.name = 'Calibri'
            run.font.size = Pt(12.5)
            run.bold = True
            run.font.color.rgb = RGBColor(0x25, 0x63, 0xEB) # Blue 600
            i += 1
            continue

        if stripped.startswith("#### "):
            p = doc.add_paragraph()
            p.paragraph_format.space_before = Pt(8)
            p.paragraph_format.space_after = Pt(2)
            run = p.add_run(stripped[5:].strip())
            run.font.name = 'Calibri'
            run.font.size = Pt(11)
            run.bold = True
            run.font.color.rgb = RGBColor(0x33, 0x41, 0x55) # Slate 700
            i += 1
            continue

        # Markdown Table Detection
        if stripped.startswith("|") and stripped.endswith("|"):
            # Collect all table lines
            table_lines = []
            while i < len(lines) and lines[i].strip().startswith("|") and lines[i].strip().endswith("|"):
                table_lines.append(lines[i].strip())
                i += 1

            if len(table_lines) >= 2:
                # Parse header
                header_cols = [c.strip() for c in table_lines[0].split("|")[1:-1]]
                # Check if second line is separator (e.g. |--|--|)
                data_start_idx = 1
                if len(table_lines) > 1 and re.match(r'^[|\s\-:]+$', table_lines[1]):
                    data_start_idx = 2

                data_rows = []
                for row_line in table_lines[data_start_idx:]:
                    cols = [c.strip() for c in row_line.split("|")[1:-1]]
                    data_rows.append(cols)

                num_cols = len(header_cols)
                if num_cols > 0:
                    tbl = doc.add_table(rows=len(data_rows) + 1, cols=num_cols)
                    tbl.alignment = WD_TABLE_ALIGNMENT.CENTER
                    set_table_borders(tbl, "CBD5E1")

                    # Style header row
                    hdr_cells = tbl.rows[0].cells
                    for col_idx, col_name in enumerate(header_cols):
                        if col_idx < len(hdr_cells):
                            cell = hdr_cells[col_idx]
                            set_cell_background(cell, "0F172A") # Deep Navy
                            set_cell_margins(cell, top=100, bottom=100, left=120, right=120)
                            p = cell.paragraphs[0]
                            p.paragraph_format.space_before = Pt(2)
                            p.paragraph_format.space_after = Pt(2)
                            run = p.add_run(col_name)
                            run.font.name = 'Calibri'
                            run.font.size = Pt(10)
                            run.bold = True
                            run.font.color.rgb = RGBColor(0xFF, 0xFF, 0xFF)

                    # Populate data rows
                    for r_idx, row_data in enumerate(data_rows):
                        row_cells = tbl.rows[r_idx + 1].cells
                        row_bg = "F8FAFC" if (r_idx % 2 == 1) else "FFFFFF"
                        for c_idx, val in enumerate(row_data):
                            if c_idx < len(row_cells):
                                cell = row_cells[c_idx]
                                set_cell_background(cell, row_bg)
                                set_cell_margins(cell, top=80, bottom=80, left=120, right=120)
                                p = cell.paragraphs[0]
                                p.paragraph_format.space_before = Pt(2)
                                p.paragraph_format.space_after = Pt(2)
                                add_inline_formatted_text(p, val, base_font_size=9.5)

                    # Post table spacing
                    doc.add_paragraph().paragraph_format.space_after = Pt(6)
            continue

        # Bullet List (- or *)
        if re.match(r'^[\-\*]\s+', stripped):
            item_text = re.sub(r'^[\-\*]\s+', '', stripped)
            p = doc.add_paragraph(style='List Bullet')
            p.paragraph_format.space_before = Pt(1)
            p.paragraph_format.space_after = Pt(2)
            add_inline_formatted_text(p, item_text, base_font_size=10.5, is_bullet=True)
            i += 1
            continue

        # Numbered List (1. , 2. )
        if re.match(r'^\d+\.\s+', stripped):
            item_text = re.sub(r'^\d+\.\s+', '', stripped)
            p = doc.add_paragraph(style='List Number')
            p.paragraph_format.space_before = Pt(1)
            p.paragraph_format.space_after = Pt(2)
            add_inline_formatted_text(p, item_text, base_font_size=10.5)
            i += 1
            continue

        # Regular Paragraph
        p = doc.add_paragraph()
        p.paragraph_format.space_before = Pt(2)
        p.paragraph_format.space_after = Pt(4)
        add_inline_formatted_text(p, stripped, base_font_size=10.5)
        i += 1

    doc.save(docx_path)
    file_size = os.path.getsize(docx_path)
    print(f"Successfully generated {docx_path} ({file_size} bytes)")

def main():
    print(f"Starting DOCX regeneration in {DOCS_DIR}")
    for fname in FILES_TO_CONVERT:
        md_file = os.path.join(DOCS_DIR, f"{fname}.md")
        docx_file = os.path.join(DOCS_DIR, f"{fname}.docx")
        if os.path.exists(md_file):
            convert_md_to_docx(md_file, docx_file)
        else:
            print(f"Warning: {md_file} not found!")

    print("\nAll DOCX files generated and synchronized successfully!")

if __name__ == "__main__":
    main()

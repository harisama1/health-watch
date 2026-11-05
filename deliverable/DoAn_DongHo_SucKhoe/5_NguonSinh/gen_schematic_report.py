"""Schematic analysis report -> outputs/schematic_analysis_report.docx. Needs python-docx and pdftoppm.
usage: python3 tools/gen_schematic_report.py"""
import os, sys
HERE = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, HERE)
from report_docx import Report, ROOT
from schematic_report_content import CONTENT
Report('Đồng hồ theo dõi sức khỏe: báo cáo phân tích schematic', 'Báo cáo phân tích schematic: đồng hồ theo dõi sức khỏe').render(
    CONTENT, os.path.join(ROOT, 'outputs', 'schematic_analysis_report.docx'))

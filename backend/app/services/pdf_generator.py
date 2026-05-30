from reportlab.lib import colors
from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer, HRFlowable, Image, PageBreak
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.pdfgen import canvas
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_RIGHT, TA_JUSTIFY
from reportlab.graphics.shapes import Drawing, Rect, String, Line
from reportlab.graphics import renderPDF
from datetime import datetime
from typing import Dict, Any, List
import tempfile
import logging
from pathlib import Path

from app.models.schemas import JobDetailsResponse

logger = logging.getLogger(__name__)

# Professional Color Scheme
class ForensicColors:
    PRIMARY = colors.HexColor('#1a365d')  # Dark blue
    SECONDARY = colors.HexColor('#2c5282')  # Medium blue
    ACCENT = colors.HexColor('#3182ce')  # Light blue
    SUCCESS = colors.HexColor('#276749')  # Green
    WARNING = colors.HexColor('#c05621')  # Orange
    ERROR = colors.HexColor('#c53030')  # Red
    LIGHT_BG = colors.HexColor('#f7fafc')  # Light gray
    BORDER = colors.HexColor('#e2e8f0')  # Border gray
    TEXT = colors.HexColor('#2d3748')  # Dark text
    MUTED = colors.HexColor('#718096')  # Muted text


class PDFReportGenerator:
    """Generates professional forensic PDF reports"""
    
    @staticmethod
    def create_header_footer(canvas_obj, doc):
        """Create professional header and footer for PDF pages"""
        canvas_obj.saveState()
        
        # Header background
        canvas_obj.setFillColor(ForensicColors.PRIMARY)
        canvas_obj.rect(0, 10.2*inch, 8.5*inch, 0.8*inch, fill=True, stroke=False)
        
        # Header text
        canvas_obj.setFillColor(colors.white)
        canvas_obj.setFont('Helvetica-Bold', 14)
        canvas_obj.drawString(inch, 10.5*inch, "FORENSIC EVIDENCE ACQUISITION SYSTEM")
        
        canvas_obj.setFont('Helvetica', 9)
        canvas_obj.drawString(inch, 10.3*inch, "Digital Evidence Report • Law Enforcement Use Only")
        
        # Header accent line
        canvas_obj.setStrokeColor(ForensicColors.ACCENT)
        canvas_obj.setLineWidth(3)
        canvas_obj.line(inch, 10.15*inch, 7.5*inch, 10.15*inch)
        
        # Footer background
        canvas_obj.setFillColor(ForensicColors.LIGHT_BG)
        canvas_obj.rect(0, 0, 8.5*inch, 0.6*inch, fill=True, stroke=False)
        
        # Footer line
        canvas_obj.setStrokeColor(ForensicColors.BORDER)
        canvas_obj.setLineWidth(1)
        canvas_obj.line(inch, 0.6*inch, 7.5*inch, 0.6*inch)
        
        # Footer text
        canvas_obj.setFillColor(ForensicColors.MUTED)
        canvas_obj.setFont('Helvetica', 8)
        canvas_obj.drawString(inch, 0.35*inch, 
                            f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S UTC')}")
        canvas_obj.drawString(4.25*inch - 30, 0.35*inch, "CONFIDENTIAL")
        canvas_obj.drawRightString(7.5*inch, 0.35*inch, f"Page {doc.page}")
        
        # Watermark (subtle)
        canvas_obj.saveState()
        canvas_obj.setFillColor(colors.Color(0.9, 0.9, 0.9, alpha=0.3))
        canvas_obj.setFont('Helvetica-Bold', 60)
        canvas_obj.translate(4.25*inch, 5.5*inch)
        canvas_obj.rotate(45)
        canvas_obj.drawCentredString(0, 0, "FEAS REPORT")
        canvas_obj.restoreState()
        
        canvas_obj.restoreState()
    
    @staticmethod
    def _create_styles():
        """Create custom paragraph styles"""
        styles = getSampleStyleSheet()
        
        # Title style
        styles.add(ParagraphStyle(
            'ReportTitle',
            parent=styles['Heading1'],
            fontSize=24,
            spaceAfter=6,
            spaceBefore=20,
            alignment=TA_CENTER,
            textColor=ForensicColors.PRIMARY,
            fontName='Helvetica-Bold'
        ))
        
        # Subtitle style
        styles.add(ParagraphStyle(
            'ReportSubtitle',
            parent=styles['Normal'],
            fontSize=11,
            spaceAfter=30,
            alignment=TA_CENTER,
            textColor=ForensicColors.MUTED
        ))
        
        # Section header style
        styles.add(ParagraphStyle(
            'SectionHeader',
            parent=styles['Heading2'],
            fontSize=14,
            spaceBefore=20,
            spaceAfter=10,
            textColor=ForensicColors.PRIMARY,
            borderPadding=(5, 5, 5, 5),
            fontName='Helvetica-Bold'
        ))
        
        # Subsection style
        styles.add(ParagraphStyle(
            'SubsectionHeader',
            parent=styles['Heading3'],
            fontSize=11,
            spaceBefore=15,
            spaceAfter=8,
            textColor=ForensicColors.SECONDARY,
            fontName='Helvetica-Bold'
        ))
        
        # Body text style (use different name to avoid conflict with default)
        styles.add(ParagraphStyle(
            'ForensicBodyText',
            parent=styles['Normal'],
            fontSize=10,
            spaceAfter=8,
            textColor=ForensicColors.TEXT,
            alignment=TA_JUSTIFY
        ))
        
        # Hash display style
        styles.add(ParagraphStyle(
            'HashText',
            parent=styles['Code'],
            fontSize=8,
            fontName='Courier',
            textColor=ForensicColors.PRIMARY,
            backColor=ForensicColors.LIGHT_BG
        ))
        
        return styles
    
    @staticmethod
    def _create_section_header_table(title: str, icon_char: str = "▸"):
        """Create a styled section header"""
        header_data = [[f"{icon_char}  {title}"]]
        header_table = Table(header_data, colWidths=[6.5*inch])
        header_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, -1), ForensicColors.PRIMARY),
            ('TEXTCOLOR', (0, 0), (-1, -1), colors.white),
            ('FONTNAME', (0, 0), (-1, -1), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, -1), 12),
            ('PADDING', (0, 0), (-1, -1), 10),
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
            ('LEFTPADDING', (0, 0), (-1, -1), 15),
            ('TOPPADDING', (0, 0), (-1, -1), 8),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 8),
        ]))
        return header_table
    
    @staticmethod
    def _create_info_table(data: list, col_widths: list = None):
        """Create a professionally styled info table"""
        if col_widths is None:
            col_widths = [2*inch, 4.5*inch]
        
        table = Table(data, colWidths=col_widths)
        style_commands = [
            ('BACKGROUND', (0, 0), (0, -1), ForensicColors.LIGHT_BG),
            ('TEXTCOLOR', (0, 0), (0, -1), ForensicColors.SECONDARY),
            ('TEXTCOLOR', (1, 0), (-1, -1), ForensicColors.TEXT),
            ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
            ('FONTNAME', (1, 0), (-1, -1), 'Helvetica'),
            ('FONTSIZE', (0, 0), (-1, -1), 10),
            ('ALIGN', (0, 0), (0, -1), 'RIGHT'),
            ('ALIGN', (1, 0), (-1, -1), 'LEFT'),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
            ('PADDING', (0, 0), (-1, -1), 8),
            ('GRID', (0, 0), (-1, -1), 0.5, ForensicColors.BORDER),
            ('BOX', (0, 0), (-1, -1), 1, ForensicColors.SECONDARY),
        ]
        
        # Add alternating row colors
        for i in range(len(data)):
            if i % 2 == 1:
                style_commands.append(('BACKGROUND', (1, i), (-1, i), colors.Color(0.98, 0.98, 1.0)))
        
        table.setStyle(TableStyle(style_commands))
        return table

    @staticmethod
    def generate_report(job_details: JobDetailsResponse) -> str:
        """Generate professional PDF report from job details"""
        try:
            # Create temporary file for PDF
            temp_file = tempfile.NamedTemporaryFile(delete=False, suffix='.pdf')
            temp_path = temp_file.name
            temp_file.close()
            
            # Create document with adjusted margins for header/footer
            doc = SimpleDocTemplate(
                temp_path,
                pagesize=letter,
                rightMargin=inch,
                leftMargin=inch,
                topMargin=1.3*inch,
                bottomMargin=0.8*inch
            )
            
            styles = PDFReportGenerator._create_styles()
            story = []
            
            # ==================== TITLE PAGE ====================
            story.append(Spacer(1, 60))
            story.append(Paragraph("FORENSIC EVIDENCE REPORT", styles['ReportTitle']))
            story.append(Paragraph("Digital Evidence Acquisition & Analysis", styles['ReportSubtitle']))
            
            # Report summary box
            story.append(Spacer(1, 20))
            
            source_str = job_details.source.upper() if job_details.source else "UNKNOWN"
            platform_str = job_details.platform.upper() if job_details.platform else "LOCAL"
            
            summary_data = [
                ["REPORT SUMMARY", ""],
                ["Job Reference:", job_details.job_id],
                ["Evidence Source:", f"{source_str} ({platform_str})"],
                ["Status:", job_details.status.upper() if job_details.status else "UNKNOWN"],
                ["Report Generated:", datetime.now().strftime('%Y-%m-%d %H:%M:%S UTC')],
            ]
            
            summary_table = Table(summary_data, colWidths=[2*inch, 4.5*inch])
            summary_table.setStyle(TableStyle([
                ('SPAN', (0, 0), (-1, 0)),
                ('BACKGROUND', (0, 0), (-1, 0), ForensicColors.PRIMARY),
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
                ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                ('FONTSIZE', (0, 0), (-1, 0), 12),
                ('ALIGN', (0, 0), (-1, 0), 'CENTER'),
                ('BACKGROUND', (0, 1), (0, -1), ForensicColors.LIGHT_BG),
                ('TEXTCOLOR', (0, 1), (0, -1), ForensicColors.SECONDARY),
                ('FONTNAME', (0, 1), (0, -1), 'Helvetica-Bold'),
                ('FONTSIZE', (0, 1), (-1, -1), 10),
                ('PADDING', (0, 0), (-1, -1), 10),
                ('GRID', (0, 0), (-1, -1), 0.5, ForensicColors.BORDER),
                ('BOX', (0, 0), (-1, -1), 2, ForensicColors.PRIMARY),
            ]))
            story.append(summary_table)
            
            # ==================== CASE INFORMATION ====================
            story.append(Spacer(1, 25))
            story.append(PDFReportGenerator._create_section_header_table("CASE INFORMATION", "📋"))
            story.append(Spacer(1, 10))
            
            investigator_id = job_details.chain_of_custody[0].investigator_id if job_details.chain_of_custody else "N/A"
            
            # Helper function to truncate long URLs
            def truncate_url(url, max_length=60):
                if url and len(url) > max_length:
                    return url[:max_length] + "..."
                return url or "N/A"
            
            case_data = [
                ["Job ID:", job_details.job_id],
                ["Investigator ID:", investigator_id],
                ["Source Type:", source_str],
                ["Platform:", platform_str],
                ["Acquisition Date:", job_details.created_at.strftime('%Y-%m-%d %H:%M:%S UTC') if job_details.created_at else "N/A"],
                ["Completion Date:", job_details.completed_at.strftime('%Y-%m-%d %H:%M:%S UTC') if job_details.completed_at else "In Progress"],
            ]
            
            if job_details.original_url:
                case_data.append(["Original URL:", truncate_url(job_details.original_url)])
            
            story.append(PDFReportGenerator._create_info_table(case_data))
            
            # ==================== DIGITAL FINGERPRINT ====================
            story.append(Spacer(1, 25))
            story.append(PDFReportGenerator._create_section_header_table("DIGITAL FINGERPRINT", "🔐"))
            story.append(Spacer(1, 10))
            
            # Format file size nicely
            file_size = job_details.metadata.file_size or 0
            if file_size >= 1024 * 1024:
                size_str = f"{file_size / (1024 * 1024):.2f} MB ({file_size:,} bytes)"
            elif file_size >= 1024:
                size_str = f"{file_size / 1024:.2f} KB ({file_size:,} bytes)"
            else:
                size_str = f"{file_size:,} bytes"
            
            hash_data = [
                ["SHA-256 Hash:", job_details.metadata.sha256_hash or "N/A"],
                ["File Name:", job_details.metadata.file_name or "N/A"],
                ["File Size:", size_str],
                ["MIME Type:", job_details.metadata.mime_type or "N/A"],
            ]
            
            story.append(PDFReportGenerator._create_info_table(hash_data))
            
            # Hash verification notice
            story.append(Spacer(1, 10))
            notice_text = (
                '<font color="#276749"><b>✓ INTEGRITY NOTICE:</b></font> The SHA-256 hash above '
                'serves as the unique digital fingerprint for this evidence. Any modification to '
                'the original file will produce a different hash value, indicating potential '
                'tampering. Verify this hash against the original to confirm evidence integrity.'
            )
            story.append(Paragraph(notice_text, styles['ForensicBodyText']))
            
            # ==================== CHAIN OF CUSTODY ====================
            story.append(Spacer(1, 25))
            story.append(PDFReportGenerator._create_section_header_table("CHAIN OF CUSTODY", "🔗"))
            story.append(Spacer(1, 10))
            
            if job_details.chain_of_custody:
                custody_data = [["#", "Timestamp", "Event", "Investigator", "Details"]]
                for idx, entry in enumerate(job_details.chain_of_custody, 1):
                    details_str = str(entry.details) if entry.details else ""
                    if len(details_str) > 80:
                        details_str = details_str[:80] + "..."
                    
                    custody_data.append([
                        str(idx),
                        entry.timestamp.strftime('%Y-%m-%d\n%H:%M:%S') if entry.timestamp else "N/A",
                        entry.event or "N/A",
                        entry.investigator_id or "N/A",
                        details_str
                    ])
                
                custody_table = Table(custody_data, colWidths=[0.4*inch, 1*inch, 1.3*inch, 1.2*inch, 2.6*inch])
                
                style_commands = [
                    # Header row
                    ('BACKGROUND', (0, 0), (-1, 0), ForensicColors.SECONDARY),
                    ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
                    ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                    ('FONTSIZE', (0, 0), (-1, 0), 9),
                    ('ALIGN', (0, 0), (-1, 0), 'CENTER'),
                    # Data rows
                    ('FONTNAME', (0, 1), (-1, -1), 'Helvetica'),
                    ('FONTSIZE', (0, 1), (-1, -1), 8),
                    ('ALIGN', (0, 1), (0, -1), 'CENTER'),
                    ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
                    ('PADDING', (0, 0), (-1, -1), 6),
                    ('GRID', (0, 0), (-1, -1), 0.5, ForensicColors.BORDER),
                    ('BOX', (0, 0), (-1, -1), 1, ForensicColors.SECONDARY),
                ]
                
                # Alternating row colors
                for i in range(1, len(custody_data)):
                    if i % 2 == 0:
                        style_commands.append(('BACKGROUND', (0, i), (-1, i), ForensicColors.LIGHT_BG))
                
                custody_table.setStyle(TableStyle(style_commands))
                story.append(custody_table)
            else:
                story.append(Paragraph("<i>No chain of custody entries recorded.</i>", styles['ForensicBodyText']))
            
            # ==================== METADATA SECTION ====================
            if job_details.metadata.exif_data:
                story.append(Spacer(1, 25))
                story.append(PDFReportGenerator._create_section_header_table("EXIF METADATA", "📷"))
                story.append(Spacer(1, 10))
                
                exif_data = []
                for key, value in job_details.metadata.exif_data.items():
                    value_str = str(value)
                    if len(value_str) > 100:
                        value_str = value_str[:100] + "..."
                    exif_data.append([key, value_str])
                
                if exif_data:
                    story.append(PDFReportGenerator._create_info_table(exif_data))
            
            # ==================== CERTIFICATION SECTION ====================
            story.append(Spacer(1, 30))
            story.append(PDFReportGenerator._create_section_header_table("CERTIFICATION", "✅"))
            story.append(Spacer(1, 10))
            
            cert_text = (
                'This report certifies that the digital evidence described herein has been acquired, '
                'processed, and documented in accordance with forensic best practices. The chain of custody '
                'has been maintained throughout the acquisition process, and all digital fingerprints have '
                'been recorded for integrity verification purposes.'
            )
            story.append(Paragraph(cert_text, styles['ForensicBodyText']))
            
            story.append(Spacer(1, 20))
            
            # Signature area
            sig_data = [
                ["VERIFICATION", "", ""],
                ["Examiner Signature:", "________________________", "Date: ____________"],
                ["Supervisor Signature:", "________________________", "Date: ____________"],
                ["Report Seal:", "________________________", ""],
            ]
            
            sig_table = Table(sig_data, colWidths=[1.8*inch, 2.5*inch, 2.2*inch])
            sig_table.setStyle(TableStyle([
                ('SPAN', (0, 0), (-1, 0)),
                ('BACKGROUND', (0, 0), (-1, 0), ForensicColors.LIGHT_BG),
                ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                ('FONTSIZE', (0, 0), (-1, 0), 10),
                ('ALIGN', (0, 0), (-1, 0), 'CENTER'),
                ('FONTNAME', (0, 1), (0, -1), 'Helvetica-Bold'),
                ('FONTSIZE', (0, 1), (-1, -1), 9),
                ('TEXTCOLOR', (0, 1), (-1, -1), ForensicColors.MUTED),
                ('PADDING', (0, 0), (-1, -1), 10),
                ('TOPPADDING', (0, 1), (-1, -1), 15),
                ('BOTTOMPADDING', (0, 1), (-1, -1), 15),
                ('BOX', (0, 0), (-1, -1), 1, ForensicColors.BORDER),
            ]))
            story.append(sig_table)
            
            # ==================== DISCLAIMER ====================
            story.append(Spacer(1, 25))
            disclaimer_text = (
                '<font size="8" color="#718096"><b>DISCLAIMER:</b> This forensic evidence report is generated '
                'automatically by the Forensic Evidence Acquisition System (FEAS). The information contained herein '
                'is intended for law enforcement and authorized personnel only. Unauthorized distribution, modification, '
                'or use of this report may be subject to legal penalties. The integrity of this evidence should be '
                'verified using the SHA-256 hash provided above before use in any legal proceedings.</font>'
            )
            story.append(Paragraph(disclaimer_text, styles['Normal']))
            
            # Build PDF
            doc.build(story, 
                     onFirstPage=PDFReportGenerator.create_header_footer,
                     onLaterPages=PDFReportGenerator.create_header_footer)
            
            logger.info(f"PDF report generated: {temp_path}")
            return temp_path
            
        except Exception as e:
            logger.error(f"PDF generation failed: {str(e)}")
            raise

    @staticmethod
    def generate_custom_report(report_data: Dict[str, Any]) -> str:
        """Generate professional custom PDF report based on selected sections and scan/cve/correlation outputs"""
        try:
            # Create temporary file for PDF
            temp_file = tempfile.NamedTemporaryFile(delete=False, suffix='.pdf')
            temp_path = temp_file.name
            temp_file.close()
            
            # Create document with adjusted margins for header/footer
            doc = SimpleDocTemplate(
                temp_path,
                pagesize=letter,
                rightMargin=inch,
                leftMargin=inch,
                topMargin=1.3*inch,
                bottomMargin=0.8*inch
            )
            
            styles = PDFReportGenerator._create_styles()
            story = []
            
            # ==================== TITLE PAGE ====================
            story.append(Spacer(1, 60))
            story.append(Paragraph("FORENSIC EVIDENCE REPORT", styles['ReportTitle']))
            story.append(Paragraph("Digital Evidence Acquisition & Analysis", styles['ReportSubtitle']))
            
            # Report summary box
            story.append(Spacer(1, 20))
            
            source_str = str(report_data.get('source', '')).upper()
            platform_str = str(report_data.get('platform_metadata', {}).get('platform', 'LOCAL')).upper()
            if not platform_str:
                platform_str = "LOCAL"
            
            summary_data = [
                ["REPORT SUMMARY", ""],
                ["Job Reference:", report_data.get('job_id', '')],
                ["Evidence Source:", f"{source_str} ({platform_str})"],
                ["Status:", str(report_data.get('status', '')).upper()],
                ["Report Generated:", datetime.now().strftime('%Y-%m-%d %H:%M:%S UTC')],
            ]
            
            summary_table = Table(summary_data, colWidths=[2*inch, 4.5*inch])
            summary_table.setStyle(TableStyle([
                ('SPAN', (0, 0), (-1, 0)),
                ('BACKGROUND', (0, 0), (-1, 0), ForensicColors.PRIMARY),
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
                ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                ('FONTSIZE', (0, 0), (-1, 0), 12),
                ('ALIGN', (0, 0), (-1, 0), 'CENTER'),
                ('BACKGROUND', (0, 1), (0, -1), ForensicColors.LIGHT_BG),
                ('TEXTCOLOR', (0, 1), (0, -1), ForensicColors.SECONDARY),
                ('FONTNAME', (0, 1), (0, -1), 'Helvetica-Bold'),
                ('FONTSIZE', (0, 1), (-1, -1), 10),
                ('PADDING', (0, 0), (-1, -1), 10),
                ('GRID', (0, 0), (-1, -1), 0.5, ForensicColors.BORDER),
                ('BOX', (0, 0), (-1, -1), 2, ForensicColors.PRIMARY),
            ]))
            story.append(summary_table)
            
            # ==================== CASE INFORMATION ====================
            story.append(Spacer(1, 25))
            story.append(PDFReportGenerator._create_section_header_table("CASE INFORMATION", "📋"))
            story.append(Spacer(1, 10))
            
            case_data = [
                ["Job ID:", report_data.get('job_id', '')],
                ["Source Type:", source_str],
                ["Platform:", platform_str],
                ["Acquisition Date:", report_data.get('created_at').strftime('%Y-%m-%d %H:%M:%S UTC') if report_data.get('created_at') else "N/A"],
                ["Completion Date:", report_data.get('completed_at').strftime('%Y-%m-%d %H:%M:%S UTC') if report_data.get('completed_at') else "In Progress"],
            ]
            
            if report_data.get('original_url'):
                url = report_data.get('original_url')
                truncated = url[:60] + "..." if len(url) > 60 else url
                case_data.append(["Original URL:", truncated])
            
            story.append(PDFReportGenerator._create_info_table(case_data))
            
            # ==================== DIGITAL FINGERPRINT ====================
            story.append(Spacer(1, 25))
            story.append(PDFReportGenerator._create_section_header_table("DIGITAL FINGERPRINT", "🔐"))
            story.append(Spacer(1, 10))
            
            file_size = report_data.get('file_size') or 0
            if file_size >= 1024 * 1024:
                size_str = f"{file_size / (1024 * 1024):.2f} MB ({file_size:,} bytes)"
            elif file_size >= 1024:
                size_str = f"{file_size / 1024:.2f} KB ({file_size:,} bytes)"
            else:
                size_str = f"{file_size:,} bytes"
            
            hash_data = [
                ["SHA-256 Hash:", report_data.get('sha256_hash') or "N/A"],
                ["File Name:", report_data.get('filename') or "N/A"],
                ["File Size:", size_str],
                ["MIME Type:", report_data.get('mime_type') or "N/A"],
            ]
            
            story.append(PDFReportGenerator._create_info_table(hash_data))
            
            story.append(Spacer(1, 10))
            integrity_val = report_data.get('integrity_status', 'VERIFIED')
            if integrity_val == "COMPROMISED":
                notice_text = (
                    '<font color="#c53030"><b>✗ INTEGRITY CRITICAL WARNING:</b></font> The SHA-256 hash '
                    'of this evidence is COMPROMISED. A digital fingerprint verification check has failed, '
                    'indicating the file was modified, tampered with, or corrupted post-acquisition.'
                )
            else:
                notice_text = (
                    '<font color="#276749"><b>✓ INTEGRITY NOTICE:</b></font> The SHA-256 hash above '
                    'serves as the unique digital fingerprint for this evidence. Any modification to '
                    'the original file will produce a different hash value, indicating potential '
                    'tampering. Verify this hash against the original to confirm evidence integrity.'
                )
            story.append(Paragraph(notice_text, styles['ForensicBodyText']))
            
            # ==================== CHAIN OF CUSTODY ====================
            if report_data.get('include_custody'):
                story.append(Spacer(1, 25))
                story.append(PDFReportGenerator._create_section_header_table("CHAIN OF CUSTODY", "🔗"))
                story.append(Spacer(1, 10))
                
                logs = report_data.get('chain_of_custody', [])
                if logs:
                    custody_data = [["#", "Timestamp", "Event", "Investigator", "Details"]]
                    for idx, entry in enumerate(logs, 1):
                        details_str = str(entry.details) if entry.details else ""
                        if len(details_str) > 80:
                            details_str = details_str[:80] + "..."
                        
                        custody_data.append([
                            str(idx),
                            entry.timestamp.strftime('%Y-%m-%d\n%H:%M:%S') if entry.timestamp else "N/A",
                            entry.event or "N/A",
                            entry.investigator_id or "N/A",
                            details_str
                        ])
                    
                    custody_table = Table(custody_data, colWidths=[0.4*inch, 1*inch, 1.3*inch, 1.2*inch, 2.6*inch])
                    
                    style_commands = [
                        ('BACKGROUND', (0, 0), (-1, 0), ForensicColors.SECONDARY),
                        ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
                        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                        ('FONTSIZE', (0, 0), (-1, 0), 9),
                        ('ALIGN', (0, 0), (-1, 0), 'CENTER'),
                        ('FONTNAME', (0, 1), (-1, -1), 'Helvetica'),
                        ('FONTSIZE', (0, 1), (-1, -1), 8),
                        ('ALIGN', (0, 1), (0, -1), 'CENTER'),
                        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
                        ('PADDING', (0, 0), (-1, -1), 6),
                        ('GRID', (0, 0), (-1, -1), 0.5, ForensicColors.BORDER),
                        ('BOX', (0, 0), (-1, -1), 1, ForensicColors.SECONDARY),
                    ]
                    
                    for i in range(1, len(custody_data)):
                        if i % 2 == 0:
                            style_commands.append(('BACKGROUND', (0, i), (-1, i), ForensicColors.LIGHT_BG))
                    
                    custody_table.setStyle(TableStyle(style_commands))
                    story.append(custody_table)
                else:
                    story.append(Paragraph("<i>No chain of custody entries recorded.</i>", styles['ForensicBodyText']))

            # ==================== NETWORK SCANNING ====================
            if report_data.get('include_scans') and report_data.get('scans'):
                story.append(Spacer(1, 25))
                story.append(PDFReportGenerator._create_section_header_table("NETWORK SCANNING RESULTS", "🌐"))
                story.append(Spacer(1, 10))
                
                scans = report_data.get('scans', [])
                for idx, s in enumerate(scans, 1):
                    status_str = (s.status or "").upper()
                    scan_data = [
                        [f"Scan #{idx} Details", ""],
                        ["Target:", s.target],
                        ["Scan Date:", s.scan_timestamp.strftime('%Y-%m-%d %H:%M:%S UTC') if s.scan_timestamp else "N/A"],
                        ["Status:", status_str],
                        ["Initiated By User:", s.initiated_by or "N/A"]
                    ]
                    
                    scan_info_table = Table(scan_data, colWidths=[2.2*inch, 4.3*inch])
                    scan_info_table.setStyle(TableStyle([
                        ('SPAN', (0, 0), (-1, 0)),
                        ('BACKGROUND', (0, 0), (-1, 0), ForensicColors.SECONDARY),
                        ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
                        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                        ('FONTSIZE', (0, 0), (-1, 0), 10),
                        ('BACKGROUND', (0, 1), (0, -1), ForensicColors.LIGHT_BG),
                        ('FONTNAME', (0, 1), (0, -1), 'Helvetica-Bold'),
                        ('FONTSIZE', (0, 1), (-1, -1), 9),
                        ('GRID', (0, 0), (-1, -1), 0.5, ForensicColors.BORDER),
                        ('BOX', (0, 0), (-1, -1), 1, ForensicColors.SECONDARY),
                        ('PADDING', (0, 0), (-1, -1), 5),
                    ]))
                    story.append(scan_info_table)
                    story.append(Spacer(1, 8))
                    
                    if status_str == "COMPLETED" and s.result_json:
                        res = s.result_json
                        hosts = res.get("hosts", [])
                        for h in hosts:
                            host_desc = f"<b>Host IP:</b> {h.get('ip')} | <b>Hostname:</b> {h.get('hostname') or 'N/A'} | <b>State:</b> {h.get('state')} | <b>OS:</b> {h.get('os_detection') or 'Unknown'}"
                            story.append(Paragraph(host_desc, styles['ForensicBodyText']))
                            story.append(Spacer(1, 4))
                            
                            ports = h.get("ports", [])
                            if ports:
                                port_table_data = [["Port", "Protocol", "State", "Service", "Version"]]
                                for p in ports:
                                    port_table_data.append([
                                        str(p.get("port")),
                                        p.get("protocol", "tcp"),
                                        p.get("state", "unknown"),
                                        p.get("service", "unknown"),
                                        p.get("version", "")
                                    ])
                                
                                port_table = Table(port_table_data, colWidths=[1*inch, 1*inch, 1*inch, 1.5*inch, 2*inch])
                                port_table.setStyle(TableStyle([
                                    ('BACKGROUND', (0, 0), (-1, 0), ForensicColors.LIGHT_BG),
                                    ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                                    ('FONTSIZE', (0, 0), (-1, -1), 8),
                                    ('GRID', (0, 0), (-1, -1), 0.5, ForensicColors.BORDER),
                                    ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                                    ('PADDING', (0, 0), (-1, -1), 4),
                                ]))
                                story.append(port_table)
                                story.append(Spacer(1, 10))
                            else:
                                story.append(Paragraph("&nbsp;&nbsp;&nbsp;&nbsp;<i>No open ports discovered on this host.</i>", styles['ForensicBodyText']))
                                story.append(Spacer(1, 8))
                    elif status_str == "FAILED":
                        err_text = f'<font color="#c53030"><b>Scan Error:</b> {s.error_message or "Unknown failure during nmap scan."}</font>'
                        story.append(Paragraph(err_text, styles['ForensicBodyText']))
                        story.append(Spacer(1, 10))
                    else:
                        story.append(Paragraph("<i>Scan is pending or currently running. No results available.</i>", styles['ForensicBodyText']))
                        story.append(Spacer(1, 10))

            # ==================== VULNERABILITIES ====================
            if report_data.get('include_vulnerabilities') and report_data.get('vulnerabilities'):
                story.append(Spacer(1, 25))
                story.append(PDFReportGenerator._create_section_header_table("CVE VULNERABILITY FINDINGS", "⚠️"))
                story.append(Spacer(1, 10))
                
                vulns = report_data.get('vulnerabilities', [])
                if vulns:
                    vuln_table_data = [["Port/Svc", "CVE ID", "CVSS", "Severity", "Description"]]
                    
                    for v in vulns:
                        svc_desc = f"{v.port}/{v.service or ''}"
                        cve_desc = v.cve_id or "N/A"
                        cvss_val = str(v.cvss_score) if v.cvss_score is not None else "N/A"
                        sev_val = (v.severity or "Unknown").upper()
                        
                        desc_para = Paragraph(v.description or "No description provided.", styles['ForensicBodyText'])
                        
                        vuln_table_data.append([
                            svc_desc,
                            cve_desc,
                            cvss_val,
                            sev_val,
                            desc_para
                        ])
                    
                    vuln_table = Table(vuln_table_data, colWidths=[1*inch, 1*inch, 0.6*inch, 1.1*inch, 2.8*inch])
                    
                    style_commands = [
                        ('BACKGROUND', (0, 0), (-1, 0), ForensicColors.SECONDARY),
                        ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
                        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                        ('FONTSIZE', (0, 0), (-1, -1), 8),
                        ('GRID', (0, 0), (-1, -1), 0.5, ForensicColors.BORDER),
                        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
                        ('ALIGN', (0, 0), (3, -1), 'CENTER'),
                        ('PADDING', (0, 0), (-1, -1), 5),
                    ]
                    
                    for i in range(1, len(vuln_table_data)):
                        sev_text = vuln_table_data[i][3]
                        bg_color = ForensicColors.LIGHT_BG
                        text_color = ForensicColors.TEXT
                        if sev_text == "CRITICAL":
                            bg_color = colors.HexColor('#fed7d7')
                            text_color = colors.HexColor('#9b2c2c')
                        elif sev_text == "HIGH":
                            bg_color = colors.HexColor('#feebc8')
                            text_color = colors.HexColor('#c05621')
                        elif sev_text == "MEDIUM":
                            bg_color = colors.HexColor('#feebc8')
                            text_color = colors.HexColor('#dd6b20')
                        elif sev_text == "LOW":
                            bg_color = colors.HexColor('#e2e8f0')
                            text_color = colors.HexColor('#4a5568')
                        elif sev_text == "INFORMATIONAL":
                            bg_color = colors.HexColor('#ebf8ff')
                            text_color = colors.HexColor('#2b6cb0')
                            
                        style_commands.append(('BACKGROUND', (3, i), (3, i), bg_color))
                        style_commands.append(('TEXTCOLOR', (3, i), (3, i), text_color))
                        style_commands.append(('FONTNAME', (3, i), (3, i), 'Helvetica-Bold'))
                        
                        if i % 2 == 0:
                            style_commands.append(('BACKGROUND', (0, i), (2, i), ForensicColors.LIGHT_BG))
                            style_commands.append(('BACKGROUND', (4, i), (4, i), ForensicColors.LIGHT_BG))
                    
                    vuln_table.setStyle(TableStyle(style_commands))
                    story.append(vuln_table)
                else:
                    story.append(Paragraph("<i>No vulnerabilities mapped.</i>", styles['ForensicBodyText']))
                story.append(Spacer(1, 10))

            # ==================== CORRELATION & ATTACK ANALYSIS ====================
            if report_data.get('include_correlation') and report_data.get('correlation'):
                corr = report_data.get('correlation')
                story.append(Spacer(1, 25))
                story.append(PDFReportGenerator._create_section_header_table("EVIDENCE CORRELATION & RISK ASSESSMENT", "🧠"))
                story.append(Spacer(1, 10))
                
                score = corr.get("score", 0)
                if score >= 75:
                    score_bg = colors.HexColor('#fed7d7')
                    score_text_color = colors.HexColor('#9b2c2c')
                    score_label = "CRITICAL SECURITY RISK"
                elif score >= 50:
                    score_bg = colors.HexColor('#feebc8')
                    score_text_color = colors.HexColor('#c05621')
                    score_label = "HIGH SECURITY RISK"
                elif score >= 25:
                    score_bg = colors.HexColor('#fefcbf')
                    score_text_color = colors.HexColor('#744210')
                    score_label = "MEDIUM SECURITY RISK"
                else:
                    score_bg = colors.HexColor('#c6f6d5')
                    score_text_color = colors.HexColor('#22543d')
                    score_label = "LOW SECURITY RISK"
                
                score_data = [[
                    f"Overall Case Risk Score: {score} / 100  |  {score_label}"
                ]]
                score_table = Table(score_data, colWidths=[6.5*inch])
                score_table.setStyle(TableStyle([
                    ('BACKGROUND', (0, 0), (-1, -1), score_bg),
                    ('TEXTCOLOR', (0, 0), (-1, -1), score_text_color),
                    ('FONTNAME', (0, 0), (-1, -1), 'Helvetica-Bold'),
                    ('FONTSIZE', (0, 0), (-1, -1), 11),
                    ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                    ('PADDING', (0, 0), (-1, -1), 8),
                    ('BOX', (0, 0), (-1, -1), 1.5, score_text_color),
                ]))
                story.append(score_table)
                story.append(Spacer(1, 15))
                
                flags = corr.get("flags", [])
                if flags:
                    story.append(Paragraph("<b>System Warning Flags:</b>", styles['SubsectionHeader']))
                    for f in flags:
                        sev = f.get("severity", "MEDIUM")
                        color_prefix = '<font color="#c53030"><b>[CRITICAL]</b></font>' if sev == "CRITICAL" else '<font color="#dd6b20"><b>[HIGH]</b></font>' if sev == "HIGH" else '<b>[MEDIUM]</b>'
                        flag_text = f"{color_prefix} <b>{f.get('title')}:</b> {f.get('description')}"
                        story.append(Paragraph(flag_text, styles['ForensicBodyText']))
                        story.append(Spacer(1, 4))
                    story.append(Spacer(1, 10))

                hypotheses = corr.get("attack_hypotheses", [])
                if hypotheses:
                    story.append(Paragraph("<b>Generated Attack Scenario Hypotheses:</b>", styles['SubsectionHeader']))
                    for idx, h in enumerate(hypotheses, 1):
                        prob = h.get("probability", "Medium")
                        prob_color = "#c53030" if prob in ["Critical", "High"] else "#dd6b20" if prob == "Medium" else "#276749"
                        scenario_header = f"<b>Hypothesis {idx}: {h.get('scenario')}</b> (Probability: <font color=\"{prob_color}\"><b>{prob}</b></font>)"
                        story.append(Paragraph(scenario_header, styles['ForensicBodyText']))
                        story.append(Paragraph(h.get("description", ""), styles['ForensicBodyText']))
                        story.append(Spacer(1, 6))
                    story.append(Spacer(1, 10))

                timeline = corr.get("timeline", [])
                if timeline:
                    story.append(Paragraph("<b>Unified Chronological Incident Timeline:</b>", styles['SubsectionHeader']))
                    timeline_data = [["Timestamp", "Event Name", "Actor", "Details"]]
                    for item in timeline:
                        ts_str = item.get("timestamp", "")
                        if ts_str:
                            try:
                                if "T" in ts_str:
                                    dt = datetime.fromisoformat(ts_str.split(".")[0])
                                    ts_str = dt.strftime('%Y-%m-%d\n%H:%M:%S')
                            except Exception:
                                pass
                        
                        det_str = str(item.get("details", ""))
                        if len(det_str) > 75:
                            det_str = det_str[:75] + "..."
                            
                        timeline_data.append([
                            ts_str,
                            item.get("event", ""),
                            item.get("investigator_id", ""),
                            det_str
                        ])
                    
                    timeline_table = Table(timeline_data, colWidths=[1.1*inch, 1.6*inch, 1*inch, 2.8*inch])
                    style_cmds = [
                        ('BACKGROUND', (0, 0), (-1, 0), ForensicColors.LIGHT_BG),
                        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                        ('FONTSIZE', (0, 0), (-1, -1), 8),
                        ('GRID', (0, 0), (-1, -1), 0.5, ForensicColors.BORDER),
                        ('ALIGN', (0, 0), (2, -1), 'CENTER'),
                        ('VALIGN', (0, 0), (-1, -1), 'TOP'),
                        ('PADDING', (0, 0), (-1, -1), 4),
                    ]
                    for i in range(1, len(timeline_data)):
                        if i % 2 == 0:
                            style_cmds.append(('BACKGROUND', (0, i), (-1, i), colors.Color(0.97, 0.97, 0.99)))
                    timeline_table.setStyle(TableStyle(style_cmds))
                    story.append(timeline_table)
                    story.append(Spacer(1, 10))

            # ==================== CERTIFICATION SECTION ====================
            story.append(Spacer(1, 20))
            story.append(PDFReportGenerator._create_section_header_table("CERTIFICATION", "✅"))
            story.append(Spacer(1, 10))
            
            cert_text = (
                'This report certifies that the digital evidence described herein has been acquired, '
                'processed, and documented in accordance with forensic best practices. The chain of custody '
                'has been maintained throughout the acquisition process, and all digital fingerprints have '
                'been recorded for integrity verification purposes.'
            )
            story.append(Paragraph(cert_text, styles['ForensicBodyText']))
            
            story.append(Spacer(1, 20))
            
            sig_data = [
                ["VERIFICATION", "", ""],
                ["Examiner Signature:", "________________________", "Date: ____________"],
                ["Supervisor Signature:", "________________________", "Date: ____________"],
                ["Report Seal:", "________________________", ""],
            ]
            
            sig_table = Table(sig_data, colWidths=[1.8*inch, 2.5*inch, 2.2*inch])
            sig_table.setStyle(TableStyle([
                ('SPAN', (0, 0), (-1, 0)),
                ('BACKGROUND', (0, 0), (-1, 0), ForensicColors.LIGHT_BG),
                ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                ('FONTSIZE', (0, 0), (-1, 0), 10),
                ('ALIGN', (0, 0), (-1, 0), 'CENTER'),
                ('FONTNAME', (0, 1), (0, -1), 'Helvetica-Bold'),
                ('FONTSIZE', (0, 1), (-1, -1), 9),
                ('TEXTCOLOR', (0, 1), (-1, -1), ForensicColors.MUTED),
                ('PADDING', (0, 0), (-1, -1), 10),
                ('TOPPADDING', (0, 1), (-1, -1), 15),
                ('BOTTOMPADDING', (0, 1), (-1, -1), 15),
                ('BOX', (0, 0), (-1, -1), 1, ForensicColors.BORDER),
            ]))
            story.append(sig_table)
            
            # ==================== DISCLAIMER ====================
            story.append(Spacer(1, 25))
            disclaimer_text = (
                '<font size="8" color="#718096"><b>DISCLAIMER:</b> This forensic evidence report is generated '
                'automatically by the Forensic Evidence Acquisition System (FEAS). The information contained herein '
                'is intended for law enforcement and authorized personnel only. Unauthorized distribution, modification, '
                'or use of this report may be subject to legal penalties. The integrity of this evidence should be '
                'verified using the SHA-256 hash provided above before use in any legal proceedings.</font>'
            )
            story.append(Paragraph(disclaimer_text, styles['Normal']))
            
            # Build PDF
            doc.build(story, 
                     onFirstPage=PDFReportGenerator.create_header_footer,
                     onLaterPages=PDFReportGenerator.create_header_footer)
            
            logger.info(f"Custom PDF report generated: {temp_path}")
            return temp_path
            
        except Exception as e:
            logger.error(f"Custom PDF generation failed: {str(e)}")
            raise

    @staticmethod
    def create_verification_report(job_id: str, 

                                  verification_result: Dict[str, Any]) -> str:
        """Create professional verification report"""
        try:
            temp_file = tempfile.NamedTemporaryFile(delete=False, suffix='_verification.pdf')
            temp_path = temp_file.name
            temp_file.close()
            
            doc = SimpleDocTemplate(
                temp_path,
                pagesize=letter,
                rightMargin=inch,
                leftMargin=inch,
                topMargin=1.3*inch,
                bottomMargin=0.8*inch
            )
            
            styles = PDFReportGenerator._create_styles()
            story = []
            
            # Title
            story.append(Spacer(1, 40))
            story.append(Paragraph("HASH VERIFICATION REPORT", styles['ReportTitle']))
            story.append(Paragraph("Evidence Integrity Check", styles['ReportSubtitle']))
            
            # Status indicator
            is_match = verification_result['matches']
            status_color = ForensicColors.SUCCESS if is_match else ForensicColors.ERROR
            status_text = "✓ INTEGRITY VERIFIED" if is_match else "✗ INTEGRITY CHECK FAILED"
            status_bg = colors.HexColor('#c6f6d5') if is_match else colors.HexColor('#fed7d7')
            
            status_data = [[status_text]]
            status_table = Table(status_data, colWidths=[6.5*inch])
            status_table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, -1), status_bg),
                ('TEXTCOLOR', (0, 0), (-1, -1), status_color),
                ('FONTNAME', (0, 0), (-1, -1), 'Helvetica-Bold'),
                ('FONTSIZE', (0, 0), (-1, -1), 16),
                ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                ('PADDING', (0, 0), (-1, -1), 20),
                ('BOX', (0, 0), (-1, -1), 2, status_color),
            ]))
            story.append(status_table)
            
            story.append(Spacer(1, 25))
            
            # Verification details
            story.append(PDFReportGenerator._create_section_header_table("VERIFICATION DETAILS", "🔍"))
            story.append(Spacer(1, 10))
            
            verification_data = [
                ["Job ID:", job_id],
                ["Verification Date:", 
                 datetime.fromisoformat(
                     verification_result['verification_timestamp'].replace('Z', '+00:00')
                 ).strftime('%Y-%m-%d %H:%M:%S UTC')],
            ]
            story.append(PDFReportGenerator._create_info_table(verification_data))
            
            story.append(Spacer(1, 20))
            
            # Hash comparison
            story.append(PDFReportGenerator._create_section_header_table("HASH COMPARISON", "🔐"))
            story.append(Spacer(1, 10))
            
            hash_data = [
                ["Original Hash:", verification_result['original_hash']],
                ["Current Hash:", verification_result['current_hash']],
                ["Match Status:", "IDENTICAL" if is_match else "MISMATCH DETECTED"],
            ]
            
            hash_table = Table(hash_data, colWidths=[2*inch, 4.5*inch])
            hash_table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (0, -1), ForensicColors.LIGHT_BG),
                ('TEXTCOLOR', (0, 0), (0, -1), ForensicColors.SECONDARY),
                ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
                ('FONTNAME', (1, 0), (1, 1), 'Courier'),
                ('FONTSIZE', (1, 0), (1, 1), 8),
                ('FONTSIZE', (0, 0), (0, -1), 10),
                ('PADDING', (0, 0), (-1, -1), 8),
                ('GRID', (0, 0), (-1, -1), 0.5, ForensicColors.BORDER),
                ('BOX', (0, 0), (-1, -1), 1, ForensicColors.SECONDARY),
                ('BACKGROUND', (1, 2), (1, 2), status_bg),
                ('TEXTCOLOR', (1, 2), (1, 2), status_color),
                ('FONTNAME', (1, 2), (1, 2), 'Helvetica-Bold'),
            ]))
            story.append(hash_table)
            
            story.append(Spacer(1, 20))
            
            # Result interpretation
            story.append(PDFReportGenerator._create_section_header_table("INTERPRETATION", "📋"))
            story.append(Spacer(1, 10))
            
            if is_match:
                result_text = (
                    '<font color="#276749"><b>VERIFIED:</b></font> The current hash of the evidence file '
                    'matches the original hash recorded during acquisition. This confirms that the evidence '
                    'has not been altered, modified, or tampered with since it was collected. The integrity '
                    'of this evidence is intact and it may be considered authentic for forensic purposes.'
                )
            else:
                result_text = (
                    '<font color="#c53030"><b>WARNING:</b></font> The current hash of the evidence file '
                    'DOES NOT match the original hash recorded during acquisition. This indicates that the '
                    'evidence may have been altered, corrupted, or tampered with since collection. This '
                    'evidence should be treated with caution and may not be suitable for legal proceedings '
                    'without further investigation.'
                )
            
            story.append(Paragraph(result_text, styles['ForensicBodyText']))
            
            # Build PDF
            doc.build(story, onFirstPage=PDFReportGenerator.create_header_footer,
                     onLaterPages=PDFReportGenerator.create_header_footer)
            
            return temp_path
            
        except Exception as e:
            logger.error(f"Verification report generation failed: {str(e)}")
            raise
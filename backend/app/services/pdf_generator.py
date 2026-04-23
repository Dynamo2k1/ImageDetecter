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

            # ==================== NETWORK SCAN RESULTS ====================
            if job_details.scan_results:
                story.append(Spacer(1, 25))
                story.append(PDFReportGenerator._create_section_header_table("NETWORK SCAN RESULTS", "🌐"))
                story.append(Spacer(1, 10))

                scan_rows = [["Scan ID", "Target", "Status", "Open Ports"]]
                for scan in job_details.scan_results:
                    open_ports = scan.get("ports", [])
                    ports_brief = ", ".join(str(p.get("port")) for p in open_ports[:6]) or "None"
                    if len(open_ports) > 6:
                        ports_brief += " ..."
                    scan_rows.append([
                        scan.get("scan_id", "N/A"),
                        scan.get("target", "N/A"),
                        scan.get("status", "N/A"),
                        ports_brief
                    ])
                story.append(PDFReportGenerator._create_info_table(scan_rows, col_widths=[1.6*inch, 2*inch, 1*inch, 1.9*inch]))

            # ==================== VULNERABILITY FINDINGS ====================
            if job_details.vulnerabilities:
                story.append(Spacer(1, 25))
                story.append(PDFReportGenerator._create_section_header_table("VULNERABILITY FINDINGS", "🛡️"))
                story.append(Spacer(1, 10))

                vuln_rows = [["CVE", "Service", "Version", "Risk", "Description"]]
                for vuln in job_details.vulnerabilities[:25]:
                    desc = vuln.get("description", "") or ""
                    if len(desc) > 55:
                        desc = desc[:55] + "..."
                    vuln_rows.append([
                        vuln.get("cve_id", "N/A"),
                        vuln.get("service", "N/A"),
                        vuln.get("version", "N/A"),
                        vuln.get("risk_level", "Low"),
                        desc
                    ])

                vuln_table = Table(vuln_rows, colWidths=[1.3*inch, 1.1*inch, 1.2*inch, 0.7*inch, 2.2*inch])
                style_commands = [
                    ('BACKGROUND', (0, 0), (-1, 0), ForensicColors.SECONDARY),
                    ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
                    ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                    ('FONTSIZE', (0, 0), (-1, 0), 9),
                    ('FONTNAME', (0, 1), (-1, -1), 'Helvetica'),
                    ('FONTSIZE', (0, 1), (-1, -1), 8),
                    ('GRID', (0, 0), (-1, -1), 0.5, ForensicColors.BORDER),
                    ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
                    ('PADDING', (0, 0), (-1, -1), 5),
                ]
                for i in range(1, len(vuln_rows)):
                    risk = (vuln_rows[i][3] or "").lower()
                    if risk == "high":
                        style_commands.append(('BACKGROUND', (3, i), (3, i), colors.HexColor('#fed7d7')))
                    elif risk == "medium":
                        style_commands.append(('BACKGROUND', (3, i), (3, i), colors.HexColor('#feebc8')))
                    else:
                        style_commands.append(('BACKGROUND', (3, i), (3, i), colors.HexColor('#c6f6d5')))

                vuln_table.setStyle(TableStyle(style_commands))
                story.append(vuln_table)

            # ==================== RISK ASSESSMENT ====================
            if job_details.risk_assessment:
                story.append(Spacer(1, 25))
                story.append(PDFReportGenerator._create_section_header_table("RISK ASSESSMENT", "⚠️"))
                story.append(Spacer(1, 10))

                counts = job_details.risk_assessment.get("counts", {})
                risk_data = [
                    ["Overall Risk:", job_details.risk_assessment.get("overall_risk", "Low")],
                    ["High Findings:", str(counts.get("High", 0))],
                    ["Medium Findings:", str(counts.get("Medium", 0))],
                    ["Low Findings:", str(counts.get("Low", 0))],
                ]
                story.append(PDFReportGenerator._create_info_table(risk_data))
            
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

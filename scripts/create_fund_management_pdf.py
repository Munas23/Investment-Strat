"""
PDF Generator for Fund Management Analysis Report
================================================

Converts the comprehensive fund management analysis to a well-formatted PDF document.
"""

from reportlab.lib.pagesizes import A4, letter
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, PageBreak
from reportlab.lib.enums import TA_LEFT, TA_CENTER, TA_JUSTIFY
from datetime import datetime
import os

def create_fund_management_pdf():
    """Create comprehensive fund management PDF report"""
    
    # Find the most recent analysis file
    analysis_files = [f for f in os.listdir('.') if f.startswith('fund_management_comprehensive_analysis_') and f.endswith('.txt')]
    if not analysis_files:
        print("No analysis file found!")
        return None
    
    latest_file = max(analysis_files)
    print(f"Converting {latest_file} to PDF...")
    
    # Read the analysis content
    with open(latest_file, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Create PDF filename
    pdf_filename = latest_file.replace('.txt', '.pdf')
    
    # Create PDF document
    doc = SimpleDocTemplate(pdf_filename, pagesize=letter, topMargin=1*inch, bottomMargin=1*inch)
    
    # Get styles
    styles = getSampleStyleSheet()
    
    # Custom styles
    title_style = ParagraphStyle(
        'CustomTitle',
        parent=styles['Title'],
        fontSize=18,
        textColor='black',
        alignment=TA_CENTER,
        spaceAfter=30
    )
    
    heading_style = ParagraphStyle(
        'CustomHeading',
        parent=styles['Heading1'], 
        fontSize=14,
        textColor='black',
        alignment=TA_LEFT,
        spaceAfter=12,
        spaceBefore=20
    )
    
    subheading_style = ParagraphStyle(
        'CustomSubHeading',
        parent=styles['Heading2'],
        fontSize=12,
        textColor='black',
        alignment=TA_LEFT,
        spaceAfter=8,
        spaceBefore=15
    )
    
    body_style = ParagraphStyle(
        'CustomBody',
        parent=styles['Normal'],
        fontSize=10,
        textColor='black',
        alignment=TA_JUSTIFY,
        spaceAfter=6,
        leftIndent=0,
        rightIndent=0
    )
    
    # Process content
    story = []
    lines = content.split('\n')
    
    for line in lines:
        line = line.strip()
        
        if not line:
            story.append(Spacer(1, 6))
            continue
            
        # Title - main heading
        if line.startswith('COMPREHENSIVE FUND MANAGEMENT ANALYSIS REPORT'):
            story.append(Paragraph(line, title_style))
            story.append(Spacer(1, 20))
            
        # Main sections
        elif any(line.startswith(x) for x in [
            'EXECUTIVE SUMMARY',
            'FUND MANAGEMENT STRUCTURES ANALYSIS', 
            'DOCUMENTATION REQUIREMENTS ANALYSIS',
            'OPERATIONAL FRAMEWORK ANALYSIS',
            'TAX IMPLICATIONS ANALYSIS',
            'SETUP RECOMMENDATIONS',
            'CONCLUSION AND NEXT STEPS'
        ]):
            story.append(PageBreak())
            story.append(Paragraph(line, heading_style))
            
        # Sub-sections with numbers or dashes
        elif any(line.startswith(x) for x in [
            '1. ', '2. ', '3. ', '4. ', '5. ', '6. ', '7. ', '8. ', '9. ',
            'PHASE 1:', 'PHASE 2:', 'PHASE 3:',
            'KEY FINDINGS:', 'IMMEDIATE ACTIONS REQUIRED:', 'STRATEGIC CONSIDERATIONS:',
            'RISK FACTORS:'
        ]):
            story.append(Paragraph(line, subheading_style))
            
        # Underlined sections (===== or -----)
        elif line.startswith('=') or line.startswith('-'):
            continue  # Skip decorative lines
            
        # Regular content
        else:
            # Handle bullet points and special formatting
            if line.startswith('✓') or line.startswith('✗') or line.startswith('-'):
                # Convert checkmarks to text for PDF compatibility
                line = line.replace('✓', '• ').replace('✗', '• ').replace('- ', '• ')
                
            story.append(Paragraph(line, body_style))
    
    # Build PDF
    try:
        doc.build(story)
        print(f"PDF created successfully: {pdf_filename}")
        return pdf_filename
    except Exception as e:
        print(f"Error creating PDF: {e}")
        return None

def main():
    """Main execution"""
    print("=" * 60)
    print("FUND MANAGEMENT ANALYSIS - PDF CONVERTER")
    print("=" * 60)
    
    try:
        pdf_file = create_fund_management_pdf()
        if pdf_file:
            print(f"\nSUCCESS!")
            print(f"PDF Report: {pdf_file}")
            print("The comprehensive fund management analysis is now available as a formatted PDF.")
        else:
            print("Failed to create PDF. Check error messages above.")
    except ImportError:
        print("ReportLab library not available. Creating simplified PDF...")
        # Fallback: create a simple text file with better formatting
        create_formatted_text_report()

def create_formatted_text_report():
    """Create formatted text report as fallback"""
    analysis_files = [f for f in os.listdir('.') if f.startswith('fund_management_comprehensive_analysis_') and f.endswith('.txt')]
    if not analysis_files:
        return
    
    latest_file = max(analysis_files)
    output_file = latest_file.replace('.txt', '_formatted.txt')
    
    with open(latest_file, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Create formatted version
    formatted_content = f"""
{'=' * 80}
COMPREHENSIVE FUND MANAGEMENT ANALYSIS REPORT
{'=' * 80}

Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
Subject: Fund Management Structure and Operations for 5-Level Conviction Strategy

{content}

{'=' * 80}
END OF REPORT
{'=' * 80}

This comprehensive analysis provides the framework for establishing a professional
fund management business implementing our proven 5-Level Conviction trading strategy.

Key recommendations:
1. Unit trust structure for tax efficiency
2. Professional legal and compliance advice essential
3. 18-24 month setup timeline with significant capital requirements
4. Minimum $50M scale for economic viability
5. Comprehensive operational framework required

Next steps: Engage professional advisers for implementation planning.
"""
    
    with open(output_file, 'w', encoding='utf-8') as f:
        f.write(formatted_content)
    
    print(f"Formatted report created: {output_file}")
    return output_file

if __name__ == "__main__":
    main()
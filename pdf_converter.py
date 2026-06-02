"""
PDF Converter for Fund Management Analysis
=========================================

Converts the fund management analysis to PDF using matplotlib for text rendering.
"""

import matplotlib.pyplot as plt
from matplotlib.backends.backend_pdf import PdfPages
import matplotlib.patches as patches
from datetime import datetime
import textwrap
import os

def create_pdf_report():
    """Create PDF version of the fund management analysis"""
    
    # Find the latest report file
    report_files = [f for f in os.listdir('.') if f.startswith('Fund_Management_Analysis_Final_Report_') and f.endswith('.txt')]
    if not report_files:
        print("No report file found!")
        return None
    
    latest_file = max(report_files)
    print(f"Converting {latest_file} to PDF...")
    
    # Read the report content
    with open(latest_file, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Create PDF filename
    pdf_filename = latest_file.replace('.txt', '.pdf')
    
    # Create PDF
    with PdfPages(pdf_filename) as pdf:
        # Split content into sections
        sections = content.split('=' * 80)
        
        for i, section in enumerate(sections):
            if not section.strip():
                continue
                
            # Create a new figure for each section
            fig, ax = plt.subplots(figsize=(8.5, 11))  # Letter size
            ax.set_xlim(0, 1)
            ax.set_ylim(0, 1)
            ax.axis('off')
            
            # Process section content
            lines = section.strip().split('\n')
            y_position = 0.95
            
            for line in lines:
                line = line.strip()
                if not line:
                    y_position -= 0.02
                    continue
                
                # Determine text style based on content
                if any(line.startswith(x) for x in ['COMPREHENSIVE FUND', 'EXECUTIVE SUMMARY', 'FUND STRUCTURE', 'DOCUMENTATION', 'OPERATIONAL', 'TAX IMPLICATIONS', 'SETUP RECOMMENDATIONS', 'RISK ASSESSMENT', 'SUCCESS FACTORS', 'CONCLUSION']):
                    # Main headings
                    wrapped_lines = textwrap.wrap(line, width=70)
                    for wrapped_line in wrapped_lines:
                        ax.text(0.5, y_position, wrapped_line, fontsize=14, fontweight='bold', 
                               ha='center', va='top', transform=ax.transAxes)
                        y_position -= 0.04
                    y_position -= 0.02
                    
                elif line.startswith(('1. ', '2. ', '3. ', '4. ', '5. ', '6. ', '7. ', '8. ')):
                    # Numbered sections
                    wrapped_lines = textwrap.wrap(line, width=80)
                    for wrapped_line in wrapped_lines:
                        ax.text(0.05, y_position, wrapped_line, fontsize=12, fontweight='bold',
                               ha='left', va='top', transform=ax.transAxes)
                        y_position -= 0.03
                    y_position -= 0.01
                    
                elif line.startswith('•'):
                    # Bullet points
                    wrapped_lines = textwrap.wrap(line, width=75)
                    for wrapped_line in wrapped_lines:
                        ax.text(0.1, y_position, wrapped_line, fontsize=10,
                               ha='left', va='top', transform=ax.transAxes)
                        y_position -= 0.025
                        
                else:
                    # Regular text
                    wrapped_lines = textwrap.wrap(line, width=80)
                    for wrapped_line in wrapped_lines:
                        ax.text(0.05, y_position, wrapped_line, fontsize=10,
                               ha='left', va='top', transform=ax.transAxes)
                        y_position -= 0.025
                
                # Check if we need a new page
                if y_position < 0.05:
                    break
            
            # Add page number
            ax.text(0.95, 0.02, f"Page {i+1}", fontsize=8, ha='right', va='bottom',
                   transform=ax.transAxes)
            
            # Save the page
            pdf.savefig(fig, bbox_inches='tight')
            plt.close(fig)
    
    print(f"PDF created successfully: {pdf_filename}")
    return pdf_filename

def create_simple_pdf():
    """Create a simpler PDF using basic text formatting"""
    
    # Find the latest report file
    report_files = [f for f in os.listdir('.') if f.startswith('Fund_Management_Analysis_Final_Report_') and f.endswith('.txt')]
    if not report_files:
        return None
    
    latest_file = max(report_files)
    
    # Read content
    with open(latest_file, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Create a simple HTML version for PDF conversion
    html_content = f"""
<!DOCTYPE html>
<html>
<head>
    <title>Fund Management Analysis Report</title>
    <style>
        body {{ font-family: Arial, sans-serif; margin: 40px; line-height: 1.4; }}
        h1 {{ color: #2c3e50; text-align: center; border-bottom: 3px solid #3498db; padding-bottom: 10px; }}
        h2 {{ color: #34495e; border-bottom: 2px solid #bdc3c7; padding-bottom: 5px; margin-top: 30px; }}
        h3 {{ color: #2c3e50; margin-top: 20px; }}
        .section {{ margin-bottom: 30px; }}
        .highlight {{ background-color: #f8f9fa; padding: 15px; border-left: 4px solid #3498db; }}
        ul {{ margin-left: 20px; }}
        li {{ margin-bottom: 5px; }}
        .page-break {{ page-break-before: always; }}
    </style>
</head>
<body>
"""
    
    # Process content for HTML
    lines = content.split('\n')
    in_section = False
    
    for line in lines:
        line = line.strip()
        
        if not line:
            html_content += '<br>\n'
            continue
            
        if line.startswith('=' * 50):
            continue
            
        # Main headings
        if any(line.startswith(x) for x in [
            'COMPREHENSIVE FUND MANAGEMENT ANALYSIS',
            'EXECUTIVE SUMMARY',
            'FUND STRUCTURE ANALYSIS', 
            'DOCUMENTATION REQUIREMENTS',
            'OPERATIONAL FRAMEWORK',
            'TAX IMPLICATIONS',
            'SETUP RECOMMENDATIONS',
            'RISK ASSESSMENT',
            'SUCCESS FACTORS',
            'CONCLUSION'
        ]):
            if in_section:
                html_content += '</div>\n'
            html_content += f'<div class="page-break section"><h1>{line}</h1>\n'
            in_section = True
            
        # Sub-headings
        elif any(line.startswith(x) for x in ['1. ', '2. ', '3. ', '4. ', '5. ', '6. ', '7. ', '8. ']):
            html_content += f'<h2>{line}</h2>\n'
            
        # Bullet points
        elif line.startswith('•'):
            html_content += f'<li>{line[1:].strip()}</li>\n'
            
        # Highlighted content
        elif any(x in line.upper() for x in ['RECOMMENDATION:', 'KEY FINDINGS:', 'CRITICAL:', 'WARNING:']):
            html_content += f'<div class="highlight"><strong>{line}</strong></div>\n'
            
        else:
            html_content += f'<p>{line}</p>\n'
    
    if in_section:
        html_content += '</div>\n'
        
    html_content += """
</body>
</html>
"""
    
    # Save HTML file
    html_filename = latest_file.replace('.txt', '.html')
    with open(html_filename, 'w', encoding='utf-8') as f:
        f.write(html_content)
    
    print(f"HTML version created: {html_filename}")
    print("You can open this HTML file in your browser and print to PDF.")
    return html_filename

def main():
    """Create PDF version of fund management analysis"""
    
    print("=" * 60)
    print("FUND MANAGEMENT ANALYSIS - PDF CONVERTER")
    print("=" * 60)
    
    try:
        # Try matplotlib PDF creation first
        pdf_file = create_pdf_report()
        if pdf_file:
            print(f"\nSUCCESS! PDF created: {pdf_file}")
            return pdf_file
    except ImportError:
        print("Matplotlib not available. Creating HTML version for PDF conversion...")
    except Exception as e:
        print(f"PDF creation failed: {e}")
        print("Creating HTML version as fallback...")
    
    # Fallback to HTML version
    html_file = create_simple_pdf()
    if html_file:
        print(f"\nHTML version created: {html_file}")
        print("\nTo convert to PDF:")
        print("1. Open the HTML file in your web browser")
        print("2. Print the page (Ctrl+P)")
        print("3. Select 'Save as PDF' as the destination")
        print("4. Adjust margins and settings as needed")
        return html_file
    
    return None

if __name__ == "__main__":
    main()
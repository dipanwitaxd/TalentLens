# src/pdf_processor.py
# PDF processor with intelligent bullet detection

import PyPDF2
import streamlit as st
from io import BytesIO
import re

def extract_text_from_pdf(uploaded_file) -> str:
    """Extract text from uploaded PDF file"""
    try:
        pdf_reader = PyPDF2.PdfReader(BytesIO(uploaded_file.read()))
        text = ""
        
        for page in pdf_reader.pages:
            text += page.extract_text() + "\n"
        
        return text.strip()
    
    except Exception as e:
        st.error(f"Error reading PDF: {e}")
        return ""

def add_smart_bullets(text: str) -> str:
    """
    Intelligently add bullet points to lines that look like resume bullets
    but lost their bullet characters during PDF extraction
    """
    
    lines = text.split('\n')
    processed_lines = []
    
    # Track if we're in an experience/projects section
    in_bullet_section = False
    last_was_role = False
    
    for i, line in enumerate(lines):
        stripped = line.strip()
        
        # Skip empty lines
        if not stripped:
            processed_lines.append(line)
            last_was_role = False
            continue
        
        # Detect section headers
        if is_section_header(stripped):
            section_lower = stripped.lower()
            in_bullet_section = any(keyword in section_lower for keyword in 
                                   ['experience', 'work', 'projects', 'employment', 'professional'])
            processed_lines.append(line)
            last_was_role = False
            continue
        
        # Check if this line already has a bullet
        if has_bullet(stripped):
            processed_lines.append(line)
            last_was_role = False
            continue
        
        # Check if this is a job title/company line
        if has_job_indicators(stripped):
            processed_lines.append(line)
            last_was_role = True
            continue
        
        # If we're in a bullet section and line should be a bullet, add one
        if in_bullet_section and (last_was_role or should_be_bullet(stripped)):
            processed_lines.append(f"• {stripped}")
        else:
            processed_lines.append(line)
            last_was_role = False
    
    return '\n'.join(processed_lines)

def is_section_header(line: str) -> bool:
    """Check if line is a section header"""
    
    # Skip very long lines
    if len(line) > 60:
        return False
    
    # All caps or mostly caps
    if line.isupper():
        return True
    
    # Known section headers
    headers = [
        'EXPERIENCE', 'WORK EXPERIENCE', 'PROFESSIONAL EXPERIENCE',
        'EDUCATION', 'SKILLS', 'TECHNICAL SKILLS', 'PROJECTS',
        'CERTIFICATIONS', 'SUMMARY', 'PROFILE', 'CONTACT',
        'WORK HISTORY', 'EMPLOYMENT HISTORY', 'KEY PROJECTS'
    ]
    
    return line.upper().strip() in headers

def has_bullet(line: str) -> bool:
    """Check if line already has a bullet character"""
    
    bullet_chars = ['•', '-', '*', '→', '▪', '◦', '⦿', '–', '—']
    
    # Check first few characters
    first_chars = line[:5].strip()
    
    for char in bullet_chars:
        if first_chars.startswith(char):
            return True
    
    # Check for numbered bullets
    if re.match(r'^\d+[\.\)]\s', line.strip()):
        return True
    
    return False

def has_job_indicators(line: str) -> bool:
    """Check if line looks like a job title/company line"""
    
    # Check for common separators between role and company
    if any(sep in line for sep in ['|', '–', '—', ' - ', ' at ']):
        return True
    
    # Check for date patterns (roles usually have dates on same or next line)
    date_patterns = [
        r'\d{4}\s*-\s*\d{4}',
        r'\d{4}\s*-\s*Present',
        r'\d{4}\s*-\s*Current',
        r'(Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)\s+\d{4}',
        r'\(\d+\s+(YEAR|MONTH)',
    ]
    
    for pattern in date_patterns:
        if re.search(pattern, line, re.IGNORECASE):
            return True
    
    return False

def should_be_bullet(line: str) -> bool:
    """
    Determine if a line should be a bullet point based on content
    """
    
    # Too short - probably not a bullet
    if len(line) < 15:
        return False
    
    # Too long - probably not a single bullet
    if len(line) > 400:
        return False
    
    # Check for action verbs at the start (past tense or present)
    action_verbs = [
        'achieved', 'architected', 'automated', 'built', 'collaborated', 
        'completed', 'conducted', 'coordinated', 'created', 'delivered',
        'deployed', 'designed', 'developed', 'engineered', 'enhanced',
        'established', 'executed', 'implemented', 'improved', 'increased',
        'integrated', 'launched', 'led', 'maintained', 'managed', 
        'optimized', 'orchestrated', 'performed', 'reduced', 'researched',
        'resolved', 'scaled', 'spearheaded', 'streamlined', 'wrote',
        # Present tense for current roles
        'achieve', 'architect', 'automate', 'build', 'collaborate',
        'complete', 'conduct', 'coordinate', 'create', 'deliver',
        'deploy', 'design', 'develop', 'engineer', 'enhance',
        'establish', 'execute', 'implement', 'improve', 'increase',
        'integrate', 'launch', 'lead', 'maintain', 'manage',
        'optimize', 'orchestrate', 'perform', 'reduce', 'research',
        'resolve', 'scale', 'spearhead', 'streamline', 'write'
    ]
    
    first_word = line.split()[0].lower().strip('.,;:')
    
    if first_word in action_verbs:
        return True
    
    # Check for past tense verbs (ending in -ed)
    if first_word.endswith('ed') and len(first_word) > 4:
        return True
    
    # Check for metrics/numbers (very common in bullets)
    metric_patterns = [
        r'\d+%',                    # Percentages (40%)
        r'\d+[KMB]\+?',            # Large numbers (10K+, 5M)
        r'\$\d+',                   # Money ($5K)
        r'\d+x',                    # Multipliers (2x faster)
        r'\d+\s*(weeks|months|days|hours)',  # Time (1.5 weeks)
        r'\d+-\d+',                 # Ranges (1-5 users)
    ]
    
    for pattern in metric_patterns:
        if re.search(pattern, line, re.IGNORECASE):
            return True
    
    # Check for technical keywords (common in engineering resumes)
    tech_keywords = [
        'api', 'database', 'framework', 'platform', 'system', 'application',
        'dashboard', 'module', 'component', 'service', 'pipeline', 'workflow'
    ]
    
    line_lower = line.lower()
    if any(keyword in line_lower for keyword in tech_keywords):
        # If it has tech keywords AND is a reasonable length, likely a bullet
        if 20 <= len(line) <= 250:
            return True
    
    return False

def process_pdf_upload():
    """Handle PDF upload in Streamlit with smart bullet detection"""
    uploaded_file = st.file_uploader(
        "Upload Resume PDF",
        type=['pdf'],
        help="Upload your resume as a PDF file",
        key="pdf_uploader"
    )

    if uploaded_file:
        # Show file info
        file_info = f"{uploaded_file.name} ({uploaded_file.size/1024:.1f} KB)"
        st.info(f"File uploaded: {file_info}")

        with st.spinner("Extracting text from PDF..."):
            text = extract_text_from_pdf(uploaded_file)

        if text:
            # Apply smart bullet detection
            processed_text = add_smart_bullets(text)
            
            # Count bullets added
            bullet_count = processed_text.count('•')
            
            st.success(f"PDF processed successfully!")
            
            # Show preview with expander
            with st.expander("Preview extracted text (first 500 characters)"):
                st.text(processed_text[:500] + "..." if len(processed_text) > 500 else processed_text)
            
            if bullet_count > 0:
                st.info(f"Detected and added {bullet_count} bullet points")
            else:
                st.warning("No bullet points detected. Make sure your resume has experience descriptions.")
            
            return processed_text
        else:
            st.error("Could not extract text from PDF")

    return None


# Test function
def test_smart_bullets():
    """Test the smart bullet detection"""
    
    test_text = """DIPANWITA MANDAL
Software Engineer

WORK EXPERIENCE

Software Engineer – Frontend
Accacia
FEB 2023 - PRESENT

Delivered 4 dashboards in 1.5 weeks (MVP) and 3 emission-tracking systems in 72 hours
Architected EC BOQ module from 0-1, featuring dynamic editable tables
Optimized API management with Tanstack Query reducing API-related code complexity by 40%
Engineered dynamic tables using Material React Table accelerated feature implementation by 60%

Senior Software Development Engineer
KAFOA
Jun 2022 - Dec 2022

Integrated Mixpanel for user behavior tracking enabling data-driven decisions
Built the foundational CRM platform developing 15+ reusable components
Optimized frontend performance cutting page load times by 15%"""
    
    processed = add_smart_bullets(test_text)
    
    print("=== ORIGINAL ===")
    print(test_text)
    print("\n=== PROCESSED ===")
    print(processed)
    print(f"\n=== STATS ===")
    print(f"Bullets added: {processed.count('•')}")


if __name__ == "__main__":
    test_smart_bullets()
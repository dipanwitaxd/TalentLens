# src/text_processor.py (FIXED VERSION)
# Phase 1: Inputs & chunking with better bullet detection

import re
from typing import List, Optional
from dataclasses import dataclass
from enum import Enum

class SectionType(Enum):
    HEADER = "header"
    CONTACT = "contact"
    SUMMARY = "summary"
    EXPERIENCE = "experience"
    EDUCATION = "education"
    SKILLS = "skills"
    PROJECTS = "projects"
    CERTIFICATIONS = "certifications"
    UNKNOWN = "unknown"

@dataclass
class ProcessedLine:
    line_number: int
    text: str
    section: SectionType
    is_bullet: bool
    bullet_level: int = 0
    metadata: dict = None

class UniversalTextProcessor:
    """IMPROVED: Better bullet point and section detection"""
    
    def __init__(self):
        self.setup_patterns()
    
    def setup_patterns(self):
        """Setup improved regex patterns for better detection"""
        
        # IMPROVED: More comprehensive bullet patterns
        self.bullet_patterns = [
            r'^\s*•\s+(.+)',           # Bullet point •
            r'^\s*-\s+(.+)',           # Dash -
            r'^\s*\*\s+(.+)',          # Asterisk *
            r'^\s*→\s+(.+)',           # Arrow →
            r'^\s*▪\s+(.+)',           # Square bullet ▪
            r'^\s*◦\s+(.+)',           # Circle bullet ◦
            r'^\s*\d+\.\s+(.+)',       # Numbered 1. 2. 3.
            r'^\s*[a-zA-Z]\.\s+(.+)',  # Lettered a. b. c.
        ]
        
        # IMPROVED: Better section detection
        self.section_patterns = {
            SectionType.EXPERIENCE: [
                r'(?i)^(work\s+)?experience',
                r'(?i)^professional\s+experience',
                r'(?i)^employment(\s+history)?',
                r'(?i)^career\s+history',
                r'(?i)^work\s+history'
            ],
            SectionType.EDUCATION: [
                r'(?i)^education',
                r'(?i)^academic\s+background',
                r'(?i)^degrees?'
            ],
            SectionType.SKILLS: [
                r'(?i)^(technical\s+)?skills',
                r'(?i)^competencies',
                r'(?i)^technologies',
                r'(?i)^tools?\s+(&|and)\s+technologies'
            ],
            SectionType.PROJECTS: [
                r'(?i)^projects?',
                r'(?i)^selected\s+projects',
                r'(?i)^key\s+projects',
                r'(?i)^notable\s+projects'
            ],
            SectionType.SUMMARY: [
                r'(?i)^(professional\s+)?summary',
                r'(?i)^profile',
                r'(?i)^objective',
                r'(?i)^about(\s+me)?'
            ],
            SectionType.CERTIFICATIONS: [
                r'(?i)^certifications?',
                r'(?i)^licenses?',
                r'(?i)^credentials'
            ]
        }
        
        # Contact info patterns
        self.contact_patterns = {
            'email': r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b',
            'phone': r'\b(?:\+?1[-.\s]?)?\(?[0-9]{3}\)?[-.\s]?[0-9]{3}[-.\s]?[0-9]{4}\b',
            'linkedin': r'(?i)linkedin\.com/in/[a-zA-Z0-9-]+',
            'github': r'(?i)github\.com/[a-zA-Z0-9-]+',
            'website': r'(?i)(?:https?://)?(?:www\.)?[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}'
        }
    
    def process_resume(self, resume_text: str) -> List[ProcessedLine]:
        """IMPROVED: Process resume with better parsing"""
        
        # Clean and normalize the text
        cleaned_text = self.clean_text(resume_text)
        lines = cleaned_text.split('\n')
        
        processed_lines = []
        current_section = SectionType.HEADER
        line_number = 1
        
        print(f"DEBUG: Processing {len(lines)} lines")  # Debug output
        
        for raw_line in lines:
            line = raw_line.strip()
            
            # Skip completely empty lines
            if not line:
                continue
            
            # Check if this is a section header
            detected_section = self.detect_section(line)
            if detected_section:
                current_section = detected_section
                print(f"DEBUG: Found section '{detected_section.value}' at line {line_number}")
                
                # Add the section header as a line
                processed_lines.append(ProcessedLine(
                    line_number=line_number,
                    text=line,
                    section=current_section,
                    is_bullet=False,
                    metadata={'is_section_header': True}
                ))
                line_number += 1
                continue
            
            # Check if this is a bullet point
            is_bullet, bullet_text, bullet_level = self.detect_bullet(line)
            
            if is_bullet:
                print(f"DEBUG: Found bullet at line {line_number}: {bullet_text[:50]}...")
            
            # Create processed line
            processed_line = ProcessedLine(
                line_number=line_number,
                text=bullet_text if is_bullet else line,
                section=current_section,
                is_bullet=is_bullet,
                bullet_level=bullet_level,
                metadata=self.extract_metadata(line)
            )
            
            processed_lines.append(processed_line)
            line_number += 1
        
        print(f"DEBUG: Processed {len(processed_lines)} total lines, {sum(1 for line in processed_lines if line.is_bullet)} bullets")
        return processed_lines
    
    def clean_text(self, text: str) -> str:
        """IMPROVED: Clean and normalize text"""
        
        # Remove extra whitespace but preserve line breaks
        text = re.sub(r'\r\n', '\n', text)  # Normalize line endings
        text = re.sub(r'\r', '\n', text)    # Handle old Mac line endings
        
        # Remove excessive blank lines (more than 2 consecutive)
        text = re.sub(r'\n\s*\n\s*\n+', '\n\n', text)
        
        # Fix common PDF extraction issues
        text = re.sub(r'([a-z])([A-Z])', r'\1 \2', text)  # Split concatenated words
        text = re.sub(r'•\s*•', '•', text)  # Remove duplicate bullets
        
        return text
    
    def detect_section(self, line: str) -> Optional[SectionType]:
        """IMPROVED: Detect section headers"""
        
        line_clean = line.strip().upper()
        
        # Skip very short lines or lines with lots of punctuation (likely not headers)
        if len(line_clean) < 3 or len(re.findall(r'[^\w\s]', line_clean)) > len(line_clean) // 2:
            return None
        
        for section_type, patterns in self.section_patterns.items():
            for pattern in patterns:
                if re.match(pattern, line_clean):
                    return section_type
        
        # Special handling for common header variations
        common_headers = {
            'WORK EXPERIENCE': SectionType.EXPERIENCE,
            'PROFESSIONAL EXPERIENCE': SectionType.EXPERIENCE,
            'EMPLOYMENT': SectionType.EXPERIENCE,
            'TECHNICAL SKILLS': SectionType.SKILLS,
            'CORE COMPETENCIES': SectionType.SKILLS,
            'EDUCATION': SectionType.EDUCATION,
            'ACADEMIC BACKGROUND': SectionType.EDUCATION,
            'PROJECTS': SectionType.PROJECTS,
            'KEY PROJECTS': SectionType.PROJECTS,
        }
        
        if line_clean in common_headers:
            return common_headers[line_clean]
        
        return None
    
    def detect_bullet(self, line: str) -> tuple[bool, str, int]:
        """IMPROVED: Detect bullet points with better accuracy"""
        
        # Calculate indentation level
        indent_level = len(line) - len(line.lstrip())
        
        for pattern in self.bullet_patterns:
            match = re.match(pattern, line)
            if match:
                bullet_text = match.group(1).strip()
                
                # Skip if bullet text is too short (likely not a real bullet)
                if len(bullet_text) < 5:
                    continue
                
                # Determine bullet level based on indentation
                bullet_level = max(0, indent_level // 2)  # Every 2 spaces = 1 level
                
                return True, bullet_text, bullet_level
        
        return False, line, 0
    
    def extract_metadata(self, line: str) -> dict:
        """Extract metadata from line"""
        
        metadata = {}
        
        # Check for contact information
        for contact_type, pattern in self.contact_patterns.items():
            if re.search(pattern, line):
                metadata[f'contains_{contact_type}'] = True
        
        # Check for dates
        date_patterns = [
            r'\b(?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)[a-z]*\s+\d{4}\b',
            r'\b\d{1,2}/\d{1,2}/\d{2,4}\b',
            r'\b\d{4}\s*-\s*\d{4}\b',
            r'\b\d{4}\s*-\s*Present\b'
        ]
        
        for pattern in date_patterns:
            if re.search(pattern, line, re.IGNORECASE):
                metadata['contains_date'] = True
                break
        
        # Check for metrics/numbers
        metric_patterns = [
            r'\b\d+%\b',  # Percentages
            r'\b\$\d+[KMB]?\b',  # Money
            r'\b\d+[KMB]\+?\b',  # Large numbers with K, M, B
            r'\b\d+x\b',  # Multipliers
        ]
        
        for pattern in metric_patterns:
            if re.search(pattern, line):
                metadata['contains_metrics'] = True
                break
        
        return metadata
    
    def process_job_description(self, jd_text: str) -> List[ProcessedLine]:
        """Process job description text"""
        
        cleaned_text = self.clean_text(jd_text)
        lines = cleaned_text.split('\n')
        
        processed_lines = []
        current_section = SectionType.UNKNOWN
        line_number = 1
        
        for raw_line in lines:
            line = raw_line.strip()
            
            if not line:
                continue
            
            # Detect JD-specific sections
            jd_section = self.detect_jd_section(line)
            if jd_section:
                current_section = jd_section
            
            # Check for bullets
            is_bullet, bullet_text, bullet_level = self.detect_bullet(line)
            
            processed_line = ProcessedLine(
                line_number=line_number,
                text=bullet_text if is_bullet else line,
                section=current_section,
                is_bullet=is_bullet,
                bullet_level=bullet_level,
                metadata={'is_jd': True}
            )
            
            processed_lines.append(processed_line)
            line_number += 1
        
        return processed_lines
    
    def detect_jd_section(self, line: str) -> Optional[SectionType]:
        """Detect job description sections"""
        
        line_upper = line.upper().strip()
        
        jd_sections = {
            'REQUIREMENTS': SectionType.SKILLS,
            'REQUIRED QUALIFICATIONS': SectionType.SKILLS,
            'MUST HAVE': SectionType.SKILLS,
            'PREFERRED QUALIFICATIONS': SectionType.SKILLS,
            'NICE TO HAVE': SectionType.SKILLS,
            'RESPONSIBILITIES': SectionType.EXPERIENCE,
            'JOB DESCRIPTION': SectionType.SUMMARY,
            'ABOUT THE ROLE': SectionType.SUMMARY,
        }
        
        for header, section_type in jd_sections.items():
            if header in line_upper:
                return section_type
        
        return None


# Test the improved processor
def test_improved_processor():
    """Test the improved text processor"""
    
    sample_resume = """
    JOHN SMITH
    Email: john.smith@email.com
    Phone: (555) 123-4567
    
    PROFESSIONAL SUMMARY
    Experienced software engineer with 5+ years developing web applications
    
    WORK EXPERIENCE
    
    Senior Software Engineer | TechCorp | 2020 - Present
    • Developed and maintained 3 Python web applications serving 10K+ users
    • Improved application performance by 40% through database optimization
    • Led a team of 4 junior developers on microservices architecture
    • Built CI/CD pipelines reducing deployment time by 60%
    
    Software Engineer | StartupCo | 2018 - 2020
    • Created REST APIs using Django and PostgreSQL
    • Implemented automated testing increasing code coverage to 85%
    • Collaborated with product team on feature requirements
    
    TECHNICAL SKILLS
    • Languages: Python, JavaScript, SQL, Go
    • Frameworks: Django, React, FastAPI
    • Tools: Docker, Kubernetes, AWS, Git
    
    PROJECTS
    • E-commerce Platform: Built full-stack application with 1M+ page views
    • Data Pipeline: Designed ETL system processing 100GB daily
    """
    
    processor = UniversalTextProcessor()
    processed_lines = processor.process_resume(sample_resume)
    
    print("=== IMPROVED TEXT PROCESSOR TEST ===")
    print(f"Total lines processed: {len(processed_lines)}")
    
    bullet_count = sum(1 for line in processed_lines if line.is_bullet)
    print(f"Bullet points found: {bullet_count}")
    
    sections = {}
    for line in processed_lines:
        section = line.section.value
        sections[section] = sections.get(section, 0) + 1
    
    print(f"Sections found: {sections}")
    
    print("\nSample bullets:")
    bullets = [line for line in processed_lines if line.is_bullet]
    for bullet in bullets[:5]:
        print(f"  L{bullet.line_number}: [{bullet.section.value}] {bullet.text[:60]}...")

if __name__ == "__main__":
    test_improved_processor()
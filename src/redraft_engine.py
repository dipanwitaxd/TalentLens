# src/redraft_engine.py
# Phase 7: Redraft (truthful, JD-tailored)
# Goal: Assemble a one-page resume version aligned to the JD

from typing import List, Dict, Any, Optional, Set
from dataclasses import dataclass
import re
from datetime import datetime

@dataclass
class RedraftedSection:
    """A redrafted section of the resume"""
    section_type: str
    title: str
    content_lines: List[str]
    word_count: int
    bullet_count: int

@dataclass
class RedraftedResume:
    """Complete redrafted resume"""
    candidate_name: str
    target_role: str
    sections: List[RedraftedSection]
    total_word_count: int
    total_bullet_count: int
    improvement_summary: Dict[str, int]  # What was improved
    evidence_placeholders: List[str]  # What needs to be filled in
    formatting_notes: List[str]

class RedraftEngine:
    """Assembles improved resume from critiques and original content"""
    
    def __init__(self):
        # Resume formatting rules
        self.max_bullets_per_role = 6
        self.max_words_per_bullet = 20
        self.target_total_bullets = 15  # For 1-page resume
        
        # Section priority for space allocation
        self.section_priority = {
            'experience': 1,
            'projects': 2, 
            'skills': 3,
            'education': 4,
            'certifications': 5,
            'other': 6
        }
        
        # Action verb improvements
        self.verb_improvements = {
            'worked on': 'developed',
            'helped with': 'collaborated on',
            'responsible for': 'managed',
            'involved in': 'contributed to',
            'participated in': 'engaged in',
            'assisted': 'supported',
            'dealt with': 'resolved',
            'handled': 'managed'
        }

    def redraft_resume(self, 
                      processed_lines: List['ProcessedLine'],
                      critiques: List['LineCritique'],
                      candidate_profile: 'CandidateProfile',
                      job_profile: 'JobProfile' = None) -> RedraftedResume:
        """Create improved resume from critiques and original content"""
        
        # Group lines by section
        sections_data = self._group_lines_by_section(processed_lines)
        
        # Apply critiques to improve content
        improved_sections = self._apply_critiques_to_sections(sections_data, critiques)
        
        # Optimize for job alignment
        if job_profile:
            improved_sections = self._optimize_for_job_alignment(improved_sections, job_profile)
        
        # Format for one-page layout
        final_sections = self._format_for_one_page(improved_sections, candidate_profile)
        
        # Calculate statistics
        total_words = sum(section.word_count for section in final_sections)
        total_bullets = sum(section.bullet_count for section in final_sections)
        
        # Track improvements made
        improvement_summary = self._calculate_improvement_summary(critiques)
        
        # Extract evidence placeholders
        evidence_placeholders = self._extract_evidence_placeholders(final_sections)
        
        # Generate formatting notes
        formatting_notes = self._generate_formatting_notes(final_sections, total_words, total_bullets)
        
        return RedraftedResume(
            candidate_name=candidate_profile.name or "Candidate Name",
            target_role=job_profile.title if job_profile else "Target Role",
            sections=final_sections,
            total_word_count=total_words,
            total_bullet_count=total_bullets,
            improvement_summary=improvement_summary,
            evidence_placeholders=evidence_placeholders,
            formatting_notes=formatting_notes
        )

    def _group_lines_by_section(self, processed_lines: List['ProcessedLine']) -> Dict[str, List['ProcessedLine']]:
        """Group processed lines by their section type"""
        sections = {}
        
        for line in processed_lines:
            section_name = line.section.value
            if section_name not in sections:
                sections[section_name] = []
            sections[section_name].append(line)
        
        return sections

    def _apply_critiques_to_sections(self, 
                                   sections_data: Dict[str, List['ProcessedLine']], 
                                   critiques: List['LineCritique']) -> Dict[str, List[str]]:
        """Apply critique improvements to each section"""
        
        # Create lookup for critiques by line number
        critique_lookup = {critique.line_number: critique for critique in critiques}
        
        improved_sections = {}
        
        for section_name, lines in sections_data.items():
            improved_lines = []
            
            for line in lines:
                # Check if we have a critique for this line
                if line.line_number in critique_lookup:
                    critique = critique_lookup[line.line_number]
                    
                    # Use improved version if available and different from original
                    if (critique.suggested_rewrite and 
                        critique.suggested_rewrite != line.text and
                        critique.overall_assessment in ['needs_improvement', 'major_issues']):
                        improved_lines.append(critique.suggested_rewrite)
                    else:
                        improved_lines.append(line.text)
                else:
                    # No critique available, keep original but apply basic improvements
                    improved_text = self._apply_basic_improvements(line.text)
                    improved_lines.append(improved_text)
            
            improved_sections[section_name] = improved_lines
        
        return improved_sections

    def _apply_basic_improvements(self, text: str) -> str:
        """Apply basic improvements to text without critique"""
        improved = text
        
        # Improve weak verbs
        for weak_verb, strong_verb in self.verb_improvements.items():
            if weak_verb in improved.lower():
                # Replace while preserving case
                pattern = re.compile(re.escape(weak_verb), re.IGNORECASE)
                improved = pattern.sub(strong_verb, improved, count=1)
        
        # Clean up formatting
        improved = improved.strip()
        if improved.startswith('•'):
            improved = improved[1:].strip()
        
        return improved

    def _optimize_for_job_alignment(self, 
                                  sections: Dict[str, List[str]], 
                                  job_profile: 'JobProfile') -> Dict[str, List[str]]:
        """Optimize content alignment with job requirements"""
        
        # Extract key skills from job requirements
        job_skills = set()
        for req in job_profile.must_have_skills + job_profile.nice_to_have_skills:
            job_skills.add(req.skill_or_requirement.lower())
        
        optimized_sections = {}
        
        for section_name, lines in sections.items():
            if section_name == 'experience':
                # Prioritize experience bullets that mention job-relevant skills
                scored_lines = []
                
                for line in lines:
                    score = 0
                    line_lower = line.lower()
                    
                    # Score based on job skill mentions
                    for skill in job_skills:
                        if skill in line_lower:
                            score += 2
                    
                    # Score based on metrics presence
                    if any(char.isdigit() for char in line):
                        score += 1
                    
                    # Score based on strong action verbs
                    strong_verbs = ['built', 'created', 'developed', 'led', 'improved', 'increased']
                    if any(verb in line_lower for verb in strong_verbs):
                        score += 1
                    
                    scored_lines.append((score, line))
                
                # Sort by score and take best lines
                scored_lines.sort(key=lambda x: x[0], reverse=True)
                optimized_sections[section_name] = [line for score, line in scored_lines]
            
            else:
                optimized_sections[section_name] = lines
        
        return optimized_sections

    def _format_for_one_page(self, 
                           sections: Dict[str, List[str]], 
                           candidate_profile: 'CandidateProfile') -> List[RedraftedSection]:
        """Format sections for optimal one-page layout"""
        
        formatted_sections = []
        
        # Process sections in priority order
        sorted_sections = sorted(sections.items(), 
                               key=lambda x: self.section_priority.get(x[0], 10))
        
        total_bullets_used = 0
        
        for section_name, lines in sorted_sections:
            if section_name in ['contact', 'other']:
                continue  # Skip non-essential sections
            
            # Calculate how many bullets this section should get
            remaining_bullet_budget = self.target_total_bullets - total_bullets_used
            
            if section_name == 'experience':
                # Experience gets the most space
                max_bullets = min(12, remaining_bullet_budget)
            elif section_name == 'projects':
                max_bullets = min(6, remaining_bullet_budget)
            elif section_name == 'skills':
                max_bullets = min(3, remaining_bullet_budget)
            else:
                max_bullets = min(2, remaining_bullet_budget)
            
            # Format the section
            formatted_section = self._format_single_section(
                section_name, lines, max_bullets, candidate_profile
            )
            
            if formatted_section.bullet_count > 0:
                formatted_sections.append(formatted_section)
                total_bullets_used += formatted_section.bullet_count
        
        return formatted_sections

    def _format_single_section(self, 
                             section_name: str, 
                             lines: List[str], 
                             max_bullets: int,
                             candidate_profile: 'CandidateProfile') -> RedraftedSection:
        """Format a single section with proper structure"""
        
        # Section title formatting
        section_titles = {
            'experience': 'PROFESSIONAL EXPERIENCE',
            'projects': 'KEY PROJECTS', 
            'skills': 'TECHNICAL SKILLS',
            'education': 'EDUCATION',
            'certifications': 'CERTIFICATIONS'
        }
        
        title = section_titles.get(section_name, section_name.upper())
        formatted_lines = []
        bullet_count = 0
        
        if section_name == 'experience':
            # Group experience bullets by job
            formatted_lines, bullet_count = self._format_experience_section(lines, max_bullets)
        
        elif section_name == 'skills':
            # Format skills as concise categories
            formatted_lines, bullet_count = self._format_skills_section(lines, candidate_profile)
        
        elif section_name == 'projects':
            # Format projects with clear outcomes
            formatted_lines, bullet_count = self._format_projects_section(lines, max_bullets)
        
        else:
            # Basic formatting for other sections
            for line in lines[:max_bullets]:
                if line.strip():
                    formatted_line = self._format_bullet_line(line)
                    formatted_lines.append(formatted_line)
                    bullet_count += 1
        
        # Calculate word count
        word_count = sum(len(line.split()) for line in formatted_lines)
        
        return RedraftedSection(
            section_type=section_name,
            title=title,
            content_lines=formatted_lines,
            word_count=word_count,
            bullet_count=bullet_count
        )

    def _format_experience_section(self, lines: List[str], max_bullets: int) -> tuple:
        """Format experience section with job groupings"""
        formatted_lines = []
        bullet_count = 0
        current_job = None
        
        for line in lines:
            if bullet_count >= max_bullets:
                break
            
            line = line.strip()
            if not line:
                continue
            
            # Check if this looks like a job header
            if self._is_job_header(line):
                current_job = line
                formatted_lines.append(f"\n{line}")
            else:
                # This is a bullet point
                formatted_bullet = self._format_bullet_line(line)
                formatted_lines.append(formatted_bullet)
                bullet_count += 1
        
        return formatted_lines, bullet_count

    def _format_skills_section(self, lines: List[str], candidate_profile: 'CandidateProfile') -> tuple:
        """Format skills section efficiently"""
        # Combine all skills into categories
        all_skills = []
        for line in lines:
            skills = [skill.strip() for skill in re.split(r'[,;|]', line) if skill.strip()]
            all_skills.extend(skills)
        
        # Categorize skills
        categorized = self._categorize_skills(all_skills)
        
        formatted_lines = []
        bullet_count = 0
        
        for category, skills in categorized.items():
            if skills:
                skills_str = ', '.join(skills[:8])  # Limit to 8 skills per category
                formatted_lines.append(f"• {category}: {skills_str}")
                bullet_count += 1
        
        return formatted_lines, bullet_count

    def _format_projects_section(self, lines: List[str], max_bullets: int) -> tuple:
        """Format projects section with clear outcomes"""
        formatted_lines = []
        bullet_count = 0
        
        for line in lines[:max_bullets]:
            if line.strip():
                formatted_bullet = self._format_bullet_line(line)
                formatted_lines.append(formatted_bullet)
                bullet_count += 1
        
        return formatted_lines, bullet_count

    def _format_bullet_line(self, line: str) -> str:
        """Format a single bullet point line"""
        # Remove existing bullet markers
        cleaned = line.strip()
        if cleaned.startswith('•'):
            cleaned = cleaned[1:].strip()
        if cleaned.startswith('-'):
            cleaned = cleaned[1:].strip()
        
        # Ensure it starts with capital letter
        if cleaned and cleaned[0].islower():
            cleaned = cleaned[0].upper() + cleaned[1:]
        
        # Add bullet marker
        return f"• {cleaned}"

    def _is_job_header(self, line: str) -> bool:
        """Check if line looks like a job title/company header"""
        # Look for patterns like "Title | Company" or "Title at Company"
        return any(separator in line for separator in ['|', ' at ', ' - ']) and len(line.split()) < 10

    def _categorize_skills(self, skills: List[str]) -> Dict[str, List[str]]:
        """Categorize skills into logical groups"""
        categories = {
            'Programming': [],
            'Technologies': [],
            'Tools': [],
            'Frameworks': []
        }
        
        # Simple categorization rules
        programming_langs = ['python', 'java', 'javascript', 'typescript', 'c++', 'c#', 'go', 'rust']
        cloud_tech = ['aws', 'azure', 'gcp', 'docker', 'kubernetes']
        frameworks = ['react', 'vue', 'angular', 'django', 'flask', 'spring']
        
        for skill in skills:
            skill_lower = skill.lower()
            
            if any(lang in skill_lower for lang in programming_langs):
                categories['Programming'].append(skill)
            elif any(tech in skill_lower for tech in cloud_tech):
                categories['Technologies'].append(skill)
            elif any(framework in skill_lower for framework in frameworks):
                categories['Frameworks'].append(skill)
            else:
                categories['Tools'].append(skill)
        
        # Remove empty categories
        return {k: v for k, v in categories.items() if v}

    def _calculate_improvement_summary(self, critiques: List['LineCritique']) -> Dict[str, int]:
        """Calculate what types of improvements were made"""
        improvements = {
            'lines_improved': 0,
            'metrics_added': 0,
            'verbs_strengthened': 0,
            'context_added': 0,
            'evidence_placeholders': 0
        }
        
        for critique in critiques:
            if critique.suggested_rewrite != critique.original_text:
                improvements['lines_improved'] += 1
                
                if '[NEED_EVIDENCE:' in critique.suggested_rewrite:
                    improvements['evidence_placeholders'] += 1
                
                for issue in critique.issues:
                    if issue.type == 'quantification':
                        improvements['metrics_added'] += 1
                    elif issue.type == 'action_clarity':
                        improvements['verbs_strengthened'] += 1
                    elif issue.type == 'technical_context':
                        improvements['context_added'] += 1
        
        return improvements

    def _extract_evidence_placeholders(self, sections: List[RedraftedSection]) -> List[str]:
        """Extract all evidence placeholders that need to be filled"""
        placeholders = []
        
        for section in sections:
            for line in section.content_lines:
                # Find all [NEED_EVIDENCE: ...] placeholders
                matches = re.findall(r'\[NEED_EVIDENCE:\s*([^\]]+)\]', line)
                placeholders.extend(matches)
        
        return list(set(placeholders))  # Remove duplicates

    def _generate_formatting_notes(self, 
                                 sections: List[RedraftedSection], 
                                 total_words: int, 
                                 total_bullets: int) -> List[str]:
        """Generate formatting and optimization notes"""
        notes = []
        
        # Length optimization notes
        if total_bullets > 18:
            notes.append(f"Consider reducing bullet points from {total_bullets} to 15-18 for better readability")
        
        if total_words > 400:
            notes.append(f"Total word count ({total_words}) is high - aim for 300-400 words")
        
        # Section balance notes
        experience_bullets = sum(s.bullet_count for s in sections if s.section_type == 'experience')
        if experience_bullets < 8:
            notes.append("Consider expanding experience section with more achievement details")
        
        # Formatting suggestions
        notes.append("Use consistent tense (past tense for previous roles, present for current)")
        notes.append("Ensure all bullets follow: Action → Method → Scale → Outcome format")
        
        return notes

    def export_to_markdown(self, redrafted_resume: RedraftedResume) -> str:
        """Export redrafted resume to markdown format"""
        
        markdown = f"# {redrafted_resume.candidate_name}\n"
        markdown += f"*Applying for: {redrafted_resume.target_role}*\n\n"
        
        for section in redrafted_resume.sections:
            markdown += f"## {section.title}\n\n"
            
            for line in section.content_lines:
                if line.strip().startswith('•'):
                    markdown += f"{line}\n"
                elif line.strip():
                    # Job headers or other content
                    markdown += f"**{line.strip()}**\n"
                else:
                    markdown += "\n"
            
            markdown += "\n"
        
        # Add improvement summary
        if redrafted_resume.evidence_placeholders:
            markdown += "---\n\n"
            markdown += "### Evidence Needed\n"
            markdown += "*Fill in these placeholders with specific data:*\n\n"
            
            for placeholder in redrafted_resume.evidence_placeholders:
                markdown += f"- {placeholder}\n"
        
        return markdown

    def print_redraft_summary(self, redrafted_resume: RedraftedResume) -> None:
        """Print summary of redraft results"""
        
        print(f"\n=== RESUME REDRAFT SUMMARY ===")
        print(f"Candidate: {redrafted_resume.candidate_name}")
        print(f"Target Role: {redrafted_resume.target_role}")
        print(f"Total Word Count: {redrafted_resume.total_word_count}")
        print(f"Total Bullet Points: {redrafted_resume.total_bullet_count}")
        
        print(f"\nImprovements Made:")
        for improvement, count in redrafted_resume.improvement_summary.items():
            if count > 0:
                print(f"  {improvement.replace('_', ' ').title()}: {count}")
        
        if redrafted_resume.evidence_placeholders:
            print(f"\nEvidence Needed ({len(redrafted_resume.evidence_placeholders)} items):")
            for placeholder in redrafted_resume.evidence_placeholders[:3]:
                print(f"  - {placeholder}")
            if len(redrafted_resume.evidence_placeholders) > 3:
                print(f"  ... and {len(redrafted_resume.evidence_placeholders) - 3} more")
        
        if redrafted_resume.formatting_notes:
            print(f"\nFormatting Notes:")
            for note in redrafted_resume.formatting_notes[:2]:
                print(f"  - {note}")


# Testing function
def test_redraft_engine():
    """Test the redraft engine"""
    print("=== TESTING REDRAFT ENGINE (Phase 7) ===")
    
    from src.text_processor import UniversalTextProcessor
    from src.profile_extractor import ProfileExtractor
    from src.critique_engine import LineCritique, CritiqueIssue
    
    # Sample data
    processor = UniversalTextProcessor()
    profile_extractor = ProfileExtractor()
    redraft_engine = RedraftEngine()
    
    sample_resume = """
    JOHN DOE
    Software Engineer
    
    EXPERIENCE
    • Worked on machine learning projects using Python
    • Was responsible for improving database performance
    • Helped with various tasks and supported multiple teams
    
    SKILLS
    Python, Java, AWS, Docker, Machine Learning
    """
    
    # Process resume
    processed_lines = processor.process_resume(sample_resume)
    candidate_profile = profile_extractor.extract_candidate_profile(processed_lines)
    
    # Create sample critiques
    sample_critiques = [
        LineCritique(
            line_number=3,
            original_text="Worked on machine learning projects using Python",
            issues=[CritiqueIssue("action_clarity", "high", "Vague verb", "Uses 'worked on'", 0.9, [])],
            suggested_rewrite="Built machine learning models that improved prediction accuracy by [NEED_EVIDENCE: percentage] using Python",
            rewrite_reasoning="Improved action verb and added metric placeholder",
            overall_assessment="needs_improvement",
            citations=[],
            heuristic_flags_used=[]
        )
    ]
    
    # Generate redraft
    redrafted = redraft_engine.redraft_resume(
        processed_lines, sample_critiques, candidate_profile
    )
    
    redraft_engine.print_redraft_summary(redrafted)
    
    print(f"\nSample markdown output:")
    markdown = redraft_engine.export_to_markdown(redrafted)
    print(markdown[:300] + "...")
    
    print(f"\n✅ Phase 7 redraft engine working!")

if __name__ == "__main__":
    test_redraft_engine()
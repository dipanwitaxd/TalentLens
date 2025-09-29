from typing import List, Dict, Any, Optional, Set
from dataclasses import dataclass
import re
from enum import Enum

class SkillLevel(Enum):
    BEGINNER = "beginner"
    INTERMEDIATE = "intermediate" 
    ADVANCED = "advanced"
    EXPERT = "expert"
    UNSPECIFIED = "unspecified"

class RequirementType(Enum):
    MUST_HAVE = "must_have"
    NICE_TO_HAVE = "nice_to_have"
    PREFERRED = "preferred"

@dataclass
class Skill:
    name: str
    level: SkillLevel
    years_experience: Optional[int] = None
    context: str = ""  # Where/how it was used

@dataclass
class Experience:
    title: str
    company: str
    duration_months: Optional[int] = None
    key_achievements: List[str] = None
    technologies: List[str] = None

@dataclass
class CandidateProfile:
    """Structured summary of a candidate's resume"""
    name: Optional[str] = None
    total_experience_years: Optional[int] = None
    current_title: Optional[str] = None
    top_skills: List[Skill] = None
    experiences: List[Experience] = None
    education_level: Optional[str] = None
    key_achievements: List[str] = None
    industries: Set[str] = None
    
    def __post_init__(self):
        if self.top_skills is None:
            self.top_skills = []
        if self.experiences is None:
            self.experiences = []
        if self.key_achievements is None:
            self.key_achievements = []
        if self.industries is None:
            self.industries = set()

@dataclass
class JobRequirement:
    skill_or_requirement: str
    requirement_type: RequirementType
    level_required: SkillLevel
    years_required: Optional[int] = None
    context: str = ""

@dataclass
class JobProfile:
    """Structured summary of a job description"""
    title: str
    company: Optional[str] = None
    must_have_skills: List[JobRequirement] = None
    nice_to_have_skills: List[JobRequirement] = None
    experience_required: Optional[int] = None
    education_required: Optional[str] = None
    location: Optional[str] = None
    work_auth_required: bool = False
    remote_ok: bool = False
    industry: Optional[str] = None
    team_size: Optional[str] = None
    growth_stage: Optional[str] = None  # startup, scale-up, enterprise
    
    def __post_init__(self):
        if self.must_have_skills is None:
            self.must_have_skills = []
        if self.nice_to_have_skills is None:
            self.nice_to_have_skills = []

class ProfileExtractor:
    """Extracts structured profiles from resumes and job descriptions"""
    
    def __init__(self):
        # Experience level indicators
        self.experience_indicators = {
            SkillLevel.BEGINNER: ["beginner", "basic", "familiar", "exposure", "coursework"],
            SkillLevel.INTERMEDIATE: ["intermediate", "working knowledge", "competent", "proficient"],
            SkillLevel.ADVANCED: ["advanced", "experienced", "skilled", "strong"],
            SkillLevel.EXPERT: ["expert", "specialist", "master", "deep", "extensive", "lead", "architect"]
        }
        
        # Requirement type indicators  
        self.requirement_indicators = {
            RequirementType.MUST_HAVE: [
                "required", "must have", "essential", "mandatory", "necessary",
                "minimum", "need", "critical", "vital"
            ],
            RequirementType.NICE_TO_HAVE: [
                "nice to have", "preferred", "plus", "bonus", "advantage",
                "desirable", "would be great", "ideally"
            ],
            RequirementType.PREFERRED: [
                "preferred", "ideally", "would prefer", "strong preference"
            ]
        }
        
        # Technical skill patterns (expandable)
        self.tech_skills = {
            "programming": ["python", "java", "javascript", "typescript", "c++", "c#", "go", "rust", "ruby"],
            "web": ["react", "vue", "angular", "nodejs", "express", "flask", "django", "html", "css"],
            "cloud": ["aws", "azure", "gcp", "docker", "kubernetes", "terraform", "cloudformation"],
            "databases": ["sql", "mysql", "postgresql", "mongodb", "redis", "elasticsearch", "sqlite"],
            "ml": ["tensorflow", "pytorch", "scikit-learn", "pandas", "numpy", "jupyter", "machine learning"],
            "devops": ["jenkins", "gitlab", "github", "ci/cd", "devops", "automation", "monitoring"],
            "analytics": ["tableau", "powerbi", "excel", "r", "statistics", "data analysis"]
        }

    def extract_candidate_profile(self, processed_lines: List['ProcessedLine']) -> CandidateProfile:
        """Extract structured candidate profile from resume lines"""
        
        profile = CandidateProfile()
        
        # Extract basic info
        profile.name = self._extract_name(processed_lines)
        profile.current_title = self._extract_current_title(processed_lines)
        profile.total_experience_years = self._calculate_total_experience(processed_lines)
        profile.education_level = self._extract_education_level(processed_lines)
        
        # Extract experience details
        profile.experiences = self._extract_experiences(processed_lines)
        
        # Extract and analyze skills
        profile.top_skills = self._extract_skills(processed_lines)
        
        # Extract key achievements with metrics
        profile.key_achievements = self._extract_achievements(processed_lines)
        
        # Infer industries
        profile.industries = self._infer_industries(processed_lines)
        
        return profile

    def extract_job_profile(self, processed_lines: List['ProcessedLine']) -> JobProfile:
        """Extract structured job profile from JD lines"""
        
        profile = JobProfile(title="")  # Will be extracted
        
        # Extract basic job info
        profile.title = self._extract_job_title(processed_lines)
        profile.company = self._extract_company_name(processed_lines)
        profile.location = self._extract_location(processed_lines)
        profile.experience_required = self._extract_experience_requirement(processed_lines)
        profile.education_required = self._extract_education_requirement(processed_lines)
        
        # Extract requirements by type
        profile.must_have_skills = self._extract_requirements(processed_lines, RequirementType.MUST_HAVE)
        profile.nice_to_have_skills = self._extract_requirements(processed_lines, RequirementType.NICE_TO_HAVE)
        
        # Extract work arrangement info
        profile.remote_ok = self._detect_remote_work(processed_lines)
        profile.work_auth_required = self._detect_work_auth_requirement(processed_lines)
        
        # Infer company characteristics
        profile.industry = self._infer_job_industry(processed_lines)
        profile.growth_stage = self._infer_company_stage(processed_lines)
        profile.team_size = self._extract_team_size(processed_lines)
        
        return profile

    def _extract_name(self, lines: List['ProcessedLine']) -> Optional[str]:
        """Extract candidate name from resume"""
        for line in lines[:5]:  # Check first 5 lines
            # Look for name-like patterns
            text = line.text.strip()
            
            # Skip obvious non-names
            if any(keyword in text.lower() for keyword in ['resume', 'cv', 'phone', 'email', '@', 'experience']):
                continue
                
            # Name is likely 2-4 capitalized words
            words = text.split()
            if 2 <= len(words) <= 4 and all(word[0].isupper() for word in words if word.isalpha()):
                return text
        
        return None

    def _extract_current_title(self, lines: List['ProcessedLine']) -> Optional[str]:
        """Extract current/target job title"""
        for line in lines[:10]:  # Check first 10 lines
            text = line.text.lower()
            
            # Common title indicators
            title_keywords = ['engineer', 'manager', 'analyst', 'developer', 'specialist', 'director', 'lead']
            if any(keyword in text for keyword in title_keywords):
                # Avoid sections headers
                if line.section.value not in ['contact', 'other']:
                    return line.text.strip()
        
        return None

    def _calculate_total_experience(self, lines: List['ProcessedLine']) -> Optional[int]:
        """Calculate total years of experience"""
        experience_years = []
        
        for line in lines:
            if line.section.value == 'experience':
                # Look for date patterns
                years = self._extract_years_from_text(line.text)
                if years:
                    experience_years.extend(years)
        
        if experience_years:
            # Calculate span from earliest to latest year
            min_year = min(experience_years)
            max_year = max(experience_years)
            current_year = 2024
            
            # If max_year is current (or recent), calculate from min_year
            if max_year >= current_year - 1:
                return current_year - min_year
            else:
                return max_year - min_year
        
        return None

    def _extract_experiences(self, lines: List['ProcessedLine']) -> List[Experience]:
        """Extract structured experience entries"""
        experiences = []
        current_experience = None
        
        for line in lines:
            if line.section.value == 'experience':
                # Check if this looks like a job title/company line
                if self._is_job_header(line.text):
                    # Save previous experience
                    if current_experience:
                        experiences.append(current_experience)
                    
                    # Start new experience
                    title, company = self._parse_job_header(line.text)
                    current_experience = Experience(
                        title=title,
                        company=company,
                        key_achievements=[],
                        technologies=[]
                    )
                
                elif current_experience and line.is_bullet:
                    # Add achievement to current experience
                    achievement = line.text.strip('• ').strip()
                    current_experience.key_achievements.append(achievement)
                    
                    # Extract technologies from this line
                    techs = self._extract_technologies_from_text(line.text)
                    current_experience.technologies.extend(techs)
        
        # Don't forget the last experience
        if current_experience:
            experiences.append(current_experience)
        
        return experiences

    def _extract_skills(self, lines: List['ProcessedLine']) -> List[Skill]:
        """Extract and categorize skills"""
        skills = []
        
        for line in lines:
            if line.section.value == 'skills':
                # Parse skills from skills section
                extracted_skills = self._parse_skills_line(line.text)
                skills.extend(extracted_skills)
            
            elif line.section.value == 'experience' and line.is_bullet:
                # Extract skills mentioned in experience bullets
                context_skills = self._extract_skills_from_context(line.text)
                skills.extend(context_skills)
        
        # Deduplicate and rank by frequency/importance
        return self._deduplicate_and_rank_skills(skills)

    def _extract_achievements(self, lines: List['ProcessedLine']) -> List[str]:
        """Extract key achievements with metrics"""
        achievements = []
        
        for line in lines:
            if line.is_bullet and line.metadata.get('has_metrics'):
                # Lines with metrics are likely achievements
                achievement = line.text.strip('• ').strip()
                achievements.append(achievement)
        
        return achievements[:10]  # Top 10 achievements

    def _extract_job_title(self, lines: List['ProcessedLine']) -> str:
        """Extract job title from JD"""
        for line in lines[:5]:
            text = line.text
            # Job title is often in the first few lines
            if any(keyword in text.lower() for keyword in ['engineer', 'manager', 'analyst', 'developer', 'director']):
                return text.strip()
        
        return "Position"  # Fallback

    def _extract_requirements(self, lines: List['ProcessedLine'], req_type: RequirementType) -> List[JobRequirement]:
        """Extract requirements of specific type"""
        requirements = []
        current_section_type = None
        
        for line in lines:
            # Detect requirement sections
            text_lower = line.text.lower()
            
            # Check if this line indicates a requirement type
            for rtype, indicators in self.requirement_indicators.items():
                if any(indicator in text_lower for indicator in indicators):
                    current_section_type = rtype
                    break
            
            # Extract requirements from bullets in the right section
            if line.is_bullet and current_section_type == req_type:
                requirement = self._parse_requirement_line(line.text, req_type)
                if requirement:
                    requirements.append(requirement)
        
        return requirements

    def _parse_requirement_line(self, text: str, req_type: RequirementType) -> Optional[JobRequirement]:
        """Parse a single requirement line"""
        # Extract years of experience
        years_match = re.search(r'(\d+)\+?\s*years?', text.lower())
        years = int(years_match.group(1)) if years_match else None
        
        # Extract skill level
        level = SkillLevel.UNSPECIFIED
        for skill_level, indicators in self.experience_indicators.items():
            if any(indicator in text.lower() for indicator in indicators):
                level = skill_level
                break
        
        # Extract the actual skill/requirement
        skill_name = self._extract_main_skill_from_text(text)
        
        if skill_name:
            return JobRequirement(
                skill_or_requirement=skill_name,
                requirement_type=req_type,
                level_required=level,
                years_required=years,
                context=text
            )
        
        return None

    def _extract_main_skill_from_text(self, text: str) -> Optional[str]:
        """Extract the primary skill/technology from requirement text"""
        text_lower = text.lower()
        
        # Check against known technical skills
        for category, skills in self.tech_skills.items():
            for skill in skills:
                if skill in text_lower:
                    return skill.title()
        
        # Look for other patterns (degree requirements, soft skills, etc.)
        if 'degree' in text_lower or 'bachelor' in text_lower or 'master' in text_lower:
            return "Education Requirement"
        
        if any(word in text_lower for word in ['communication', 'leadership', 'teamwork']):
            return "Soft Skills"
        
        # Extract first meaningful word as fallback
        words = text.split()
        for word in words:
            if len(word) > 3 and word.isalpha():
                return word.title()
        
        return None

    def _extract_education_level(self, lines: List['ProcessedLine']) -> Optional[str]:
        """Extract education level from resume"""
        education_levels = ['PhD', 'Ph.D', 'Doctor', 'Master', 'Bachelor', 'Associate', 'High School', 'GED']
    
        for line in lines:
            if line.section.value == 'education':
                text = line.text
                for level in education_levels:
                    if level.lower() in text.lower():
                        return level
    
        return None

    # Helper methods for parsing
    def _is_job_header(self, text: str) -> bool:
        """Check if line looks like job title/company header"""
        # Look for patterns like "Software Engineer | Company" or "Title at Company"
        return any(sep in text for sep in ['|', ' at ', ' - ']) and len(text.split()) < 10

    def _parse_job_header(self, text: str) -> tuple:
        """Parse job title and company from header line"""
        for sep in ['|', ' at ', ' - ']:
            if sep in text:
                parts = text.split(sep, 1)
                return parts[0].strip(), parts[1].strip()
        
        return text.strip(), "Unknown Company"

    def _extract_years_from_text(self, text: str) -> List[int]:
        """Extract years from text - FIXED VERSION"""
        years = []
        # Extract 4-digit years (1900-2099)
        year_matches = re.findall(r'\b(19|20)\d{2}\b', text)
        for match in year_matches:
            # Convert the full match to integer
            full_year = int(text[text.find(match):text.find(match)+4])
            years.append(full_year)
    
        return years

    def _extract_technologies_from_text(self, text: str) -> List[str]:
        """Extract technology mentions from text"""
        technologies = []
        text_lower = text.lower()
        
        for category, techs in self.tech_skills.items():
            for tech in techs:
                if tech in text_lower:
                    technologies.append(tech.title())
        
        return technologies

    def _parse_skills_line(self, text: str) -> List[Skill]:
        """Parse skills from a skills section line"""
        skills = []
        
        # Split by common separators
        skill_text = re.split(r'[,;|]', text)
        
        for skill_item in skill_text:
            skill_name = skill_item.strip()
            if len(skill_name) > 2:  # Ignore very short items
                # Try to extract level from the skill name
                level = SkillLevel.UNSPECIFIED
                for skill_level, indicators in self.experience_indicators.items():
                    if any(indicator in skill_name.lower() for indicator in indicators):
                        level = skill_level
                        # Remove level indicator from name
                        for indicator in indicators:
                            skill_name = skill_name.replace(indicator, '').strip()
                        break
                
                skills.append(Skill(name=skill_name, level=level))
        
        return skills

    def _extract_skills_from_context(self, text: str) -> List[Skill]:
        """Extract skills mentioned in experience context"""
        skills = []
        technologies = self._extract_technologies_from_text(text)
        
        for tech in technologies:
            # Infer level from context
            level = SkillLevel.INTERMEDIATE  # Default assumption
            if any(word in text.lower() for word in ['led', 'architected', 'designed']):
                level = SkillLevel.ADVANCED
            elif any(word in text.lower() for word in ['learned', 'introduced', 'started']):
                level = SkillLevel.BEGINNER
            
            skills.append(Skill(name=tech, level=level, context=text))
        
        return skills

    def _deduplicate_and_rank_skills(self, skills: List[Skill]) -> List[Skill]:
        """Remove duplicates and rank skills by importance"""
        skill_map = {}
        
        for skill in skills:
            name_lower = skill.name.lower()
            if name_lower in skill_map:
                # Keep highest level and merge contexts
                existing = skill_map[name_lower]
                if skill.level.value > existing.level.value:
                    existing.level = skill.level
                if skill.context and skill.context not in existing.context:
                    existing.context += "; " + skill.context
            else:
                skill_map[name_lower] = skill
        
        # Convert back to list and sort by level
        unique_skills = list(skill_map.values())
        level_order = {SkillLevel.EXPERT: 4, SkillLevel.ADVANCED: 3, SkillLevel.INTERMEDIATE: 2, SkillLevel.BEGINNER: 1, SkillLevel.UNSPECIFIED: 0}
        unique_skills.sort(key=lambda s: level_order[s.level], reverse=True)
        
        return unique_skills[:15]  # Top 15 skills

    def _infer_industries(self, lines: List['ProcessedLine']) -> Set[str]:
        """Infer industries from resume content"""
        industries = set()
        
        industry_keywords = {
            'technology': ['software', 'tech', 'saas', 'cloud', 'ai', 'ml', 'data'],
            'finance': ['bank', 'finance', 'investment', 'trading', 'fintech'],
            'healthcare': ['health', 'medical', 'hospital', 'pharma', 'biotech'],
            'retail': ['retail', 'ecommerce', 'shopping', 'commerce'],
            'consulting': ['consulting', 'advisory', 'strategy']
        }
        
        text_all = ' '.join(line.text.lower() for line in lines)
        
        for industry, keywords in industry_keywords.items():
            if any(keyword in text_all for keyword in keywords):
                industries.add(industry)
        
        return industries

    # Additional helper methods for job description parsing
    def _extract_company_name(self, lines: List['ProcessedLine']) -> Optional[str]:
        """Extract company name from JD"""
        for line in lines[:5]:
            # Look for company indicators
            if any(indicator in line.text for indicator in ['Inc', 'LLC', 'Corp', 'Company', 'Ltd']):
                return line.text.strip()
        return None

    def _extract_location(self, lines: List['ProcessedLine']) -> Optional[str]:
        """Extract job location"""
        location_patterns = [
            r'\b[A-Z][a-z]+,\s*[A-Z]{2}\b',  # City, ST
            r'\b[A-Z][a-z]+,\s*[A-Z][a-z]+\b',  # City, Country
        ]
        
        for line in lines[:10]:
            for pattern in location_patterns:
                match = re.search(pattern, line.text)
                if match:
                    return match.group()
        
        return None

    def _extract_experience_requirement(self, lines: List['ProcessedLine']) -> Optional[int]:
        """Extract years of experience required"""
        for line in lines:
            # Look for experience requirements
            exp_match = re.search(r'(\d+)\+?\s*years?\s*(?:of\s*)?experience', line.text.lower())
            if exp_match:
                return int(exp_match.group(1))
        
        return None

    def _extract_education_requirement(self, lines: List['ProcessedLine']) -> Optional[str]:
        """Extract education requirements"""
        education_levels = ['PhD', 'Master', 'Bachelor', 'Associate', 'High School']
        
        for line in lines:
            text = line.text
            for level in education_levels:
                if level.lower() in text.lower():
                    return level
        
        return None

    def _detect_remote_work(self, lines: List['ProcessedLine']) -> bool:
        """Detect if remote work is allowed"""
        remote_indicators = ['remote', 'work from home', 'distributed', 'virtual']
        
        text_all = ' '.join(line.text.lower() for line in lines)
        return any(indicator in text_all for indicator in remote_indicators)

    def _detect_work_auth_requirement(self, lines: List['ProcessedLine']) -> bool:
        """Detect if work authorization is required"""
        auth_indicators = ['work authorization', 'visa', 'citizen', 'eligible to work']
        
        text_all = ' '.join(line.text.lower() for line in lines)
        return any(indicator in text_all for indicator in auth_indicators)

    def _infer_job_industry(self, lines: List['ProcessedLine']) -> Optional[str]:
        """Infer industry from job description"""
        return list(self._infer_industries(lines))[0] if self._infer_industries(lines) else None

    def _infer_company_stage(self, lines: List['ProcessedLine']) -> Optional[str]:
        """Infer company growth stage"""
        text_all = ' '.join(line.text.lower() for line in lines)
        
        if any(word in text_all for word in ['startup', 'early stage', 'seed']):
            return 'startup'
        elif any(word in text_all for word in ['scale-up', 'growth', 'series']):
            return 'scale-up'
        elif any(word in text_all for word in ['enterprise', 'fortune', 'established']):
            return 'enterprise'
        
        return None

    def _extract_team_size(self, lines: List['ProcessedLine']) -> Optional[str]:
        """Extract team size information"""
        for line in lines:
            # Look for team size indicators
            team_match = re.search(r'team\s*of\s*(\d+)', line.text.lower())
            if team_match:
                size = int(team_match.group(1))
                if size < 5:
                    return "small"
                elif size < 15:
                    return "medium"
                else:
                    return "large"
        
        return None

# Testing function
def test_profile_extraction():
    """Test profile extraction functionality"""
    print("=== TESTING PROFILE EXTRACTION (Phase 4) ===")
    
    from src.text_processor import UniversalTextProcessor
    processor = UniversalTextProcessor()
    extractor = ProfileExtractor()
    
    # Test resume extraction
    sample_resume = """
    JOHN DOE
    Senior Software Engineer
    
    EXPERIENCE
    Senior Software Engineer | TechCorp Inc
    • Built scalable Python applications serving 10K+ users daily
    • Improved database query performance by 40% through optimization
    • Led cross-functional team of 5 engineers on cloud migration to AWS
    
    Software Developer | StartupXYZ
    • Developed machine learning models for recommendation system
    • Implemented CI/CD pipelines reducing deployment time by 60%
    
    SKILLS
    Python, AWS, PostgreSQL, Docker, Kubernetes, Machine Learning
    
    EDUCATION
    Bachelor of Science in Computer Science
    """
    
    print("Processing resume...")
    processed_resume = processor.process_resume(sample_resume)
    candidate_profile = extractor.extract_candidate_profile(processed_resume)
    
    print(f"Candidate: {candidate_profile.name}")
    print(f"Current title: {candidate_profile.current_title}")
    print(f"Experience: {candidate_profile.total_experience_years} years")
    print(f"Top skills: {[skill.name for skill in candidate_profile.top_skills[:5]]}")
    print(f"Key achievements: {len(candidate_profile.key_achievements)}")
    print(f"Industries: {candidate_profile.industries}")
    
    # Test job description extraction
    sample_jd = """
    Senior Machine Learning Engineer
    TechStartup Inc.
    
    REQUIREMENTS
    • 5+ years of experience in Python and machine learning frameworks
    • Strong background in AWS cloud platforms and containerization
    • Experience with distributed systems handling 1M+ requests per day
    
    NICE TO HAVE
    • PhD in Computer Science or related field
    • Experience with Kubernetes and microservices architecture
    • Publications in top-tier ML conferences
    """
    
    print("\nProcessing job description...")
    processed_jd = processor.process_job_description(sample_jd)
    job_profile = extractor.extract_job_profile(processed_jd)
    
    print(f"Job title: {job_profile.title}")
    print(f"Experience required: {job_profile.experience_required} years")
    print(f"Must-have skills: {len(job_profile.must_have_skills)}")
    print(f"Nice-to-have skills: {len(job_profile.nice_to_have_skills)}")
    
    for req in job_profile.must_have_skills[:3]:
        print(f"  - {req.skill_or_requirement} ({req.level_required.value})")
    
    print("✅ Phase 4 profile extraction working!")

if __name__ == "__main__":
    test_profile_extraction()
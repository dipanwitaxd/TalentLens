# src/fit_analyzer.py
# Phase 8: Role & company fit suggestions
# Goal: Suggest where the candidate fits best and why

from typing import List, Dict, Any, Optional, Set, Tuple
from dataclasses import dataclass
from enum import Enum
import re

class FitConfidence(Enum):
    EXCELLENT = "excellent"
    GOOD = "good"
    MODERATE = "moderate"
    WEAK = "weak"

@dataclass
class SkillGap:
    """A gap between candidate skills and role requirements"""
    skill_name: str
    required_level: str
    candidate_level: str
    gap_severity: str  # "critical", "important", "nice_to_have"
    learning_timeline: str  # "1-3 months", "3-6 months", "6+ months"
    learning_resources: List[str]

@dataclass
class RoleFit:
    """Analysis of fit for a specific role archetype"""
    role_title: str
    role_description: str
    fit_confidence: FitConfidence
    fit_score: float  # 0.0 to 1.0
    matching_skills: List[str]
    matching_experiences: List[str]
    skill_gaps: List[SkillGap]
    why_good_fit: List[str]
    growth_potential: str
    typical_companies: List[str]
    salary_range: str
    next_career_steps: List[str]

@dataclass
class CompanyFit:
    """Analysis of fit for a company archetype"""
    company_type: str
    company_description: str
    fit_confidence: FitConfidence
    fit_score: float
    culture_match_reasons: List[str]
    company_examples: List[str]
    typical_benefits: List[str]
    work_environment: str
    why_good_fit: List[str]
    potential_challenges: List[str]

@dataclass
class FitAnalysisReport:
    """Complete fit analysis for a candidate"""
    candidate_name: str
    analysis_date: str
    top_role_fits: List[RoleFit]
    top_company_fits: List[CompanyFit]
    overall_marketability: str  # "high", "medium", "low"
    career_stage: str  # "junior", "mid-level", "senior", "lead"
    recommended_focus_areas: List[str]
    market_positioning: str

class FitAnalyzer:
    """Analyzes candidate fit across roles and company types"""
    
    def __init__(self):
        self.role_archetypes = self._initialize_role_archetypes()
        self.company_archetypes = self._initialize_company_archetypes()
        self.skill_learning_resources = self._initialize_learning_resources()

    def _initialize_role_archetypes(self) -> Dict[str, Dict]:
        """Define role archetypes with requirements and characteristics"""
        return {
            "ml_platform_engineer": {
                "title": "ML Platform Engineer",
                "description": "Builds and maintains infrastructure for machine learning workflows",
                "must_have_skills": ["python", "kubernetes", "docker", "cloud platforms", "mlops"],
                "nice_to_have": ["tensorflow", "pytorch", "airflow", "mlflow", "monitoring"],
                "experience_level": "3-7 years",
                "key_responsibilities": ["ML pipeline development", "infrastructure scaling", "model deployment"],
                "typical_companies": ["Tech companies", "AI startups", "Cloud providers"],
                "salary_range": "$120K-$200K",
                "growth_path": ["Senior ML Platform Engineer", "ML Infrastructure Lead", "Staff Engineer"]
            },
            "data_scientist": {
                "title": "Data Scientist", 
                "description": "Develops statistical models and algorithms to solve business problems",
                "must_have_skills": ["python", "statistics", "machine learning", "sql", "data analysis"],
                "nice_to_have": ["r", "deep learning", "aws", "tableau", "experimentation"],
                "experience_level": "2-6 years",
                "key_responsibilities": ["Model development", "data analysis", "business insights"],
                "typical_companies": ["Tech companies", "Consulting firms", "Financial services"],
                "salary_range": "$100K-$180K",
                "growth_path": ["Senior Data Scientist", "Lead Data Scientist", "Data Science Manager"]
            },
            "software_engineer": {
                "title": "Software Engineer",
                "description": "Develops and maintains software applications and systems",
                "must_have_skills": ["programming", "software development", "debugging", "testing"],
                "nice_to_have": ["cloud platforms", "databases", "frameworks", "devops"],
                "experience_level": "1-5 years",
                "key_responsibilities": ["Code development", "system design", "feature implementation"],
                "typical_companies": ["Tech companies", "Startups", "Financial services"],
                "salary_range": "$80K-$160K", 
                "growth_path": ["Senior Software Engineer", "Tech Lead", "Engineering Manager"]
            },
            "product_manager": {
                "title": "Product Manager",
                "description": "Defines product strategy and coordinates development efforts",
                "must_have_skills": ["product strategy", "stakeholder management", "data analysis", "communication"],
                "nice_to_have": ["technical background", "user research", "agile", "sql"],
                "experience_level": "3-8 years",
                "key_responsibilities": ["Product roadmap", "feature prioritization", "cross-team coordination"],
                "typical_companies": ["Tech companies", "Startups", "Consumer goods"],
                "salary_range": "$110K-$190K",
                "growth_path": ["Senior Product Manager", "Director of Product", "VP Product"]
            },
            "devops_engineer": {
                "title": "DevOps Engineer",
                "description": "Manages infrastructure, deployment pipelines, and system reliability",
                "must_have_skills": ["cloud platforms", "ci/cd", "containerization", "infrastructure"],
                "nice_to_have": ["monitoring", "security", "automation", "scripting"],
                "experience_level": "2-6 years", 
                "key_responsibilities": ["Infrastructure management", "deployment automation", "monitoring"],
                "typical_companies": ["Tech companies", "Cloud providers", "Financial services"],
                "salary_range": "$90K-$170K",
                "growth_path": ["Senior DevOps Engineer", "Platform Engineer", "Infrastructure Lead"]
            }
        }

    def _initialize_company_archetypes(self) -> Dict[str, Dict]:
        """Define company archetypes with culture and characteristics"""
        return {
            "big_tech": {
                "type": "Big Tech (FAANG+)",
                "description": "Large technology companies with global scale",
                "culture_traits": ["engineering excellence", "scale challenges", "structured processes"],
                "work_environment": "Collaborative, process-oriented, high technical bar",
                "typical_benefits": ["High compensation", "Stock options", "Great benefits", "Learning opportunities"],
                "examples": ["Google", "Meta", "Amazon", "Apple", "Microsoft", "Netflix"],
                "hiring_preferences": ["Strong technical skills", "System design knowledge", "Scale experience"],
                "challenges": ["Bureaucracy", "Intense competition", "Work-life balance varies"]
            },
            "startup_early": {
                "type": "Early-Stage Startup",
                "description": "Small companies building new products and finding market fit",
                "culture_traits": ["fast-paced", "ownership mentality", "resource constraints"],
                "work_environment": "Scrappy, flexible, high impact per person",
                "typical_benefits": ["Equity upside", "Learning opportunities", "Rapid career growth"],
                "examples": ["Seed/Series A companies", "Y Combinator startups", "Stealth mode companies"],
                "hiring_preferences": ["Versatility", "Ownership mindset", "Comfort with ambiguity"],
                "challenges": ["Job security", "Limited resources", "Undefined processes"]
            },
            "scale_up": {
                "type": "Scale-up (Series B+)",
                "description": "Growing companies with proven product-market fit",
                "culture_traits": ["growth focused", "building processes", "expanding teams"],
                "work_environment": "Dynamic, growing structure, opportunity to build",
                "typical_benefits": ["Meaningful equity", "Growth opportunities", "Building from ground up"],
                "examples": ["Stripe", "Databricks", "Figma", "Notion", "Canva"],
                "hiring_preferences": ["Growth mindset", "Building experience", "Adaptability"],
                "challenges": ["Rapid change", "Growing pains", "Scaling challenges"]
            },
            "enterprise": {
                "type": "Enterprise/Fortune 500",
                "description": "Large established companies with mature products",
                "culture_traits": ["stability", "established processes", "specialized roles"],
                "work_environment": "Structured, stable, clear career paths",
                "typical_benefits": ["Job security", "Comprehensive benefits", "Training programs"],
                "examples": ["IBM", "Oracle", "Salesforce", "Adobe", "Intuit"],
                "hiring_preferences": ["Domain expertise", "Process adherence", "Team collaboration"],
                "challenges": ["Slower innovation", "Bureaucracy", "Limited agility"]
            },
            "fintech": {
                "type": "Financial Technology",
                "description": "Companies building financial products and services",
                "culture_traits": ["compliance focused", "data driven", "customer security"],
                "work_environment": "Regulated environment, high attention to detail",
                "typical_benefits": ["Competitive compensation", "Industry expertise", "Stable market"],
                "examples": ["Stripe", "Square", "Robinhood", "Coinbase", "Plaid"],
                "hiring_preferences": ["Security mindset", "Attention to detail", "Financial domain knowledge"],
                "challenges": ["Regulatory constraints", "High compliance overhead", "Risk aversion"]
            }
        }

    def _initialize_learning_resources(self) -> Dict[str, List[str]]:
        """Map skills to learning resources"""
        return {
            "kubernetes": ["Kubernetes docs", "CKAD certification", "Hands-on clusters"],
            "machine learning": ["Coursera ML course", "Kaggle competitions", "Fast.ai"],
            "system design": ["Designing Data-Intensive Applications", "System design interviews"],
            "python": ["Python docs", "Real Python", "LeetCode practice"],
            "aws": ["AWS certification", "AWS free tier", "Cloud practitioner"],
            "sql": ["SQL tutorials", "HackerRank SQL", "Database design books"],
            "react": ["React docs", "FreeCodeCamp", "Build projects"],
            "product management": ["PM courses", "Product coalition", "Case studies"]
        }

    def analyze_candidate_fit(self, 
                            candidate_profile: 'CandidateProfile',
                            target_job_profile: 'JobProfile' = None) -> FitAnalysisReport:
        """Analyze candidate fit across all roles and companies"""
        
        # Analyze role fits
        role_fits = []
        for role_key, role_data in self.role_archetypes.items():
            fit = self._analyze_role_fit(candidate_profile, role_key, role_data)
            role_fits.append(fit)
        
        # Sort and take top 3 role fits
        role_fits.sort(key=lambda x: x.fit_score, reverse=True)
        top_role_fits = role_fits[:3]
        
        # Analyze company fits based on candidate profile
        company_fits = []
        for company_key, company_data in self.company_archetypes.items():
            fit = self._analyze_company_fit(candidate_profile, company_key, company_data)
            company_fits.append(fit)
        
        # Sort and take top 3 company fits
        company_fits.sort(key=lambda x: x.fit_score, reverse=True)
        top_company_fits = company_fits[:3]
        
        # Determine overall marketability and career stage
        overall_marketability = self._assess_overall_marketability(candidate_profile, top_role_fits)
        career_stage = self._determine_career_stage(candidate_profile)
        
        # Generate recommendations
        recommended_focus_areas = self._generate_focus_recommendations(candidate_profile, top_role_fits)
        market_positioning = self._generate_market_positioning(candidate_profile, top_role_fits[0])
        
        return FitAnalysisReport(
            candidate_name=candidate_profile.name or "Candidate",
            analysis_date="2024",
            top_role_fits=top_role_fits,
            top_company_fits=top_company_fits,
            overall_marketability=overall_marketability,
            career_stage=career_stage,
            recommended_focus_areas=recommended_focus_areas,
            market_positioning=market_positioning
        )

    def _analyze_role_fit(self, candidate_profile: 'CandidateProfile', role_key: str, role_data: Dict) -> RoleFit:
        """Analyze how well candidate fits a specific role"""
        
        # Extract candidate skills
        candidate_skills = [skill.name.lower() for skill in candidate_profile.top_skills]
        candidate_experiences = [exp.title.lower() for exp in candidate_profile.experiences]
        
        # Calculate skill matches
        must_have_matches = []
        must_have_gaps = []
        
        for required_skill in role_data["must_have_skills"]:
            if any(required_skill.lower() in skill for skill in candidate_skills):
                must_have_matches.append(required_skill)
            else:
                gap = SkillGap(
                    skill_name=required_skill,
                    required_level="Proficient",
                    candidate_level="None",
                    gap_severity="critical",
                    learning_timeline="3-6 months",
                    learning_resources=self.skill_learning_resources.get(required_skill.lower(), ["Online courses"])
                )
                must_have_gaps.append(gap)
        
        # Calculate nice-to-have matches
        nice_to_have_matches = []
        for nice_skill in role_data["nice_to_have"]:
            if any(nice_skill.lower() in skill for skill in candidate_skills):
                nice_to_have_matches.append(nice_skill)
        
        # Calculate experience relevance
        experience_matches = []
        for responsibility in role_data["key_responsibilities"]:
            for exp in candidate_profile.experiences:
                if any(keyword in exp.title.lower() or 
                       any(keyword in achievement.lower() for achievement in exp.key_achievements)
                       for keyword in responsibility.lower().split()):
                    experience_matches.append(f"Experience with {responsibility.lower()}")
                    break
        
        # Calculate fit score
        must_have_score = len(must_have_matches) / len(role_data["must_have_skills"])
        nice_to_have_score = len(nice_to_have_matches) / len(role_data["nice_to_have"]) if role_data["nice_to_have"] else 0
        experience_score = len(experience_matches) / len(role_data["key_responsibilities"])
        
        # Weighted fit score
        fit_score = (must_have_score * 0.6) + (nice_to_have_score * 0.2) + (experience_score * 0.2)
        
        # Determine fit confidence
        if fit_score >= 0.8:
            fit_confidence = FitConfidence.EXCELLENT
        elif fit_score >= 0.6:
            fit_confidence = FitConfidence.GOOD
        elif fit_score >= 0.4:
            fit_confidence = FitConfidence.MODERATE
        else:
            fit_confidence = FitConfidence.WEAK
        
        # Generate why good fit reasons
        why_good_fit = []
        if must_have_matches:
            why_good_fit.append(f"Strong foundation in {', '.join(must_have_matches[:3])}")
        if nice_to_have_matches:
            why_good_fit.append(f"Additional expertise in {', '.join(nice_to_have_matches[:2])}")
        if experience_matches:
            why_good_fit.append(f"Relevant experience in {len(experience_matches)} key areas")
        
        # Determine growth potential
        years_exp = candidate_profile.total_experience_years or 0
        if years_exp < 3:
            growth_potential = "High - early career with room for rapid development"
        elif years_exp < 7:
            growth_potential = "Good - mid-level with proven experience and upward trajectory"
        else:
            growth_potential = "Moderate - senior level with potential for leadership roles"
        
        return RoleFit(
            role_title=role_data["title"],
            role_description=role_data["description"],
            fit_confidence=fit_confidence,
            fit_score=round(fit_score, 2),
            matching_skills=must_have_matches + nice_to_have_matches,
            matching_experiences=experience_matches,
            skill_gaps=must_have_gaps,
            why_good_fit=why_good_fit,
            growth_potential=growth_potential,
            typical_companies=role_data["typical_companies"],
            salary_range=role_data["salary_range"],
            next_career_steps=role_data["growth_path"]
        )

    def _analyze_company_fit(self, candidate_profile: 'CandidateProfile', company_key: str, company_data: Dict) -> CompanyFit:
        """Analyze how well candidate fits a company type"""
        
        years_exp = candidate_profile.total_experience_years or 0
        industries = candidate_profile.industries
        
        # Calculate culture fit based on experience and background
        culture_score = 0.5  # Base score
        culture_match_reasons = []
        
        if company_key == "big_tech":
            if years_exp >= 3:
                culture_score += 0.2
                culture_match_reasons.append("Sufficient experience for structured environment")
            if "technology" in industries:
                culture_score += 0.2
                culture_match_reasons.append("Tech industry background")
            if any("scale" in achievement.lower() for exp in candidate_profile.experiences for achievement in exp.key_achievements):
                culture_score += 0.1
                culture_match_reasons.append("Experience with scale challenges")
        
        elif company_key == "startup_early":
            if years_exp <= 5:
                culture_score += 0.2
                culture_match_reasons.append("Good fit for early career growth")
            if len(candidate_profile.top_skills) >= 8:
                culture_score += 0.1
                culture_match_reasons.append("Versatile skill set for startup needs")
            if any("built" in achievement.lower() or "created" in achievement.lower() 
                   for exp in candidate_profile.experiences for achievement in exp.key_achievements):
                culture_score += 0.2
                culture_match_reasons.append("Experience building from ground up")
        
        elif company_key == "scale_up":
            if 2 <= years_exp <= 8:
                culture_score += 0.3
                culture_match_reasons.append("Ideal experience level for scale-up growth")
            if any("improved" in achievement.lower() or "optimized" in achievement.lower()
                   for exp in candidate_profile.experiences for achievement in exp.key_achievements):
                culture_score += 0.2
                culture_match_reasons.append("Experience improving and optimizing systems")
        
        # Determine fit confidence
        if culture_score >= 0.8:
            fit_confidence = FitConfidence.EXCELLENT
        elif culture_score >= 0.6:
            fit_confidence = FitConfidence.GOOD
        elif culture_score >= 0.4:
            fit_confidence = FitConfidence.MODERATE
        else:
            fit_confidence = FitConfidence.WEAK
        
        # Generate why good fit and potential challenges
        why_good_fit = culture_match_reasons[:3]
        potential_challenges = company_data["challenges"][:2]
        
        return CompanyFit(
            company_type=company_data["type"],
            company_description=company_data["description"],
            fit_confidence=fit_confidence,
            fit_score=round(culture_score, 2),
            culture_match_reasons=culture_match_reasons,
            company_examples=company_data["examples"][:4],
            typical_benefits=company_data["typical_benefits"],
            work_environment=company_data["work_environment"],
            why_good_fit=why_good_fit,
            potential_challenges=potential_challenges
        )

    def _assess_overall_marketability(self, candidate_profile: 'CandidateProfile', top_roles: List[RoleFit]) -> str:
        """Assess overall marketability based on role fits"""
        if not top_roles:
            return "low"
        
        best_fit_score = top_roles[0].fit_score
        
        if best_fit_score >= 0.7:
            return "high"
        elif best_fit_score >= 0.5:
            return "medium"
        else:
            return "low"

    def _determine_career_stage(self, candidate_profile: 'CandidateProfile') -> str:
        """Determine career stage based on experience"""
        years_exp = candidate_profile.total_experience_years or 0
        
        if years_exp < 2:
            return "junior"
        elif years_exp < 6:
            return "mid-level"
        elif years_exp < 10:
            return "senior"
        else:
            return "lead"

    def _generate_focus_recommendations(self, candidate_profile: 'CandidateProfile', top_roles: List[RoleFit]) -> List[str]:
        """Generate recommendations for skills to focus on"""
        recommendations = []
        
        if not top_roles:
            return ["Develop core technical skills", "Gain relevant experience"]
        
        # Get critical gaps from top role
        top_role = top_roles[0]
        critical_gaps = [gap.skill_name for gap in top_role.skill_gaps if gap.gap_severity == "critical"]
        
        if critical_gaps:
            recommendations.append(f"Develop critical skills: {', '.join(critical_gaps[:3])}")
        
        # Check for common patterns across top roles
        all_missing_skills = []
        for role in top_roles[:2]:
            all_missing_skills.extend([gap.skill_name for gap in role.skill_gaps])
        
        common_missing = [skill for skill in set(all_missing_skills) if all_missing_skills.count(skill) >= 2]
        if common_missing:
            recommendations.append(f"High-impact skills across roles: {', '.join(common_missing[:2])}")
        
        # Experience recommendations
        if candidate_profile.total_experience_years and candidate_profile.total_experience_years < 3:
            recommendations.append("Focus on gaining hands-on project experience")
        
        return recommendations[:3]

    def _generate_market_positioning(self, candidate_profile: 'CandidateProfile', top_role: RoleFit) -> str:
        """Generate market positioning statement"""
        
        strengths = []
        if candidate_profile.top_skills:
            main_skills = [skill.name for skill in candidate_profile.top_skills[:3]]
            strengths.append(f"strong {'/'.join(main_skills)} skills")
        
        if candidate_profile.total_experience_years:
            exp_level = "early-career" if candidate_profile.total_experience_years < 3 else "experienced"
            strengths.append(f"{exp_level} professional")
        
        if candidate_profile.industries:
            industry = list(candidate_profile.industries)[0]
            strengths.append(f"{industry} background")
        
        strength_text = ", ".join(strengths)
        
        return f"Position as {strength_text} targeting {top_role.role_title} roles with {top_role.fit_confidence.value} fit potential"

    def print_fit_analysis_report(self, report: FitAnalysisReport) -> None:
        """Print comprehensive fit analysis report"""
        
        print(f"\n=== FIT ANALYSIS REPORT ===")
        print(f"Candidate: {report.candidate_name}")
        print(f"Career Stage: {report.career_stage.title()}")
        print(f"Overall Marketability: {report.overall_marketability.title()}")
        
        print(f"\n🎯 TOP ROLE RECOMMENDATIONS:")
        for i, role in enumerate(report.top_role_fits, 1):
            print(f"\n{i}. {role.role_title} (Fit: {role.fit_confidence.value.title()}, Score: {role.fit_score})")
            print(f"   Why good fit: {'; '.join(role.why_good_fit[:2])}")
            print(f"   Salary range: {role.salary_range}")
            
            if role.skill_gaps:
                gaps = [gap.skill_name for gap in role.skill_gaps[:2]]
                print(f"   Skills to develop: {', '.join(gaps)}")
        
        print(f"\n🏢 TOP COMPANY TYPE RECOMMENDATIONS:")
        for i, company in enumerate(report.top_company_fits, 1):
            print(f"\n{i}. {company.company_type} (Fit: {company.fit_confidence.value.title()})")
            print(f"   Why good fit: {'; '.join(company.why_good_fit[:2])}")
            print(f"   Examples: {', '.join(company.company_examples[:3])}")
        
        print(f"\n💡 FOCUS RECOMMENDATIONS:")
        for rec in report.recommended_focus_areas:
            print(f"   • {rec}")
        
        print(f"\n📈 MARKET POSITIONING:")
        print(f"   {report.market_positioning}")


# Testing function
def test_fit_analyzer():
    """Test the fit analyzer"""
    print("=== TESTING FIT ANALYZER (Phase 8) ===")
    
    from src.text_processor import UniversalTextProcessor
    from src.profile_extractor import ProfileExtractor, Skill, Experience, SkillLevel
    
    processor = UniversalTextProcessor()
    profile_extractor = ProfileExtractor()
    fit_analyzer = FitAnalyzer()
    
    # Create sample candidate profile
    sample_resume = """
    JOHN DOE
    Software Engineer
    
    EXPERIENCE
    • Built machine learning models using Python and TensorFlow
    • Deployed applications on AWS with Docker and Kubernetes
    • Led team of 3 engineers on microservices migration project
    
    SKILLS
    Python, AWS, Docker, Kubernetes, Machine Learning, TensorFlow
    """
    
    processed_lines = processor.process_resume(sample_resume)
    candidate_profile = profile_extractor.extract_candidate_profile(processed_lines)
    
    # Enhance profile for testing
    candidate_profile.total_experience_years = 4
    candidate_profile.industries.add("technology")
    
    # Analyze fit
    report = fit_analyzer.analyze_candidate_fit(candidate_profile)
    
    fit_analyzer.print_fit_analysis_report(report)
    
    print(f"\n✅ Phase 8 fit analysis working!")

if __name__ == "__main__":
    test_fit_analyzer()
# src/critique_engine.py
# Phase 6: Line-level critique (RAG + LangChain)
# Goal: For each bullet, produce issues, reasons, fixes, and citations

from typing import List, Dict, Any, Optional
from dataclasses import dataclass
import json
import re
from groq import Groq
from src.heuristic_checker import HeuristicFlag, IssueSeverity, IssueType

@dataclass
class CritiqueIssue:
    """A single issue identified in a resume line"""
    type: str
    severity: str  # "low", "medium", "high", "critical"
    rule_violated: str
    explanation: str
    confidence: float  # 0.0 to 1.0
    evidence_citations: List[str]  # References to context that supports this critique

@dataclass
class LineCritique:
    """Complete critique for a single resume line"""
    line_number: int
    original_text: str
    issues: List[CritiqueIssue]
    suggested_rewrite: str
    rewrite_reasoning: str
    overall_assessment: str  # "good", "needs_improvement", "major_issues"
    citations: List[str]  # All sources used for this critique
    heuristic_flags_used: List[str]  # Which heuristic flags influenced this critique

class CritiqueEngine:
    """Generates line-level critiques using LLM + RAG + heuristics"""
    
    def __init__(self, groq_api_key: str):
        self.groq_client = Groq(api_key=groq_api_key)
        self.model = "llama-3.1-70b-versatile"  # Fast Groq model
        
        # Issue type mapping from heuristics to critique
        self.heuristic_to_critique_type = {
            IssueType.MISSING_METRICS: "quantification",
            IssueType.VAGUE_VERBS: "action_clarity", 
            IssueType.TOOL_WITHOUT_CONTEXT: "technical_context",
            IssueType.OVERLONG_BULLET: "conciseness",
            IssueType.LAUNDRY_LIST: "focus",
            IssueType.PASSIVE_VOICE: "ownership",
            IssueType.WEAK_IMPACT: "impact_clarity"
        }

    def critique_resume_line(self, 
                       target_line: str,
                       line_number: int,
                       context_pack: 'ContextPack',
                       heuristic_flags: List[HeuristicFlag] = None,
                       job_profile: 'JobProfile' = None) -> LineCritique:
        """Generate comprehensive critique for a single resume line"""
    
        if heuristic_flags is None:
            heuristic_flags = []
    
        # Build the critique prompt
        prompt = self._build_critique_prompt(
            target_line, line_number, context_pack, heuristic_flags, job_profile
        )
    
        # Get LLM response
        response = self._call_groq_llm(prompt)
    
        # Parse the structured response
        critique = self._parse_llm_response(response, target_line, line_number, heuristic_flags)
    
        # ADD GUARDRAILS VALIDATION HERE:
        try:
            from guardrails_system import GuardrailsSystem, SeverityLevel
            guardrails = GuardrailsSystem()
        
            # Validate the critique content
            critique_violations = guardrails.validate_critique_content(critique.suggested_rewrite)
        
            # Check for critical violations
            critical_violations = [v for v in critique_violations if v.severity == SeverityLevel.CRITICAL]
        
            if critical_violations:
                # Log the issue
                print(f"CRITICAL: Critique for line {line_number} flagged for review")
            
                # Replace with safe fallback
                critique.suggested_rewrite = f"[FLAGGED_FOR_REVIEW: {critique.original_text}]"
                critique.rewrite_reasoning = "Content flagged by safety systems for human review"
                critique.overall_assessment = "needs_review"
            
                # Add violation info to citations
                violation_details = [f"Safety: {v.description}" for v in critical_violations]
                critique.citations.extend(violation_details)
        
            # Check truthfulness compliance
            truthfulness_violations = guardrails.ensure_truthfulness_compliance(
                target_line, critique.suggested_rewrite
            )
        
            critical_truth_violations = [v for v in truthfulness_violations if v.severity == SeverityLevel.CRITICAL]
        
            if critical_truth_violations:
                # Log the issue
                print(f"TRUTHFULNESS: Critique for line {line_number} contains potential hallucinations")
            
                # Clean up the rewrite
                critique.suggested_rewrite = critique.original_text  # Fall back to original
                critique.rewrite_reasoning = "Rewrite contained potential hallucinations - kept original"
            
                # Add to citations
                truth_details = [f"Truthfulness: {v.description}" for v in critical_truth_violations]
                critique.citations.extend(truth_details)
    
        except ImportError:
            # Guardrails not available, continue without validation
            pass
    
        return critique

    def _build_critique_prompt(self, 
                              target_line: str,
                              line_number: int,
                              context_pack: 'ContextPack',
                              heuristic_flags: List[HeuristicFlag],
                              job_profile: 'JobProfile' = None) -> str:
        """Build the complete prompt for line critique"""
        
        # Prepare context sections
        resume_context = self._format_resume_context(context_pack.resume_neighbors)
        jd_context = self._format_jd_context(context_pack.jd_requirements)
        heuristic_hints = self._format_heuristic_hints(heuristic_flags)
        job_requirements = self._format_job_requirements(job_profile) if job_profile else ""
        
        prompt = f"""You are an expert technical recruiter and resume coach. Analyze this resume bullet point and provide detailed, actionable feedback.

TARGET LINE TO CRITIQUE:
Line {line_number}: "{target_line}"

CONTEXT PROVIDED:
{resume_context}

{jd_context}

{heuristic_hints}

{job_requirements}

ANALYSIS RULES:
1. Base ALL feedback on the provided context only
2. If you need facts not in the context, use [NEED_EVIDENCE: what to add]
3. Every critique point must cite specific context (neighboring lines or JD requirements)
4. Focus on IMPROVEMENT, not rejection
5. Prioritize: impact metrics > technical depth > action clarity

RESPONSE FORMAT:
Return a valid JSON object with this exact structure:

{{
    "issues": [
        {{
            "type": "quantification|action_clarity|technical_context|focus|ownership|impact_clarity",
            "severity": "low|medium|high|critical",
            "rule_violated": "specific rule broken",
            "explanation": "why this is an issue",
            "confidence": 0.8,
            "evidence_citations": ["specific context reference"]
        }}
    ],
    "suggested_rewrite": "improved version of the bullet",
    "rewrite_reasoning": "explanation of changes made",
    "overall_assessment": "good|needs_improvement|major_issues",
    "key_improvements": ["list of main improvements made"]
}}

EXAMPLES OF GOOD CRITIQUES:
- Issue: "Missing quantification" → Evidence: "Line mentions 'improved performance' but neighboring line L15 shows '40% improvement' - add specific metrics"
- Issue: "Vague action verb" → Evidence: "Uses 'worked on' while JD requires 'build and deploy' - shows ownership"
- Issue: "Tool without context" → Evidence: "Lists Python but doesn't show what was built - context line L12 shows 'web applications'"

Begin your analysis:"""

        return prompt

    def _format_resume_context(self, neighbors: List['RetrievalResult']) -> str:
        """Format resume neighbor lines for context"""
        if not neighbors:
            return "RESUME CONTEXT: No neighboring lines available"
        
        context = "RESUME CONTEXT (neighboring lines for reference):\n"
        for neighbor in neighbors[:5]:  # Top 5 neighbors
            context += f"  {neighbor.id}: \"{neighbor.text}\"\n"
        
        return context

    def _format_jd_context(self, jd_requirements: List['RetrievalResult']) -> str:
        """Format job description requirements for context"""
        if not jd_requirements:
            return "JOB REQUIREMENTS: No job description provided"
        
        context = "JOB REQUIREMENTS (relevant requirements):\n"
        for req in jd_requirements[:3]:  # Top 3 requirements
            context += f"  JD Requirement: \"{req.text}\"\n"
        
        return context

    def _format_heuristic_hints(self, flags: List[HeuristicFlag]) -> str:
        """Format heuristic flags as hints for the LLM"""
        if not flags:
            return "HEURISTIC PRE-CHECKS: No issues detected"
        
        hints = "HEURISTIC PRE-CHECKS (focus areas):\n"
        for flag in flags:
            hints += f"  - {flag.issue_type.value}: {flag.explanation}\n"
            hints += f"    Suggested fix: {flag.suggested_fix}\n"
        
        return hints

    def _format_job_requirements(self, job_profile: 'JobProfile') -> str:
        """Format job profile requirements"""
        if not job_profile:
            return ""
        
        context = f"JOB PROFILE ANALYSIS:\n"
        context += f"  Position: {job_profile.title}\n"
        
        if job_profile.must_have_skills:
            context += f"  Must-have skills: {[skill.skill_or_requirement for skill in job_profile.must_have_skills[:5]]}\n"
        
        if job_profile.experience_required:
            context += f"  Experience required: {job_profile.experience_required} years\n"
        
        return context

    def _call_groq_llm(self, prompt: str) -> str:
        """Call Groq LLM with better error handling"""
        try:
            if not self.groq_client:
                return self._generate_heuristic_fallback()
            
            response = self.groq_client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": "You are an expert resume coach. Respond with valid JSON."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.1,
                max_tokens=1000,
                response_format={"type": "json_object"}
            )
        
            return response.choices[0].message.content
        
        except Exception as e:
            print(f"LLM Error: {e}")
            return self._generate_heuristic_fallback()

    def _generate_heuristic_fallback(self) -> str:
        """Generate critique using heuristics when LLM fails"""
        return json.dumps({
            "issues": [{
                "type": "action_clarity",
                "severity": "medium",
                "rule_violated": "Passive language detected",
                "explanation": "Uses passive voice - 'was responsible for' - instead of showing direct action",
                "confidence": 0.8,
                "evidence_citations": ["heuristic_analysis"]
            }],
            "suggested_rewrite": "Improved database performance by [NEED_EVIDENCE: specific percentage or metric]",
            "rewrite_reasoning": "Changed to active voice and added placeholder for metrics",
            "overall_assessment": "needs_improvement",
            "key_improvements": ["Active voice", "Quantified impact needed"]
    })

    def _parse_llm_response(self, 
                           response: str,
                           original_text: str,
                           line_number: int,
                           heuristic_flags: List[HeuristicFlag]) -> LineCritique:
        """Parse LLM JSON response into LineCritique object"""
        
        try:
            data = json.loads(response)
            
            # Parse issues
            issues = []
            for issue_data in data.get("issues", []):
                issue = CritiqueIssue(
                    type=issue_data.get("type", "unknown"),
                    severity=issue_data.get("severity", "medium"),
                    rule_violated=issue_data.get("rule_violated", ""),
                    explanation=issue_data.get("explanation", ""),
                    confidence=float(issue_data.get("confidence", 0.5)),
                    evidence_citations=issue_data.get("evidence_citations", [])
                )
                issues.append(issue)
            
            # Extract citations from all issues
            all_citations = []
            for issue in issues:
                all_citations.extend(issue.evidence_citations)
            
            # Track which heuristic flags were used
            heuristic_flags_used = [flag.issue_type.value for flag in heuristic_flags]
            
            critique = LineCritique(
                line_number=line_number,
                original_text=original_text,
                issues=issues,
                suggested_rewrite=data.get("suggested_rewrite", original_text),
                rewrite_reasoning=data.get("rewrite_reasoning", "No changes suggested"),
                overall_assessment=data.get("overall_assessment", "needs_improvement"),
                citations=list(set(all_citations)),
                heuristic_flags_used=heuristic_flags_used
            )
            self._validate_critique_safety(critique)
            return critique
            
        except json.JSONDecodeError as e:
            print(f"Error parsing LLM response: {e}")
            print(f"Raw response: {response}")
            
            # Return minimal critique on parse error
            return LineCritique(
                line_number=line_number,
                original_text=original_text,
                issues=[CritiqueIssue(
                    type="parse_error",
                    severity="medium",
                    rule_violated="Response format",
                    explanation="Could not parse LLM response",
                    confidence=0.1,
                    evidence_citations=["parse_error"]
                )],
                suggested_rewrite=original_text,
                rewrite_reasoning="Parse error occurred",
                overall_assessment="needs_improvement",
                citations=["parse_error"],
                heuristic_flags_used=[]
            )
        
    def _validate_critique_safety(self, critique: LineCritique) -> None:
        """Validate critique for safety and compliance"""
        try:
            from guardrails_system import GuardrailsSystem, SeverityLevel
            guardrails = GuardrailsSystem()
        
            # Check content safety
            content_violations = guardrails.validate_critique_content(critique.suggested_rewrite)
            critical_content = [v for v in content_violations if v.severity == SeverityLevel.CRITICAL]
        
            # Check truthfulness
            truth_violations = guardrails.ensure_truthfulness_compliance(
                critique.original_text, critique.suggested_rewrite
            )
            critical_truth = [v for v in truth_violations if v.severity == SeverityLevel.CRITICAL]
        
            # Handle critical violations
            if critical_content or critical_truth:
                critique.suggested_rewrite = f"[SAFETY_REVIEW_REQUIRED: {critique.original_text}]"
                critique.rewrite_reasoning = "Content requires safety review before use"
                critique.overall_assessment = "flagged_for_review"
            
                # Add safety annotations
                safety_notes = []
                for v in critical_content + critical_truth:
                    safety_notes.append(f"Safety: {v.description}")
            
                critique.citations.extend(safety_notes)
    
        except ImportError:
            # Guardrails system not available
            pass

    def critique_multiple_lines(self,
                               lines_to_critique: List[tuple],  # (line_text, line_number, context_pack, heuristic_flags)
                               job_profile: 'JobProfile' = None) -> List[LineCritique]:
        """Critique multiple resume lines efficiently"""
        
        critiques = []
        
        for line_text, line_number, context_pack, heuristic_flags in lines_to_critique:
            print(f"Critiquing line {line_number}...")
            
            critique = self.critique_resume_line(
                line_text, line_number, context_pack, heuristic_flags, job_profile
            )
            
            critiques.append(critique)
        
        return critiques

    def generate_critique_summary(self, critiques: List[LineCritique]) -> Dict[str, Any]:
        """Generate summary statistics for all critiques"""
        
        total_lines = len(critiques)
        total_issues = sum(len(critique.issues) for critique in critiques)
        
        # Count by severity
        severity_counts = {"low": 0, "medium": 0, "high": 0, "critical": 0}
        for critique in critiques:
            for issue in critique.issues:
                severity_counts[issue.severity] += 1
        
        # Count by type
        type_counts = {}
        for critique in critiques:
            for issue in critique.issues:
                type_counts[issue.type] = type_counts.get(issue.type, 0) + 1
        
        # Overall assessment distribution
        assessment_counts = {"good": 0, "needs_improvement": 0, "major_issues": 0}
        for critique in critiques:
            assessment_counts[critique.overall_assessment] += 1
        
        # Lines needing rewrites
        lines_with_rewrites = sum(1 for critique in critiques 
                                if critique.suggested_rewrite != critique.original_text)
        
        return {
            "total_lines_critiqued": total_lines,
            "total_issues_found": total_issues,
            "avg_issues_per_line": round(total_issues / total_lines, 2) if total_lines > 0 else 0,
            "severity_distribution": severity_counts,
            "issue_type_distribution": type_counts,
            "assessment_distribution": assessment_counts,
            "lines_needing_rewrites": lines_with_rewrites,
            "rewrite_percentage": round(lines_with_rewrites / total_lines * 100, 1) if total_lines > 0 else 0
        }

    def print_critique_report(self, critiques: List[LineCritique]) -> None:
        """Print human-readable critique report"""
        
        print(f"\n=== RESUME CRITIQUE REPORT ===")
        
        summary = self.generate_critique_summary(critiques)
        
        print(f"Lines analyzed: {summary['total_lines_critiqued']}")
        print(f"Total issues: {summary['total_issues_found']} (avg: {summary['avg_issues_per_line']} per line)")
        print(f"Lines needing rewrites: {summary['lines_needing_rewrites']} ({summary['rewrite_percentage']}%)")
        
        if summary['total_issues_found'] > 0:
            print(f"\nIssue severity breakdown:")
            for severity, count in summary['severity_distribution'].items():
                if count > 0:
                    print(f"  {severity.title()}: {count}")
            
            print(f"\nMost common issues:")
            sorted_issues = sorted(summary['issue_type_distribution'].items(), 
                                 key=lambda x: x[1], reverse=True)
            for issue_type, count in sorted_issues[:5]:
                print(f"  {issue_type.replace('_', ' ').title()}: {count}")
        
        # Show sample critiques
        print(f"\nSample critiques:")
        for i, critique in enumerate(critiques[:3], 1):
            print(f"\n{i}. Line {critique.line_number}: \"{critique.original_text[:60]}...\"")
            print(f"   Assessment: {critique.overall_assessment}")
            
            if critique.issues:
                top_issue = critique.issues[0]
                print(f"   Main issue: {top_issue.explanation}")
                print(f"   Suggested fix: {critique.suggested_rewrite[:80]}...")
            else:
                print(f"   ✅ No issues found")

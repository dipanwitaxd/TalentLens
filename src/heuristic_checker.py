# src/heuristic_checker.py
# Phase 5: Heuristic pre-checks
# Goal: Cheap signals to boost precision before the LLM

from typing import List, Dict, Any, Set, Optional
from dataclasses import dataclass
from enum import Enum
import re
from datetime import datetime

class IssueType(Enum):
    MISSING_METRICS = "missing_metrics"
    VAGUE_VERBS = "vague_verbs"
    TOOL_WITHOUT_CONTEXT = "tool_without_context"
    OVERLONG_BULLET = "overlong_bullet"
    LAUNDRY_LIST = "laundry_list"
    STALE_TECH = "stale_tech"
    DATE_OVERLAP = "date_overlap"
    PASSIVE_VOICE = "passive_voice"
    WEAK_IMPACT = "weak_impact"
    TYPOS_GRAMMAR = "typos_grammar"

class IssueSeverity(Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"

@dataclass
class HeuristicFlag:
    """A single heuristic flag for a resume line"""
    issue_type: IssueType
    severity: IssueSeverity
    confidence: float  # 0.0 to 1.0
    explanation: str
    suggested_fix: str
    line_number: int
    examples: List[str] = None
    
    def __post_init__(self):
        if self.examples is None:
            self.examples = []

@dataclass
class HeuristicReport:
    """Summary of all heuristic checks for a resume"""
    total_lines_checked: int
    total_flags: int
    flags_by_type: Dict[IssueType, int]
    flags_by_severity: Dict[IssueSeverity, int]
    line_flags: Dict[int, List[HeuristicFlag]]
    overall_score: float  # 0.0 to 1.0 (higher is better)

class HeuristicChecker:
    """Performs heuristic checks on resume lines before LLM processing"""
    
    def __init__(self):
        # Weak action verbs that should be flagged
        self.weak_verbs = {
            "worked on", "helped with", "assisted", "involved in", "responsible for",
            "duties included", "participated in", "contributed to", "engaged in",
            "supported", "handled", "dealt with", "took part in", "was part of"
        }
        
        # Strong action verbs for suggestions
        self.strong_verbs = {
            "built", "created", "developed", "designed", "implemented", "launched",
            "led", "managed", "optimized", "improved", "increased", "reduced",
            "delivered", "achieved", "established", "transformed", "streamlined"
        }
        
        # Technology/tools that might be outdated
        self.stale_technologies = {
            "flash", "silverlight", "internet explorer", "ie6", "ie7", "ie8",
            "visual basic 6", "perl", "cobol", "fortran", "actionscript",
            "jquery 1.x", "angular 1", "angularjs", "backbone.js"
        }
        
        # Modern technology alternatives
        self.modern_alternatives = {
            "jquery": "React/Vue/Angular",
            "angularjs": "Angular (2+)",
            "flash": "HTML5/CSS3",
            "silverlight": "HTML5/CSS3"
        }
        
        # Common typos and grammar issues
        self.common_typos = {
            "recieve": "receive",
            "seperate": "separate",
            "definately": "definitely",
            "occured": "occurred",
            "managment": "management",
            "develpment": "development",
            "sucessful": "successful"
        }
        
        # Metrics indicators
        self.metric_indicators = [
            r'\d+%', r'\$[\d,]+[KMB]?', r'\d+[KMB]?\+?\s*(users?|customers?|clients?)',
            r'\d+\s*(years?|months?|weeks?)', r'\d+x\s*(faster|improvement)',
            r'\d+[KMB]?\s*(revenue|sales|leads)', r'\d+:\d+\s*(ratio|improvement)'
        ]
        
        # Impact words that should have metrics
        self.impact_words_needing_metrics = [
            "improved", "increased", "reduced", "optimized", "enhanced",
            "boosted", "accelerated", "streamlined", "minimized", "maximized"
        ]

    def check_resume_lines(self, processed_lines: List['ProcessedLine']) -> HeuristicReport:
        """Run all heuristic checks on resume lines"""
        
        line_flags = {}
        flags_by_type = {issue_type: 0 for issue_type in IssueType}
        flags_by_severity = {severity: 0 for severity in IssueSeverity}
        
        total_lines_checked = 0
        
        for line in processed_lines:
            # Only check meaningful content lines
            if self._should_check_line(line):
                total_lines_checked += 1
                line_flags[line.line_number] = []
                
                # Run all heuristic checks
                flags = self._check_single_line(line)
                
                for flag in flags:
                    line_flags[line.line_number].append(flag)
                    flags_by_type[flag.issue_type] += 1
                    flags_by_severity[flag.severity] += 1
        
        # Calculate overall score
        total_flags = sum(flags_by_type.values())
        overall_score = self._calculate_overall_score(total_flags, total_lines_checked, flags_by_severity)
        
        return HeuristicReport(
            total_lines_checked=total_lines_checked,
            total_flags=total_flags,
            flags_by_type=flags_by_type,
            flags_by_severity=flags_by_severity,
            line_flags=line_flags,
            overall_score=overall_score
        )

    def _should_check_line(self, line: 'ProcessedLine') -> bool:
        """Determine if line should be checked"""
        # Skip contact info and very short lines
        if line.section.value == "contact" or len(line.text.strip()) < 15:
            return False
        
        # Focus on experience and project bullets
        if line.section.value in ["experience", "projects"] and line.is_bullet:
            return True
        
        # Also check skills if they're in bullet format
        if line.section.value == "skills" and line.is_bullet:
            return True
        
        return False

    def _check_single_line(self, line: 'ProcessedLine') -> List[HeuristicFlag]:
        """Run all checks on a single line"""
        flags = []
        
        # Check for missing metrics
        flags.extend(self._check_missing_metrics(line))
        
        # Check for vague verbs
        flags.extend(self._check_vague_verbs(line))
        
        # Check for tools without context
        flags.extend(self._check_tool_without_context(line))
        
        # Check line length
        flags.extend(self._check_overlong_bullet(line))
        
        # Check for laundry list
        flags.extend(self._check_laundry_list(line))
        
        # Check for stale technology
        flags.extend(self._check_stale_tech(line))
        
        # Check for passive voice
        flags.extend(self._check_passive_voice(line))
        
        # Check for weak impact statements
        flags.extend(self._check_weak_impact(line))
        
        # Check for typos and grammar
        flags.extend(self._check_typos_grammar(line))
        
        return flags

    def _check_missing_metrics(self, line: 'ProcessedLine') -> List[HeuristicFlag]:
        """Check if line has impact words but no metrics"""
        flags = []
        text_lower = line.text.lower()
        
        # Check if line has impact words
        has_impact_words = any(word in text_lower for word in self.impact_words_needing_metrics)
        
        # Check if line has any metrics
        has_metrics = any(re.search(pattern, line.text) for pattern in self.metric_indicators)
        
        if has_impact_words and not has_metrics:
            # Determine severity based on the impact word
            severity = IssueSeverity.HIGH if any(word in text_lower for word in ["improved", "increased", "reduced"]) else IssueSeverity.MEDIUM
            
            flags.append(HeuristicFlag(
                issue_type=IssueType.MISSING_METRICS,
                severity=severity,
                confidence=0.8,
                explanation=f"Line claims impact but lacks quantification",
                suggested_fix=f"Add specific metrics: by how much? (e.g., '15%', '$50K', '2x faster')",
                line_number=line.line_number,
                examples=["Improved performance by 40%", "Increased sales by $100K", "Reduced costs by 25%"]
            ))
        
        return flags

    def _check_vague_verbs(self, line: 'ProcessedLine') -> List[HeuristicFlag]:
        """Check for weak action verbs"""
        flags = []
        text_lower = line.text.lower()
        
        for weak_verb in self.weak_verbs:
            if weak_verb in text_lower:
                # Suggest alternatives
                alternatives = list(self.strong_verbs)[:3]
                
                flags.append(HeuristicFlag(
                    issue_type=IssueType.VAGUE_VERBS,
                    severity=IssueSeverity.HIGH,
                    confidence=0.9,
                    explanation=f"Uses weak action verb: '{weak_verb}'",
                    suggested_fix=f"Replace with specific action verb",
                    line_number=line.line_number,
                    examples=[f"Built {text_lower.split(weak_verb, 1)[1]}", f"Developed {text_lower.split(weak_verb, 1)[1]}"]
                ))
                break  # Only flag once per line
        
        return flags

    def _check_tool_without_context(self, line: 'ProcessedLine') -> List[HeuristicFlag]:
        """Check for technology mentions without context"""
        flags = []
        text = line.text
        
        # Common technologies that should have context
        technologies = ["Python", "Java", "React", "AWS", "Docker", "Kubernetes", "SQL", "JavaScript"]
        
        tech_mentions = [tech for tech in technologies if tech.lower() in text.lower()]
        
        if tech_mentions:
            # Check if there's meaningful context (verbs, outcomes)
            has_context = any(verb in text.lower() for verb in ["built", "developed", "implemented", "used", "deployed", "designed"])
            
            if not has_context:
                flags.append(HeuristicFlag(
                    issue_type=IssueType.TOOL_WITHOUT_CONTEXT,
                    severity=IssueSeverity.MEDIUM,
                    confidence=0.7,
                    explanation=f"Mentions {', '.join(tech_mentions)} without showing how they were used",
                    suggested_fix=f"Add context: what did you build/achieve with {tech_mentions[0]}?",
                    line_number=line.line_number,
                    examples=[f"Built REST API using {tech_mentions[0]}", f"Deployed applications with {tech_mentions[0]}"]
                ))
        
        return flags

    def _check_overlong_bullet(self, line: 'ProcessedLine') -> List[HeuristicFlag]:
        """Check for overly long bullet points"""
        flags = []
        
        # Count words and characters
        word_count = len(line.text.split())
        char_count = len(line.text)
        
        if word_count > 25 or char_count > 150:
            flags.append(HeuristicFlag(
                issue_type=IssueType.OVERLONG_BULLET,
                severity=IssueSeverity.MEDIUM,
                confidence=0.8,
                explanation=f"Bullet point too long ({word_count} words, {char_count} chars)",
                suggested_fix="Break into 2 bullets or focus on single main achievement",
                line_number=line.line_number,
                examples=["Split into: 'Built X' + 'Achieved Y'", "Focus on most important outcome"]
            ))
        
        return flags

    def _check_laundry_list(self, line: 'ProcessedLine') -> List[HeuristicFlag]:
        """Check for technology laundry lists"""
        flags = []
        
        # Count technology mentions (look for commas and multiple tech terms)
        tech_count = len(re.findall(r'\b[A-Z][a-z]*(?:[A-Z][a-z]*)*\b', line.text))
        comma_count = line.text.count(',')
        
        if tech_count >= 5 and comma_count >= 3:
            flags.append(HeuristicFlag(
                issue_type=IssueType.LAUNDRY_LIST,
                severity=IssueSeverity.MEDIUM,
                confidence=0.7,
                explanation=f"Lists {tech_count} technologies without showing expertise depth",
                suggested_fix="Focus on 2-3 key technologies with specific usage context",
                line_number=line.line_number,
                examples=["Built API using Python and PostgreSQL", "Deployed with Docker and AWS"]
            ))
        
        return flags

    def _check_stale_tech(self, line: 'ProcessedLine') -> List[HeuristicFlag]:
        """Check for outdated technologies"""
        flags = []
        text_lower = line.text.lower()
        
        for stale_tech in self.stale_technologies:
            if stale_tech in text_lower:
                alternative = self.modern_alternatives.get(stale_tech, "modern alternatives")
                
                flags.append(HeuristicFlag(
                    issue_type=IssueType.STALE_TECH,
                    severity=IssueSeverity.LOW,
                    confidence=0.6,
                    explanation=f"Mentions outdated technology: {stale_tech}",
                    suggested_fix=f"Consider highlighting {alternative} instead",
                    line_number=line.line_number,
                    examples=[f"Migrated from {stale_tech} to {alternative}"]
                ))
        
        return flags

    def _check_passive_voice(self, line: 'ProcessedLine') -> List[HeuristicFlag]:
        """Check for passive voice usage"""
        flags = []
        text_lower = line.text.lower()
        
        # Simple passive voice detection
        passive_indicators = ["was responsible", "were responsible", "was tasked", "were tasked", "was assigned"]
        
        for indicator in passive_indicators:
            if indicator in text_lower:
                flags.append(HeuristicFlag(
                    issue_type=IssueType.PASSIVE_VOICE,
                    severity=IssueSeverity.MEDIUM,
                    confidence=0.7,
                    explanation=f"Uses passive voice: '{indicator}'",
                    suggested_fix="Use active voice to show ownership and impact",
                    line_number=line.line_number,
                    examples=["Led the project", "Managed the team", "Delivered the solution"]
                ))
                break
        
        return flags

    def _check_weak_impact(self, line: 'ProcessedLine') -> List[HeuristicFlag]:
        """Check for weak impact statements"""
        flags = []
        text_lower = line.text.lower()
        
        # Weak impact phrases
        weak_phrases = ["various", "multiple", "several", "many", "numerous", "some"]
        
        weak_found = [phrase for phrase in weak_phrases if phrase in text_lower]
        
        if weak_found:
            flags.append(HeuristicFlag(
                issue_type=IssueType.WEAK_IMPACT,
                severity=IssueSeverity.MEDIUM,
                confidence=0.6,
                explanation=f"Uses vague quantifiers: {', '.join(weak_found)}",
                suggested_fix="Replace with specific numbers or meaningful scales",
                line_number=line.line_number,
                examples=["15 clients", "3 major projects", "5-person team"]
            ))
        
        return flags

    def _check_typos_grammar(self, line: 'ProcessedLine') -> List[HeuristicFlag]:
        """Check for common typos and grammar issues"""
        flags = []
        text_lower = line.text.lower()
        
        for typo, correction in self.common_typos.items():
            if typo in text_lower:
                flags.append(HeuristicFlag(
                    issue_type=IssueType.TYPOS_GRAMMAR,
                    severity=IssueSeverity.HIGH,
                    confidence=0.9,
                    explanation=f"Possible typo: '{typo}' should be '{correction}'",
                    suggested_fix=f"Change '{typo}' to '{correction}'",
                    line_number=line.line_number,
                    examples=[f"Correct spelling: {correction}"]
                ))
        
        return flags

    def _calculate_overall_score(self, total_flags: int, total_lines: int, flags_by_severity: Dict[IssueSeverity, int]) -> float:
        """Calculate overall resume quality score"""
        if total_lines == 0:
            return 1.0
        
        # Weight penalties by severity
        penalty_weights = {
            IssueSeverity.CRITICAL: 0.3,
            IssueSeverity.HIGH: 0.2,
            IssueSeverity.MEDIUM: 0.1,
            IssueSeverity.LOW: 0.05
        }
        
        total_penalty = sum(
            flags_by_severity[severity] * weight 
            for severity, weight in penalty_weights.items()
        )
        
        # Convert to score (0.0 to 1.0, higher is better)
        score = max(0.0, 1.0 - (total_penalty / total_lines))
        return round(score, 2)

    def get_top_issues(self, report: HeuristicReport, top_n: int = 5) -> List[HeuristicFlag]:
        """Get the most important issues to address first"""
        all_flags = []
        
        for line_num, flags in report.line_flags.items():
            all_flags.extend(flags)
        
        # Sort by severity (high to low) then confidence (high to low)
        severity_order = {IssueSeverity.CRITICAL: 4, IssueSeverity.HIGH: 3, IssueSeverity.MEDIUM: 2, IssueSeverity.LOW: 1}
        
        all_flags.sort(key=lambda f: (severity_order[f.severity], f.confidence), reverse=True)
        
        return all_flags[:top_n]

    def print_report_summary(self, report: HeuristicReport) -> None:
        """Print a human-readable summary of the heuristic report"""
        print(f"\n=== HEURISTIC ANALYSIS REPORT ===")
        print(f"Lines checked: {report.total_lines_checked}")
        print(f"Total flags: {report.total_flags}")
        print(f"Overall score: {report.overall_score:.2f}/1.00")
        
        if report.total_flags > 0:
            print(f"\nIssues by severity:")
            for severity, count in report.flags_by_severity.items():
                if count > 0:
                    print(f"  {severity.value.title()}: {count}")
            
            print(f"\nIssues by type:")
            for issue_type, count in report.flags_by_type.items():
                if count > 0:
                    print(f"  {issue_type.value.replace('_', ' ').title()}: {count}")
            
            print(f"\nTop issues to fix:")
            top_issues = self.get_top_issues(report, 3)
            for i, flag in enumerate(top_issues, 1):
                print(f"  {i}. Line {flag.line_number}: {flag.explanation}")
                print(f"     Fix: {flag.suggested_fix}")
        else:
            print("\n✅ No issues found!")

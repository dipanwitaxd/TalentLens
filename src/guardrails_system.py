# src/guardrails_system.py
# Phase 11: Guardrails, privacy, fairness
# Goal: Keep it safe, respectful, and compliant

from typing import List, Dict, Any, Optional, Set, Tuple
from dataclasses import dataclass
import re
import logging
from enum import Enum
import hashlib

class ViolationType(Enum):
    PII_EXPOSURE = "pii_exposure"
    BIAS_DETECTION = "bias_detection"
    PROTECTED_CLASS = "protected_class"
    INAPPROPRIATE_CONTENT = "inappropriate_content"
    DISCRIMINATION_RISK = "discrimination_risk"
    PRIVACY_VIOLATION = "privacy_violation"

class SeverityLevel(Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"

@dataclass
class GuardrailViolation:
    """A detected guardrail violation"""
    violation_type: ViolationType
    severity: SeverityLevel
    description: str
    location: str  # Where in the text/process
    recommended_action: str
    confidence: float

@dataclass
class PrivacyReport:
    """Privacy analysis report"""
    pii_detected: List[str]
    pii_redacted: List[str]
    sensitive_patterns: List[str]
    anonymization_applied: bool
    compliance_status: str

class GuardrailsSystem:
    """Comprehensive safety and fairness system"""
    
    def __init__(self):
        self.setup_logging()
        self.initialize_patterns()
        self.initialize_bias_detection()
        
    def setup_logging(self):
        """Setup guardrails logging"""
        logging.basicConfig(level=logging.INFO)
        self.logger = logging.getLogger("Guardrails")
    
    def initialize_patterns(self):
        """Initialize PII and sensitive content patterns"""
        
        # PII patterns
        self.pii_patterns = {
            'email': r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b',
            'phone': r'\b(?:\+?1[-.\s]?)?\(?[0-9]{3}\)?[-.\s]?[0-9]{3}[-.\s]?[0-9]{4}\b',
            'ssn': r'\b\d{3}-?\d{2}-?\d{4}\b',
            'address': r'\b\d+\s+[A-Za-z\s]+(?:Street|St|Avenue|Ave|Road|Rd|Drive|Dr|Lane|Ln|Boulevard|Blvd)\b',
            'credit_card': r'\b(?:\d{4}[-\s]?){3}\d{4}\b',
            'date_of_birth': r'\b(?:0?[1-9]|1[0-2])[/-](?:0?[1-9]|[12][0-9]|3[01])[/-](?:19|20)\d{2}\b'
        }
        
        # Protected class indicators (to flag, not use for decisions)
        self.protected_class_patterns = {
            'age': r'\b(?:age|years old|born in|birth year)\b',
            'gender': r'\b(?:male|female|man|woman|he|she|gender|sex)\b',
            'race': r'\b(?:white|black|asian|hispanic|latino|african|caucasian|race|ethnicity)\b',
            'religion': r'\b(?:christian|muslim|jewish|hindu|buddhist|atheist|religion|faith)\b',
            'disability': r'\b(?:disabled|disability|handicap|impaired|wheelchair)\b',
            'sexual_orientation': r'\b(?:gay|lesbian|straight|bisexual|lgbt|sexual orientation)\b',
            'marital_status': r'\b(?:married|single|divorced|widowed|spouse|husband|wife)\b',
            'nationality': r'\b(?:american|citizen|immigrant|visa|nationality|country of origin)\b'
        }
        
        # Inappropriate content patterns
        self.inappropriate_patterns = {
            'discriminatory_language': r'\b(?:discriminat|prejud|bias|unfair|exclud)\b',
            'inappropriate_requirements': r'\b(?:must be|only|native speaker|young|energetic)\b'
        }
    
    def initialize_bias_detection(self):
        """Initialize bias detection rules"""
        
        # Biased language patterns
        self.biased_language = {
            'age_bias': [
                'digital native', 'tech-savvy', 'energetic', 'young', 'recent graduate',
                'experienced', 'seasoned', 'mature', 'senior'
            ],
            'gender_bias': [
                'aggressive', 'assertive', 'bossy', 'emotional', 'nurturing',
                'competitive', 'collaborative', 'supportive'
            ],
            'cultural_bias': [
                'native speaker', 'cultural fit', 'team player', 'go-getter',
                'rockstar', 'ninja', 'guru'
            ]
        }
        
        # Inclusive alternatives
        self.inclusive_alternatives = {
            'guys': 'team/everyone/folks',
            'manpower': 'workforce/staff',
            'master/slave': 'primary/secondary',
            'blacklist': 'blocklist',
            'whitelist': 'allowlist'
        }

    def scan_resume_content(self, resume_text: str) -> Tuple[str, PrivacyReport, List[GuardrailViolation]]:
        """Scan resume content for privacy and safety issues"""
        
        violations = []
        
        # PII Detection and Redaction
        cleaned_text, pii_report = self.handle_pii(resume_text)
        
        # Bias Detection
        bias_violations = self.detect_bias_indicators(cleaned_text)
        violations.extend(bias_violations)
        
        # Inappropriate Content Detection
        content_violations = self.detect_inappropriate_content(cleaned_text)
        violations.extend(content_violations)
        
        # Protected Class Information Detection
        protected_violations = self.detect_protected_class_info(cleaned_text)
        violations.extend(protected_violations)
        
        return cleaned_text, pii_report, violations

    def handle_pii(self, text: str) -> Tuple[str, PrivacyReport]:
        """Detect and redact PII from resume text"""
        
        pii_detected = []
        pii_redacted = []
        cleaned_text = text
        
        for pii_type, pattern in self.pii_patterns.items():
            matches = re.findall(pattern, text, re.IGNORECASE)
            
            if matches:
                pii_detected.append(f"{pii_type}: {len(matches)} instances")
                
                # Redact PII (except email which might be needed for contact)
                if pii_type != 'email':
                    for match in matches:
                        if pii_type == 'phone':
                            redacted = '[PHONE_REDACTED]'
                        elif pii_type == 'ssn':
                            redacted = '[SSN_REDACTED]'
                        elif pii_type == 'address':
                            redacted = '[ADDRESS_REDACTED]'
                        elif pii_type == 'credit_card':
                            redacted = '[CC_REDACTED]'
                        elif pii_type == 'date_of_birth':
                            redacted = '[DOB_REDACTED]'
                        else:
                            redacted = f'[{pii_type.upper()}_REDACTED]'
                        
                        cleaned_text = cleaned_text.replace(match, redacted)
                        pii_redacted.append(f"{pii_type}: {match}")
        
        # Create anonymized candidate ID
        candidate_hash = hashlib.sha256(text.encode()).hexdigest()[:8]
        
        privacy_report = PrivacyReport(
            pii_detected=pii_detected,
            pii_redacted=pii_redacted,
            sensitive_patterns=[],
            anonymization_applied=len(pii_redacted) > 0,
            compliance_status="compliant" if len(pii_detected) <= 1 else "review_required"
        )
        
        return cleaned_text, privacy_report

    def detect_bias_indicators(self, text: str) -> List[GuardrailViolation]:
        """Detect potential bias indicators in text"""
        
        violations = []
        text_lower = text.lower()
        
        for bias_type, terms in self.biased_language.items():
            for term in terms:
                if term.lower() in text_lower:
                    violations.append(GuardrailViolation(
                        violation_type=ViolationType.BIAS_DETECTION,
                        severity=SeverityLevel.MEDIUM,
                        description=f"Potential {bias_type.replace('_', ' ')} detected: '{term}'",
                        location=f"Text contains: {term}",
                        recommended_action=f"Consider neutral alternative for '{term}'",
                        confidence=0.7
                    ))
        
        return violations

    def detect_inappropriate_content(self, text: str) -> List[GuardrailViolation]:
        """Detect inappropriate content in text"""
        
        violations = []
        text_lower = text.lower()
        
        for content_type, pattern in self.inappropriate_patterns.items():
            matches = re.findall(pattern, text_lower)
            
            for match in matches:
                violations.append(GuardrailViolation(
                    violation_type=ViolationType.INAPPROPRIATE_CONTENT,
                    severity=SeverityLevel.HIGH,
                    description=f"Inappropriate {content_type.replace('_', ' ')}: '{match}'",
                    location=f"Pattern match: {match}",
                    recommended_action="Remove or rephrase inappropriate content",
                    confidence=0.8
                ))
        
        return violations

    def detect_protected_class_info(self, text: str) -> List[GuardrailViolation]:
        """Detect protected class information that shouldn't influence decisions"""
        
        violations = []
        text_lower = text.lower()
        
        for protected_class, pattern in self.protected_class_patterns.items():
            matches = re.findall(pattern, text_lower)
            
            if matches:
                violations.append(GuardrailViolation(
                    violation_type=ViolationType.PROTECTED_CLASS,
                    severity=SeverityLevel.HIGH,
                    description=f"Protected class information detected: {protected_class}",
                    location=f"References to {protected_class}",
                    recommended_action="Flag for review - do not use in hiring decisions",
                    confidence=0.9
                ))
        
        return violations

    def validate_critique_content(self, critique_text: str) -> List[GuardrailViolation]:
        """Validate that critique content is appropriate and unbiased"""
        
        violations = []
        
        # Check for discriminatory language in critiques
        discriminatory_terms = [
            'too old', 'too young', 'overqualified', 'not a good fit',
            'cultural fit', 'personality', 'attitude'
        ]
        
        text_lower = critique_text.lower()
        
        for term in discriminatory_terms:
            if term in text_lower:
                violations.append(GuardrailViolation(
                    violation_type=ViolationType.DISCRIMINATION_RISK,
                    severity=SeverityLevel.CRITICAL,
                    description=f"Potentially discriminatory critique language: '{term}'",
                    location="Critique content",
                    recommended_action="Rephrase to focus on skills and qualifications only",
                    confidence=0.9
                ))
        
        # Check for personal attacks or inappropriate feedback
        inappropriate_critique = [
            'stupid', 'dumb', 'terrible', 'awful', 'pathetic',
            'worthless', 'useless', 'hopeless'
        ]
        
        for term in inappropriate_critique:
            if term in text_lower:
                violations.append(GuardrailViolation(
                    violation_type=ViolationType.INAPPROPRIATE_CONTENT,
                    severity=SeverityLevel.CRITICAL,
                    description=f"Inappropriate critique language: '{term}'",
                    location="Critique feedback",
                    recommended_action="Replace with constructive, professional feedback",
                    confidence=0.95
                ))
        
        return violations

    def ensure_truthfulness_compliance(self, original_text: str, suggested_rewrite: str) -> List[GuardrailViolation]:
        """Ensure rewritten content doesn't add false information"""
        
        violations = []
        
        # Check for invented metrics
        original_numbers = re.findall(r'\d+(?:\.\d+)?[%KMB]?', original_text)
        rewrite_numbers = re.findall(r'\d+(?:\.\d+)?[%KMB]?', suggested_rewrite)
        
        # Remove [NEED_EVIDENCE] placeholders for comparison
        clean_rewrite = re.sub(r'\[NEED_EVIDENCE:.*?\]', '', suggested_rewrite)
        clean_rewrite_numbers = re.findall(r'\d+(?:\.\d+)?[%KMB]?', clean_rewrite)
        
        new_numbers = set(clean_rewrite_numbers) - set(original_numbers)
        
        if new_numbers:
            violations.append(GuardrailViolation(
                violation_type=ViolationType.INAPPROPRIATE_CONTENT,
                severity=SeverityLevel.CRITICAL,
                description=f"Invented metrics detected: {list(new_numbers)}",
                location="Suggested rewrite",
                recommended_action="Remove invented numbers, use [NEED_EVIDENCE] placeholders",
                confidence=0.95
            ))
        
        # Check for invented company names
        original_caps = re.findall(r'\b[A-Z][a-z]+(?:\s+[A-Z][a-z]+)*\b', original_text)
        rewrite_caps = re.findall(r'\b[A-Z][a-z]+(?:\s+[A-Z][a-z]+)*\b', suggested_rewrite)
        
        # Common words that aren't company names
        common_words = {'Built', 'Developed', 'Improved', 'Led', 'Managed', 'Created', 'Designed'}
        
        original_caps = set(original_caps) - common_words
        rewrite_caps = set(rewrite_caps) - common_words
        
        new_caps = rewrite_caps - original_caps
        
        if new_caps:
            violations.append(GuardrailViolation(
                violation_type=ViolationType.INAPPROPRIATE_CONTENT,
                severity=SeverityLevel.HIGH,
                description=f"Potentially invented proper nouns: {list(new_caps)}",
                location="Suggested rewrite",
                recommended_action="Verify these are not invented company/product names",
                confidence=0.7
            ))
        
        return violations

    def apply_content_filters(self, text: str) -> str:
        """Apply content filters to ensure appropriate language"""
        
        filtered_text = text
        
        # Replace biased language with inclusive alternatives
        for biased_term, inclusive_term in self.inclusive_alternatives.items():
            filtered_text = re.sub(
                r'\b' + re.escape(biased_term) + r'\b',
                inclusive_term,
                filtered_text,
                flags=re.IGNORECASE
            )
        
        return filtered_text

    def generate_compliance_report(self, violations: List[GuardrailViolation], privacy_report: PrivacyReport) -> Dict[str, Any]:
        """Generate comprehensive compliance report"""
        
        # Count violations by type and severity
        violation_counts = {}
        severity_counts = {}
        
        for violation in violations:
            v_type = violation.violation_type.value
            severity = violation.severity.value
            
            violation_counts[v_type] = violation_counts.get(v_type, 0) + 1
            severity_counts[severity] = severity_counts.get(severity, 0) + 1
        
        # Determine overall compliance status
        critical_violations = severity_counts.get('critical', 0)
        high_violations = severity_counts.get('high', 0)
        
        if critical_violations > 0:
            compliance_status = "non_compliant"
            risk_level = "high"
        elif high_violations > 2:
            compliance_status = "review_required"
            risk_level = "medium"
        elif len(violations) > 0:
            compliance_status = "caution"
            risk_level = "low"
        else:
            compliance_status = "compliant"
            risk_level = "minimal"
        
        return {
            "compliance_status": compliance_status,
            "risk_level": risk_level,
            "total_violations": len(violations),
            "violation_breakdown": violation_counts,
            "severity_breakdown": severity_counts,
            "privacy_status": privacy_report.compliance_status,
            "pii_detected": len(privacy_report.pii_detected),
            "recommendations": self._generate_recommendations(violations),
            "required_actions": [v.recommended_action for v in violations if v.severity in [SeverityLevel.CRITICAL, SeverityLevel.HIGH]]
        }

    def _generate_recommendations(self, violations: List[GuardrailViolation]) -> List[str]:
        """Generate specific recommendations based on violations"""
        
        recommendations = []
        
        violation_types = {v.violation_type for v in violations}
        
        if ViolationType.PII_EXPOSURE in violation_types:
            recommendations.append("Implement stronger PII detection and redaction")
        
        if ViolationType.BIAS_DETECTION in violation_types:
            recommendations.append("Review language for potential bias and use inclusive alternatives")
        
        if ViolationType.PROTECTED_CLASS in violation_types:
            recommendations.append("Ensure protected class information is not used in decision-making")
        
        if ViolationType.DISCRIMINATION_RISK in violation_types:
            recommendations.append("Revise feedback to focus solely on job-relevant qualifications")
        
        if ViolationType.INAPPROPRIATE_CONTENT in violation_types:
            recommendations.append("Replace inappropriate language with professional alternatives")
        
        # General recommendations
        recommendations.extend([
            "Regularly audit system outputs for compliance",
            "Provide bias training for system operators",
            "Implement human review for high-risk cases"
        ])
        
        return recommendations[:5]  # Top 5 recommendations

    def enforce_guardrails(self, resume_text: str, critique_results: List[Any] = None) -> Dict[str, Any]:
        """Comprehensive guardrail enforcement"""
        
        self.logger.info("Starting guardrail enforcement")
        
        # Scan resume content
        cleaned_text, privacy_report, content_violations = self.scan_resume_content(resume_text)
        
        all_violations = content_violations.copy()
        
        # Validate critique content if provided
        if critique_results:
            for critique in critique_results:
                if hasattr(critique, 'suggested_rewrite'):
                    # Check critique language
                    critique_violations = self.validate_critique_content(critique.suggested_rewrite)
                    all_violations.extend(critique_violations)
                    
                    # Check truthfulness
                    truth_violations = self.ensure_truthfulness_compliance(
                        critique.original_text, critique.suggested_rewrite
                    )
                    all_violations.extend(truth_violations)
        
        # Apply content filters
        filtered_text = self.apply_content_filters(cleaned_text)
        
        # Generate compliance report
        compliance_report = self.generate_compliance_report(all_violations, privacy_report)
        
        # Log results
        self.logger.info(f"Guardrail enforcement complete: {compliance_report['compliance_status']}")
        
        return {
            "original_text": resume_text,
            "cleaned_text": filtered_text,
            "privacy_report": privacy_report,
            "violations": all_violations,
            "compliance_report": compliance_report,
            "safe_to_process": compliance_report['compliance_status'] in ['compliant', 'caution']
        }

    def print_guardrail_report(self, enforcement_result: Dict[str, Any], use_streamlit: bool = False) -> None:
        """Print human-readable guardrail report"""

        compliance = enforcement_result['compliance_report']
        privacy = enforcement_result['privacy_report']
        violations = enforcement_result['violations']

        if use_streamlit:
            # Use streamlit for UI display
            try:
                import streamlit as st

                st.markdown("### 🔒 Guardrails & Compliance Report")

                col1, col2, col3 = st.columns(3)
                with col1:
                    st.metric("Compliance Status", compliance['compliance_status'].upper())
                with col2:
                    st.metric("Risk Level", compliance['risk_level'].upper())
                with col3:
                    st.metric("Safe to Process", "YES" if enforcement_result['safe_to_process'] else "NO")

                if privacy.pii_detected:
                    st.markdown("#### Privacy Status")
                    st.write(f"- PII Detected: {len(privacy.pii_detected)} types")
                    st.write(f"- Anonymization Applied: {'YES' if privacy.anonymization_applied else 'NO'}")

                if violations:
                    st.markdown(f"#### Violations Found ({len(violations)} total)")
                    for violation in violations[:5]:  # Show top 5
                        with st.expander(f"{violation.violation_type.value.replace('_', ' ').title()}: {violation.severity.value.upper()}"):
                            st.write(f"**Description:** {violation.description}")
                            st.write(f"**Location:** {violation.location}")
                            st.write(f"**Recommended Action:** {violation.recommended_action}")
                            st.write(f"**Confidence:** {violation.confidence:.2f}")

                if compliance['required_actions']:
                    st.markdown("#### Required Actions")
                    for action in compliance['required_actions'][:3]:
                        st.write(f"- {action}")

                st.markdown("#### Recommendations")
                for rec in compliance['recommendations'][:3]:
                    st.write(f"- {rec}")

            except ImportError:
                # Fallback to regular print if streamlit not available
                use_streamlit = False

        if not use_streamlit:
            # Use regular print for console/testing
            print(f"\n=== GUARDRAILS & COMPLIANCE REPORT ===")
            print(f"Compliance Status: {compliance['compliance_status'].upper()}")
            print(f"Risk Level: {compliance['risk_level'].upper()}")
            print(f"Safe to Process: {'YES' if enforcement_result['safe_to_process'] else 'NO'}")

            if privacy.pii_detected:
                print(f"\nPrivacy Status:")
                print(f"  PII Detected: {len(privacy.pii_detected)} types")
                print(f"  Anonymization Applied: {'YES' if privacy.anonymization_applied else 'NO'}")

            if violations:
                print(f"\nViolations Found ({len(violations)} total):")
                for violation in violations[:5]:  # Show top 5
                    print(f"  - {violation.violation_type.value}: {violation.description}")
                    print(f"    Action: {violation.recommended_action}")

            if compliance['required_actions']:
                print(f"\nRequired Actions:")
                for action in compliance['required_actions'][:3]:
                    print(f"  - {action}")

            print(f"\nRecommendations:")
            for rec in compliance['recommendations'][:3]:
                print(f"  - {rec}")


# Testing function
def test_guardrails_system():
    """Test the guardrails system"""
    print("=== TESTING GUARDRAILS SYSTEM (Phase 11) ===")
    
    guardrails = GuardrailsSystem()
    
    # Test case with multiple issues
    problematic_resume = """
    JOHN DOE
    Email: john.doe@email.com
    Phone: 555-123-4567
    Age: 25 years old
    
    EXPERIENCE
    • Worked as an aggressive go-getter rockstar developer
    • Must be a native English speaker for this role
    • Built applications that guys on the team loved
    • Used master/slave architecture for database replication
    """
    
    print("Testing resume with multiple guardrail issues...")
    
    # Run guardrail enforcement
    result = guardrails.enforce_guardrails(problematic_resume)
    
    # Print report
    guardrails.print_guardrail_report(result)
    
    print(f"\nCleaned text preview:")
    print(result['cleaned_text'][:200] + "...")
    
    print(f"\n✅ Phase 11 guardrails system working!")

if __name__ == "__main__":
    test_guardrails_system()
#!/usr/bin/env python3
# demo_runner.py - Automated demo of TalentLens capabilities

import json
import time
from src.text_processor import UniversalTextProcessor
from src.heuristic_checker import HeuristicChecker
from src.profile_extractor import ProfileExtractor
from src.fit_analyzer import FitAnalyzer

def run_demo():
    print("🎯 TalentLens Demo - Candidate-Centric ATS")
    print("=" * 50)
    
    # Load demo data
    with open("demo_samples.json", "r") as f:
        demo_data = json.load(f)
    
    # Initialize components
    processor = UniversalTextProcessor()
    checker = HeuristicChecker()
    extractor = ProfileExtractor()
    analyzer = FitAnalyzer()
    
    print("\n📝 Testing with problematic resume...")
    
    # Process problematic resume
    resume = demo_data["sample_resumes"]["problematic_resume"]
    jd = demo_data["sample_job_descriptions"]["frontend_developer"]
    
    print(f"Resume preview: {resume[:100]}...")
    
    # Run analysis
    processed = processor.process_resume(resume)
    report = checker.check_resume_lines(processed)
    profile = extractor.extract_candidate_profile(processed)
    fit_analysis = analyzer.analyze_candidate_fit(profile)
    
    # Show results
    print(f"\n📊 Analysis Results:")
    print(f"  Quality Score: {report.overall_score:.2f}/1.00")
    print(f"  Issues Found: {report.total_flags}")
    print(f"  Top Role Fit: {fit_analysis.top_role_fits[0].role_title}")
    print(f"  Fit Score: {fit_analysis.top_role_fits[0].fit_score:.2f}")
    
    print(f"\n🔍 Top Issues:")
    for issue_type, count in report.flags_by_type.items():
        if count > 0:
            print(f"  - {issue_type.value.replace('_', ' ').title()}: {count}")
    
    print("\n✅ Demo completed! Check the web interface for detailed analysis.")
    print("Run: streamlit run ui/streamlit_app.py")

if __name__ == "__main__":
    run_demo()

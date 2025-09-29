import ssl
import certifi

# Fix SSL certificate issues for macOS
try:
    import nltk
    # Set SSL context for NLTK downloads
    ssl_context = ssl.create_default_context()
    ssl_context.check_hostname = False
    ssl_context.verify_mode = ssl.CERT_NONE
    
    # Alternative: use certifi for proper SSL
    # ssl_context = ssl.create_default_context(cafile=certifi.where())
    
    # Download NLTK data with proper SSL context
    nltk.download('punkt', quiet=True)
    nltk.download('stopwords', quiet=True)
    print("✅ NLTK data downloaded successfully")
    
except Exception as e:
    print(f"Note: NLTK download issue (will continue anyway): {e}")

def test_phases_1_and_2_first():
    """Test Phases 1 & 2 before Phase 3"""
    print("=== TESTING PHASES 1 & 2 FIRST ===")
    
    from src.text_processor import UniversalTextProcessor
    from src.index_manager import ATSIndexManager
    
    # Phase 1: Process text
    processor = UniversalTextProcessor()
    
    sample_resume = """
    JOHN DOE
    Software Engineer
    
    EXPERIENCE
    • Built scalable Python applications serving 10K+ users daily
    • Improved database query performance by 40% through optimization
    • Led cross-functional team of 5 engineers on cloud migration
    • Developed machine learning models for recommendation system
    
    SKILLS
    Python, AWS, PostgreSQL, Docker, Kubernetes, Machine Learning
    """
    
    print("Phase 1: Processing resume...")
    processed_lines = processor.process_resume(sample_resume)
    processor.display_processed_lines(processed_lines)
    
    # Phase 2: Index the data
    print(f"\nPhase 2: Indexing {len(processed_lines)} lines...")
    index_manager = ATSIndexManager(persist_directory="./indexes")
    
    # Index resume lines
    resume_count = index_manager.index_resume(processed_lines, resume_id="test_user")
    print(f"✅ Indexed {resume_count} resume lines")
    
    # Test basic search
    print("\nTesting basic search...")
    search_results = index_manager.test_search("Python machine learning")
    
    if search_results.get("vector"):
        print(f"Vector search found {len(search_results['vector'])} results")
        for i, result in enumerate(search_results["vector"][:2]):
            print(f"  {i+1}. {result['text']}")
    
    if search_results.get("bm25"):
        print(f"BM25 search found {len(search_results['bm25'])} results")
        for i, result in enumerate(search_results["bm25"][:2]):
            print(f"  {i+1}. {result['text']}")
    
    print("✅ Phases 1 & 2 working!")
    return index_manager

def test_phase3_with_existing_data():
    """Test Phase 3 with data from Phases 1 & 2"""
    print("\n=== TESTING PHASE 3 RETRIEVAL ===")
    
    # First ensure we have indexed data
    index_manager = test_phases_1_and_2_first()
    
    # Now test Phase 3
    from src.retriever import HybridRetriever
    
    print("\nInitializing hybrid retriever...")
    retriever = HybridRetriever(index_manager)
    
    # Test hybrid search
    print("Testing hybrid search...")
    try:
        results = retriever.retrieve_resume_context("Python machine learning")
        
        print(f"Found {len(results)} relevant lines:")
        for i, result in enumerate(results[:3]):
            print(f"  {i+1}. [{result.source_type}] Score: {result.score:.3f}")
            print(f"      {result.text[:60]}...")
        
        # Test context pack building
        print("\nTesting context pack...")
        target_line = "Built scalable Python applications serving 10K+ users daily"
        target_id = "test_user_L001"  # Updated to match our resume_id
        
        context_pack = retriever.build_context_pack(target_line, target_id)
        
        print(f"Context pack stats:")
        print(f"  Resume neighbors: {len(context_pack.resume_neighbors)}")
        print(f"  Target section: {context_pack.section_context.get('target_section', 'unknown')}")
        
        print("✅ Phase 3 retrieval working!")
        
    except Exception as e:
        print(f"❌ Phase 3 error: {e}")
        import traceback
        traceback.print_exc()

def minimal_test():
    """Minimal test that should definitely work"""
    print("=== MINIMAL TEST (Phase 1 only) ===")
    
    from src.text_processor import UniversalTextProcessor
    
    processor = UniversalTextProcessor()
    
    simple_resume = """
    EXPERIENCE
    • Built Python applications
    • Improved performance by 40%
    """
    
    processed = processor.process_resume(simple_resume)
    processor.display_processed_lines(processed)
    
    print(f"✅ Processed {len(processed)} lines successfully")

def test_phase4():
    from src.text_processor import UniversalTextProcessor
    from src.profile_extractor import ProfileExtractor
    
    print("=== TESTING PHASE 4 PROFILE EXTRACTION ===")
    
    processor = UniversalTextProcessor()
    extractor = ProfileExtractor()
    
    # Test with sample resume
    sample_resume = """
    JOHN DOE
    Senior Software Engineer
    
    EXPERIENCE
    Senior Software Engineer | TechCorp Inc
    • Built Python applications serving 10K+ users daily
    • Improved database performance by 40% through optimization
    
    SKILLS
    Python, AWS, PostgreSQL, Docker, Machine Learning
    """
    
    processed_resume = processor.process_resume(sample_resume)
    candidate_profile = extractor.extract_candidate_profile(processed_resume)
    
    print(f"Candidate: {candidate_profile.name}")
    print(f"Title: {candidate_profile.current_title}")
    print(f"Top skills: {[skill.name for skill in candidate_profile.top_skills[:3]]}")
    print(f"Achievements: {len(candidate_profile.key_achievements)}")
    
    print("✅ Phase 4 working!")

def test_phase5():
    from src.text_processor import UniversalTextProcessor
    from src.heuristic_checker import HeuristicChecker
    
    print("=== TESTING PHASE 5 HEURISTIC CHECKER ===")
    
    processor = UniversalTextProcessor()
    checker = HeuristicChecker()
    
    # Test with problematic resume
    bad_resume = """
    EXPERIENCE
    • Worked on machine learning projects using Python, Java, React, Vue, AWS, Docker
    • Was responsible for improving database performance
    • Helped with various tasks and supported multiple teams
    • Reduced system downtime and increased user satisfaction
    """
    
    processed_lines = processor.process_resume(bad_resume)
    report = checker.check_resume_lines(processed_lines)
    
    checker.print_report_summary(report)
    print("✅ Phase 5 working!")

def test_phase6():
    import os
    from src.text_processor import UniversalTextProcessor
    from src.index_manager import ATSIndexManager
    from src.retriever import HybridRetriever
    from src.heuristic_checker import HeuristicChecker
    from src.critique_engine import CritiqueEngine
    
    print("=== TESTING PHASE 6 CRITIQUE ENGINE ===")
    
    # Check for API key
    api_key = os.getenv('GROQ_API_KEY')
    if not api_key:
        print("⚠️  GROQ_API_KEY not set. Set with: export GROQ_API_KEY='your_key'")
        print("Testing structure only...")
        from src.critique_engine import test_critique_engine
        test_critique_engine()
        return
    
    # Initialize all components
    processor = UniversalTextProcessor()
    index_manager = ATSIndexManager(persist_directory="./indexes")
    retriever = HybridRetriever(index_manager)
    checker = HeuristicChecker()
    critique_engine = CritiqueEngine(api_key)
    
    # Sample resume with issues
    test_resume = """
    EXPERIENCE
    • Worked on machine learning projects using Python
    • Was responsible for improving database performance
    • Helped with various tasks and supported multiple teams
    """
    
    # Process and index
    processed_lines = processor.process_resume(test_resume)
    index_manager.index_resume(processed_lines, resume_id="test")
    
    # Get critique for first bullet
    target_line = "Worked on machine learning projects using Python"
    target_id = "test_L001"
    
    # Get context and heuristic flags
    context_pack = retriever.build_context_pack(target_line, target_id)
    heuristic_report = checker.check_resume_lines(processed_lines)
    heuristic_flags = heuristic_report.line_flags.get(1, [])
    
    # Generate critique
    critique = critique_engine.critique_resume_line(
        target_line, 1, context_pack, heuristic_flags
    )
    
    print(f"Critiquing: \"{target_line}\"")
    print(f"Assessment: {critique.overall_assessment}")
    print(f"Issues found: {len(critique.issues)}")
    print(f"Suggested rewrite: {critique.suggested_rewrite}")
    
    for issue in critique.issues:
        print(f"  - {issue.type} ({issue.severity}): {issue.explanation}")
    
    print("✅ Phase 6 working!")

def test_phase7():
    from src.text_processor import UniversalTextProcessor
    from src.profile_extractor import ProfileExtractor
    from src.critique_engine import LineCritique, CritiqueIssue
    from src.redraft_engine import RedraftEngine
    
    print("=== TESTING PHASE 7 REDRAFT ENGINE ===")
    
    processor = UniversalTextProcessor()
    profile_extractor = ProfileExtractor()
    redraft_engine = RedraftEngine()
    
    # Sample problematic resume
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
    
    # Simulate critiques (normally from Phase 6)
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
    
    print("\nSample redrafted content:")
    markdown = redraft_engine.export_to_markdown(redrafted)
    print(markdown[:400] + "...")
    
    print("✅ Phase 7 working!")


def test_phase8():
    from src.text_processor import UniversalTextProcessor
    from src.profile_extractor import ProfileExtractor
    from src.fit_analyzer import FitAnalyzer
    
    print("=== TESTING PHASE 8 FIT ANALYZER ===")
    
    processor = UniversalTextProcessor()
    profile_extractor = ProfileExtractor()
    fit_analyzer = FitAnalyzer()
    
    # Sample resume with ML/engineering background
    sample_resume = """
    JOHN DOE
    Software Engineer
    
    EXPERIENCE
    • Built machine learning models using Python and TensorFlow serving 100K+ users
    • Deployed applications on AWS with Docker and Kubernetes reducing costs by 30%
    • Led team of 3 engineers on microservices migration project
    
    SKILLS
    Python, AWS, Docker, Kubernetes, Machine Learning, TensorFlow, SQL
    """
    
    processed_lines = processor.process_resume(sample_resume)
    candidate_profile = profile_extractor.extract_candidate_profile(processed_lines)
    
    # Enhance profile for realistic testing
    candidate_profile.total_experience_years = 4
    candidate_profile.industries.add("technology")
    
    # Analyze fit
    report = fit_analyzer.analyze_candidate_fit(candidate_profile)
    
    fit_analyzer.print_fit_analysis_report(report)
    
    print("✅ Phase 8 working!")

# Add to your main.py
def test_phase10():
    from src.text_processor import UniversalTextProcessor
    from src.index_manager import ATSIndexManager
    from src.heuristic_checker import HeuristicChecker
    from src.profile_extractor import ProfileExtractor
    from src.redraft_engine import RedraftEngine
    from src.fit_analyzer import FitAnalyzer
    from src.evaluation_system import EvaluationSystem
    
    print("=== TESTING PHASE 10 EVALUATION SYSTEM ===")
    
    # Initialize evaluation system
    evaluator = EvaluationSystem(log_directory="./evaluation_logs")
    
    # Initialize ATS components for testing
    components = {
        'processor': UniversalTextProcessor(),
        'index_manager': ATSIndexManager(persist_directory="./indexes"),
        'heuristic_checker': HeuristicChecker(),
        'profile_extractor': ProfileExtractor(),
        'redraft_engine': RedraftEngine(),
        'fit_analyzer': FitAnalyzer()
    }
    
    print(f"Golden test set created with {len(evaluator.golden_test_set)} test cases")
    
    # Run evaluation on a sample test case
    sample_test = evaluator.golden_test_set[0]
    print(f"\nTesting with: {sample_test.id} ({sample_test.difficulty_level})")
    
    # Trace execution
    trace = evaluator.trace_execution(sample_test.resume_text, components)
    
    print(f"Execution trace: {trace.trace_id}")
    print(f"Success: {trace.success}")
    print(f"Total time: {trace.total_time:.2f}s")
    print(f"Processing steps: {len(trace.processing_steps)}")
    
    # Show step details
    for step in trace.processing_steps:
        print(f"  - {step['step']}: {step['duration']:.2f}s")
    
    # Run quick evaluation
    print("\nRunning system evaluation...")
    metrics = evaluator.evaluate_system(components)
    
    # Generate report
    report = evaluator.generate_quality_report(metrics)
    print(report)
    
    print("✅ Phase 10 evaluation system working!")

# Add to your main.py
def test_phase11():
    from src.guardrails_system import GuardrailsSystem
    
    print("=== TESTING PHASE 11 GUARDRAILS SYSTEM ===")
    
    guardrails = GuardrailsSystem()
    
    # Test with problematic resume content
    problematic_resume = """
    JANE SMITH
    Email: jane.smith@email.com
    Phone: 555-123-4567
    Age: 28 years old
    Married with 2 children
    
    EXPERIENCE
    • Worked as an aggressive go-getter rockstar developer
    • Must be a native English speaker for this position
    • Built applications that guys on the team loved
    • Led all-male team of 5 engineers
    """
    
    print("Testing with problematic resume content...")
    
    # Run guardrail enforcement
    result = guardrails.enforce_guardrails(problematic_resume)
    
    # Print detailed report
    guardrails.print_guardrail_report(result)
    
    print("\nCleaned text preview:")
    print(result['cleaned_text'][:300] + "...")
    
    print("✅ Phase 11 guardrails working!")

if __name__ == "__main__":
    test_phase11()

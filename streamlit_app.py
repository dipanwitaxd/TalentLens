# ui/streamlit_app.py
# Phase 9: UI or API façade with Guardrails Integration
# Goal: Make it demo-able in minutes with safety controls

import streamlit as st
import traceback
from datetime import datetime
import sys
import os
import importlib

# Add both possible paths
current_dir = os.path.dirname(os.path.abspath(__file__))
src_dir = os.path.join(current_dir, 'src')

# Add to Python path
if src_dir not in sys.path:
    sys.path.insert(0, src_dir)

try:
    from text_processor import UniversalTextProcessor
    from index_manager import ATSIndexManager
    from retriever import HybridRetriever
    from profile_extractor import ProfileExtractor
    from heuristic_checker import HeuristicChecker
    from critique_engine import CritiqueEngine
    from redraft_engine import RedraftEngine
    from fit_analyzer import FitAnalyzer
    from guardrails_system import GuardrailsSystem
except ImportError as e:
    st.error(f"Import error: {e}")
    st.error("Make sure all source files are in the src/ directory")
    st.stop()


if 'pdf_processor' in sys.modules:
    importlib.reload(sys.modules['pdf_processor'])

# Page configuration
st.set_page_config(
    page_title="TalentLens - Candidate-Centric ATS",
    page_icon="🎯",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS for better styling
st.markdown("""
<style>
.main-header {
    font-size: 2.5rem;
    color: #1f77b4;
    text-align: center;
    margin-bottom: 2rem;
}
.section-header {
    font-size: 1.5rem;
    color: #2e3440;
    border-bottom: 2px solid #1f77b4;
    padding-bottom: 0.5rem;
    margin: 1.5rem 0 1rem 0;
}
.metric-box {
    background-color: #f8f9fa;
    padding: 1rem;
    border-radius: 0.5rem;
    border-left: 4px solid #1f77b4;
    margin: 0.5rem 0;
}
.critique-issue {
    background-color: #fff3cd;
    padding: 0.75rem;
    border-radius: 0.25rem;
    border-left: 4px solid #ffc107;
    margin: 0.5rem 0;
}
.success-box {
    background-color: #d4edda;
    padding: 0.75rem;
    border-radius: 0.25rem;
    border-left: 4px solid #28a745;
    margin: 0.5rem 0;
}
</style>
""", unsafe_allow_html=True)

class ATSApp:
    """Main ATS Application Class"""
    
    def __init__(self):
        self.initialize_session_state()
        self.initialize_components()
        # Initialize default settings
        self.critique_mode = "Full Analysis"
    
    def initialize_session_state(self):
        """Initialize session state variables"""
        if 'processed_resume' not in st.session_state:
            st.session_state.processed_resume = None
        if 'processed_jd' not in st.session_state:
            st.session_state.processed_jd = None
        if 'candidate_profile' not in st.session_state:
            st.session_state.candidate_profile = None
        if 'job_profile' not in st.session_state:
            st.session_state.job_profile = None
        if 'critiques' not in st.session_state:
            st.session_state.critiques = []
        if 'heuristic_report' not in st.session_state:
            st.session_state.heuristic_report = None
        if 'redrafted_resume' not in st.session_state:
            st.session_state.redrafted_resume = None
        if 'fit_analysis' not in st.session_state:
            st.session_state.fit_analysis = None
        if 'compliance_status' not in st.session_state:
            st.session_state.compliance_status = None
    
    def initialize_components(self):
        """Initialize all processing components"""
        with st.spinner("Initializing ATS components..."):
            try:
                self.processor = UniversalTextProcessor()
                self.index_manager = ATSIndexManager(persist_directory="./indexes")
                self.retriever = HybridRetriever(self.index_manager)
                self.profile_extractor = ProfileExtractor()
                self.heuristic_checker = HeuristicChecker()
                self.redraft_engine = RedraftEngine()
                self.fit_analyzer = FitAnalyzer()
                self.guardrails = GuardrailsSystem()
                
                # Initialize critique engine if API key available
                groq_api_key = os.getenv('GROQ_API_KEY')
                if groq_api_key:
                    self.critique_engine = CritiqueEngine(groq_api_key)
                    self.llm_available = True
                else:
                    self.critique_engine = None  # Don't initialize without API key
                    self.llm_available = False
                
            except Exception as e:
                st.error(f"Failed to initialize components: {e}")
                st.error("Please check your setup and try again.")
                st.stop()

    def run(self):
        """Main application entry point"""
        
        # Header
        st.markdown('<h1 class="main-header">🎯 TalentLens</h1>', unsafe_allow_html=True)
        st.markdown('<p style="text-align: center; font-size: 1.2rem; color: #666;">Candidate-Centric ATS - Helping Talent Succeed</p>', unsafe_allow_html=True)
        
        # Sidebar navigation
        self.render_sidebar()
        
        # Main content area
        tab1, tab2, tab3, tab4 = st.tabs(["📝 Resume Analysis", "🔍 Critique Results", "✨ Redrafted Resume", "🎯 Role & Company Fit"])
        
        with tab1:
            self.render_input_tab()
        
        with tab2:
            self.render_critique_tab()
        
        with tab3:
            self.render_redraft_tab()
        
        with tab4:
            self.render_fit_tab()

    def render_sidebar(self):
        """Render sidebar with controls and status"""
        st.sidebar.markdown("### 📊 Analysis Pipeline")
        
        # Status indicators
        pipeline_status = {
            "Resume Processed": st.session_state.processed_resume is not None,
            "Profile Extracted": st.session_state.candidate_profile is not None,
            "Heuristics Run": st.session_state.heuristic_report is not None,
            "Critiques Generated": len(st.session_state.critiques) > 0,
            "Resume Redrafted": st.session_state.redrafted_resume is not None,
            "Fit Analysis Done": st.session_state.fit_analysis is not None
        }
        
        for step, completed in pipeline_status.items():
            status_icon = "✅" if completed else "⏳"
            st.sidebar.markdown(f"{status_icon} {step}")
        
        st.sidebar.markdown("---")
        
        # API Status
        if self.llm_available:
            st.sidebar.success("🤖 Groq LLM: Connected")
        else:
            st.sidebar.warning("🤖 Groq LLM: Not connected")
            st.sidebar.info("Set GROQ_API_KEY for full functionality")
        
        st.sidebar.markdown("---")
        
        # Settings
        st.sidebar.markdown("### ⚙️ Settings")
        self.critique_mode = st.sidebar.selectbox(
            "Critique Mode",
            ["Full Analysis", "Heuristics Only", "Quick Review"]
        )
        
        st.sidebar.markdown("---")
        
        # Compliance Status
        st.sidebar.markdown("### 🔒 Compliance Status")
        if st.session_state.compliance_status:
            status = st.session_state.compliance_status
            if status == 'compliant':
                st.sidebar.success("✅ Fully Compliant")
            elif status == 'caution':
                st.sidebar.warning("⚠️ Minor Issues")
            elif status == 'review_required':
                st.sidebar.error("🚨 Review Required")
            else:
                st.sidebar.info("🔄 Checking...")
        else:
            st.sidebar.info("🔄 Not Checked")
        
        st.sidebar.markdown("---")
        
        # Reset button
        if st.sidebar.button("🔄 Reset Analysis"):
            self.reset_session_state()
            st.rerun()

    def reset_session_state(self):
        """Reset all session state variables"""
        for key in list(st.session_state.keys()):
            del st.session_state[key]

    def render_input_tab(self):
        """Render the main input and analysis tab"""
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.markdown('<h3 class="section-header">📄 Resume Input</h3>', unsafe_allow_html=True)
        
            # Add PDF upload option
            upload_option = st.radio(
                "Choose input method:",
                ["Type/Paste Text", "Upload PDF"],
                horizontal=True
            )
        
            if upload_option == "Upload PDF":
                from pdf_processor import process_pdf_upload
                resume_text = process_pdf_upload()
                if not resume_text:
                    resume_text = ""
            else:
                resume_text = st.text_area(
                    "Paste your resume here:",
                    height=300,
                    placeholder="Paste your resume content..."
                )
            
        with col2:
            st.markdown('<h3 class="section-header">📋 Job Description (Optional)</h3>', unsafe_allow_html=True)
            
            jd_text = st.text_area(
                "Paste job description here:",
                height=300,
                placeholder="""Example:
Senior Software Engineer
TechCorp Inc.

REQUIREMENTS
• 5+ years of Python development experience
• Experience with cloud platforms (AWS preferred)
• Strong background in database optimization
• Leadership experience with small teams

NICE TO HAVE
• Machine learning background
• Kubernetes experience"""
            )
        
        # Analysis button
        if st.button("🚀 Analyze Resume", type="primary", use_container_width=True):
            if resume_text.strip():
                self.process_resume_analysis(resume_text, jd_text)
            else:
                st.error("Please enter a resume to analyze.")
        
        # Show quick stats if analysis is done
        if st.session_state.processed_resume:
            self.render_quick_stats()

    def process_resume_analysis(self, resume_text, jd_text=""):
        """Process the complete resume analysis pipeline"""
        
        progress_bar = st.progress(0)
        status_text = st.empty()
        
        try:
            # Use original resume text directly - skip unnecessary guardrails for now
            cleaned_resume_text = resume_text
            st.session_state.compliance_status = 'compliant'
            
            # Step 1: Process resume text
            status_text.text("🔄 Processing resume text...")
            progress_bar.progress(10)
            
            processed_resume = self.processor.process_resume(cleaned_resume_text)
            st.session_state.processed_resume = processed_resume
            
            # Step 2: Extract candidate profile
            status_text.text("🔄 Extracting candidate profile...")
            progress_bar.progress(20)
            
            candidate_profile = self.profile_extractor.extract_candidate_profile(processed_resume)
            st.session_state.candidate_profile = candidate_profile
            
            # Step 3: Process JD if provided
            job_profile = None
            if jd_text.strip():
                status_text.text("🔄 Processing job description...")
                progress_bar.progress(30)
                
                processed_jd = self.processor.process_job_description(jd_text)
                st.session_state.processed_jd = processed_jd
                
                job_profile = self.profile_extractor.extract_job_profile(processed_jd)
                st.session_state.job_profile = job_profile
                
                # Index JD for retrieval
                self.index_manager.index_job_description(processed_jd, jd_id="target_job")
            
            # Step 4: Index resume
            status_text.text("🔄 Indexing resume for analysis...")
            progress_bar.progress(40)
            
            self.index_manager.index_resume(processed_resume, resume_id="candidate")
            
            # Step 5: Run heuristic checks
            status_text.text("🔄 Running quality checks...")
            progress_bar.progress(50)
            
            heuristic_report = self.heuristic_checker.check_resume_lines(processed_resume)
            st.session_state.heuristic_report = heuristic_report
            
            # Step 6: Generate critiques (if enabled)
            critiques = []
            if self.llm_available:
                status_text.text("🔄 Generating detailed critiques...")
                progress_bar.progress(70)
    
                try:
                    critiques = self.generate_critiques(processed_resume, heuristic_report, job_profile)
                    st.session_state.critiques = critiques
        
                    if len(critiques) == 0:
                        st.warning("No critiques generated. Check that your resume has bullet points.")
                except Exception as e:
                    st.error(f"Critique generation failed: {str(e)}")
                    with st.expander("Critique Error Details"):
                        st.code(traceback.format_exc())
            else:
                st.warning("⚠️ Critique engine requires GROQ_API_KEY")
                st.info("Set the GROQ_API_KEY environment variable to enable detailed analysis")

            
            # Step 7: Generate redraft
            status_text.text("🔄 Creating improved resume...")
            progress_bar.progress(80)
            
            redrafted_resume = self.redraft_engine.redraft_resume(
                processed_resume, critiques, candidate_profile, job_profile
            )
            st.session_state.redrafted_resume = redrafted_resume
            
            # Step 8: Analyze fit
            status_text.text("🔄 Analyzing role and company fit...")
            progress_bar.progress(90)
            
            fit_analysis = self.fit_analyzer.analyze_candidate_fit(candidate_profile, job_profile)
            st.session_state.fit_analysis = fit_analysis
            
            # Complete
            progress_bar.progress(100)
            status_text.text("✅ Analysis complete!")
            
            st.success("🎉 Resume analysis completed successfully!")
            
        except Exception as e:
            st.error(f"Analysis failed: {str(e)}")
            st.error("Please check your input and try again.")
            with st.expander("Error Details"):
                st.code(traceback.format_exc())

    def generate_critiques(self, processed_resume, heuristic_report, job_profile=None):
        """FIXED: Generate critiques for resume lines - ALWAYS RUN, even without heuristic flags"""
        critiques = []
    
        # Focus on experience and project bullets - GET ALL
        lines_to_critique = [
            line for line in processed_resume 
            if line.section.value in ['experience', 'projects'] and line.is_bullet
        ]
    
        # Debug output
        st.write(f"🔍 Found {len(lines_to_critique)} bullet points to analyze")
    
        if not lines_to_critique:
            st.warning("⚠️ No bullet points found in Experience or Projects sections")
            st.info("Make sure your resume has bullet points (•, -, *) in the Experience section")
            return critiques
    
        # Limit to 10 lines to avoid rate limits
        lines_to_critique = lines_to_critique[:10]
    
        # Progress indicator
        critique_progress = st.progress(0)
        critique_status = st.empty()
    
        for idx, line in enumerate(lines_to_critique):
            try:
                critique_status.text(f"Analyzing bullet {idx + 1} of {len(lines_to_critique)}...")
                critique_progress.progress((idx + 1) / len(lines_to_critique))
            
                # Get context pack
                try:
                    context_pack = self.retriever.build_context_pack(
                        line.text, 
                        f"candidate_L{line.line_number:03d}"
                    )
                except Exception as e:
                    # Create empty context pack if retrieval fails
                    from retriever import ContextPack
                    context_pack = ContextPack(
                        resume_neighbors=[],
                        jd_requirements=[],
                        metadata={"error": str(e)}
                    )
            
                # Get heuristic flags for this line (may be empty - that's OK!)
                heuristic_flags = heuristic_report.line_flags.get(line.line_number, [])
            
                # CRITICAL: Generate critique REGARDLESS of heuristic flags
                # Even "good" bullets should get optimization suggestions
                critique = self.critique_engine.critique_resume_line(
                    line.text, line.line_number, context_pack, heuristic_flags, job_profile
                )
            
                critiques.append(critique)
            
            except Exception as e:
                st.warning(f"Could not critique line {line.line_number}: {str(e)}")
                continue
    
        critique_progress.progress(1.0)
        critique_status.text(f"✅ Analyzed {len(critiques)} bullet points")
    
        return critiques

    def render_quick_stats(self):
        """Render quick statistics after analysis"""
        
        if not st.session_state.heuristic_report:
            return
        
        st.markdown('<h3 class="section-header">📊 Quick Stats</h3>', unsafe_allow_html=True)
        
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            st.metric(
                "Lines Analyzed",
                st.session_state.heuristic_report.total_lines_checked
            )
        
        with col2:
            st.metric(
                "Issues Found",
                st.session_state.heuristic_report.total_flags
            )
        
        with col3:
            score = st.session_state.heuristic_report.overall_score
            st.metric(
                "Quality Score",
                f"{score:.2f}/1.00",
                delta=f"{(score - 0.5):.2f}" if score != 0.5 else None
            )
        
        with col4:
            if st.session_state.redrafted_resume:
                improvement_count = st.session_state.redrafted_resume.improvement_summary.get('lines_improved', 0)
                st.metric(
                    "Lines Improved",
                    improvement_count
                )

    def render_critique_tab(self):
        """Render the critique results tab"""
        
        if not st.session_state.heuristic_report:
            st.info("📝 Run resume analysis first to see critique results.")
            return
        
        st.markdown('<h3 class="section-header">🔍 Quality Analysis Results</h3>', unsafe_allow_html=True)
        
        # Heuristic analysis summary
        report = st.session_state.heuristic_report
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.markdown("#### Severity Breakdown")
            for severity, count in report.flags_by_severity.items():
                if count > 0:
                    st.markdown(f"**{severity.value.title()}**: {count}")
        
        with col2:
            st.markdown("#### Issue Types")
            for issue_type, count in report.flags_by_type.items():
                if count > 0:
                    st.markdown(f"**{issue_type.value.replace('_', ' ').title()}**: {count}")
        
        # Line-by-line critiques
        if st.session_state.critiques:
            st.markdown('<h4 class="section-header">📝 Line-by-Line Critiques</h4>', unsafe_allow_html=True)
            
            for critique in st.session_state.critiques:
                with st.expander(f"Line {critique.line_number}: {critique.original_text[:60]}..."):
                    
                    # Assessment
                    assessment_color = {
                        "good": "success",
                        "needs_improvement": "warning", 
                        "major_issues": "error",
                        "flagged_for_review": "error"
                    }
                    
                    st.markdown(f"**Assessment**: :{assessment_color.get(critique.overall_assessment, 'info')}[{critique.overall_assessment.replace('_', ' ').title()}]")
                    
                    # Issues
                    if critique.issues:
                        st.markdown("**Issues Found:**")
                        for issue in critique.issues:
                            st.markdown(f"- **{issue.type.replace('_', ' ').title()}** ({issue.severity}): {issue.explanation}")
                    
                    # Suggested rewrite
                    if critique.suggested_rewrite != critique.original_text:
                        st.markdown("**Suggested Improvement:**")
                        st.code(critique.suggested_rewrite)
                        
                        st.markdown("**Reasoning:**")
                        st.write(critique.rewrite_reasoning)

    def render_redraft_tab(self):
        """Render the redrafted resume tab"""
        
        if not st.session_state.redrafted_resume:
            st.info("📝 Run resume analysis first to see the redrafted version.")
            return
        
        redraft = st.session_state.redrafted_resume
        
        st.markdown('<h3 class="section-header">✨ Improved Resume</h3>', unsafe_allow_html=True)
        
        # Summary stats
        col1, col2, col3 = st.columns(3)
        
        with col1:
            st.metric("Total Word Count", redraft.total_word_count)
        
        with col2:
            st.metric("Total Bullets", redraft.total_bullet_count)
        
        with col3:
            lines_improved = redraft.improvement_summary.get('lines_improved', 0)
            st.metric("Lines Improved", lines_improved)
        
        # Improvement summary
        if any(count > 0 for count in redraft.improvement_summary.values()):
            st.markdown("#### Improvements Made")
            for improvement, count in redraft.improvement_summary.items():
                if count > 0:
                    st.markdown(f"- **{improvement.replace('_', ' ').title()}**: {count}")
        
        # Evidence placeholders
        if redraft.evidence_placeholders:
            st.markdown("#### Evidence Needed")
            st.warning("Fill in these placeholders with specific data:")
            for placeholder in redraft.evidence_placeholders:
                st.markdown(f"- {placeholder}")
        
        # Formatted resume
        st.markdown("#### Redrafted Resume")
        
        # Export options
        col1, col2 = st.columns(2)
        with col1:
            if st.button("📋 Show Markdown Code"):
                markdown_content = self.redraft_engine.export_to_markdown(redraft)
                st.code(markdown_content, language="markdown")
    
        with col2:
            markdown_content = self.redraft_engine.export_to_markdown(redraft)
            st.download_button(
                label="💾 Download Resume",
                data=markdown_content,
                file_name=f"{redraft.candidate_name.replace(' ', '_')}_improved_resume.md",
                mime="text/markdown"
            )
    
        # Display as formatted content (not raw markdown)
        st.markdown("---")
        markdown_content = self.redraft_engine.export_to_markdown(redraft)
    
        # Process and display the markdown properly
        lines = markdown_content.split('\n')
        for line in lines:
            if line.startswith('# '):
                st.markdown(f"## {line[2:]}")  # Convert to h2 for better display
            elif line.startswith('## '):
                st.markdown(f"### {line[3:]}")  # Convert to h3
            elif line.startswith('• '):
                st.markdown(f"- {line[2:]}")  # Convert bullets to markdown lists
            elif line.strip():
                st.markdown(line)

    def render_fit_tab(self):
        """Render the role and company fit tab"""
        
        if not st.session_state.fit_analysis:
            st.info("📝 Run resume analysis first to see fit recommendations.")
            return
        
        analysis = st.session_state.fit_analysis
        
        st.markdown('<h3 class="section-header">🎯 Role & Company Fit Analysis</h3>', unsafe_allow_html=True)
        
        # Overview
        col1, col2, col3 = st.columns(3)
        
        with col1:
            st.metric("Career Stage", analysis.career_stage.title())
        
        with col2:
            st.metric("Marketability", analysis.overall_marketability.title())
        
        with col3:
            if analysis.top_role_fits:
                best_fit_score = analysis.top_role_fits[0].fit_score
                st.metric("Best Role Fit", f"{best_fit_score:.2f}")
        
        # Role recommendations
        st.markdown("#### 🎯 Top Role Recommendations")
        
        for i, role in enumerate(analysis.top_role_fits, 1):
            with st.expander(f"{i}. {role.role_title} (Fit: {role.fit_confidence.value.title()})"):
                
                col1, col2 = st.columns(2)
                
                with col1:
                    st.markdown("**Why Good Fit:**")
                    for reason in role.why_good_fit:
                        st.markdown(f"- {reason}")
                    
                    if role.matching_skills:
                        st.markdown("**Matching Skills:**")
                        st.markdown(", ".join(role.matching_skills))
                
                with col2:
                    st.markdown(f"**Salary Range:** {role.salary_range}")
                    st.markdown(f"**Growth Potential:** {role.growth_potential}")
                    
                    if role.skill_gaps:
                        st.markdown("**Skills to Develop:**")
                        for gap in role.skill_gaps[:3]:
                            st.markdown(f"- {gap.skill_name} ({gap.learning_timeline})")
        
        # Company recommendations
        st.markdown("#### 🏢 Top Company Type Recommendations")
        
        for i, company in enumerate(analysis.top_company_fits, 1):
            with st.expander(f"{i}. {company.company_type} (Fit: {company.fit_confidence.value.title()})"):
                
                col1, col2 = st.columns(2)
                
                with col1:
                    st.markdown("**Why Good Fit:**")
                    for reason in company.why_good_fit:
                        st.markdown(f"- {reason}")
                    
                    st.markdown("**Work Environment:**")
                    st.markdown(company.work_environment)
                
                with col2:
                    st.markdown("**Example Companies:**")
                    st.markdown(", ".join(company.company_examples))
                    
                    st.markdown("**Typical Benefits:**")
                    for benefit in company.typical_benefits:
                        st.markdown(f"- {benefit}")
        
        # Recommendations
        if analysis.recommended_focus_areas:
            st.markdown("#### 💡 Focus Recommendations")
            for rec in analysis.recommended_focus_areas:
                st.markdown(f"- {rec}")
        
        # Market positioning
        st.markdown("#### 📈 Market Positioning")
        st.info(analysis.market_positioning)

def main():
    """Main application entry point"""
    try:
        app = ATSApp()
        app.run()
    except Exception as e:
        st.error(f"Application failed to start: {e}")
        st.error("Please check your setup and restart the application.")
        with st.expander("Error Details"):
            st.code(traceback.format_exc())

if __name__ == "__main__":
    main()
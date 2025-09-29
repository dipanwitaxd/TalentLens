# src/retriever.py
# Phase 3: Retrievers & Grounding Strategy
# Goal: Reliable hybrid retrieval with good citations

from typing import List, Dict, Any, Tuple, Optional
from dataclasses import dataclass
import numpy as np
from src.index_manager import ATSIndexManager

@dataclass
class RetrievalResult:
    """Single retrieval result with metadata"""
    id: str
    text: str
    score: float
    metadata: Dict[str, Any]
    source_type: str  # "vector" or "bm25"
    section: str
    line_number: int

@dataclass
class ContextPack:
    """Complete context package for critiquing a resume line"""
    target_line: str
    target_line_id: str
    resume_neighbors: List[RetrievalResult]
    jd_requirements: List[RetrievalResult]
    section_context: Dict[str, Any]
    retrieval_stats: Dict[str, int]

class HybridRetriever:
    """Combines vector and BM25 search for optimal retrieval"""
    
    def __init__(self, index_manager: ATSIndexManager):
        self.index_manager = index_manager
        
        # Retrieval parameters (tunable)
        self.vector_top_k = 6
        self.bm25_top_k = 6
        self.final_top_k = 8
        
        # Fusion weights
        self.vector_weight = 0.6
        self.bm25_weight = 0.4
        
        # Section importance weights
        self.section_weights = {
            "experience": 0.4,
            "skills": 0.3,
            "projects": 0.2,
            "education": 0.1,
            "summary": 0.15,
            "certifications": 0.1
        }

    def retrieve_resume_context(self, query: str, target_line_id: str = None) -> List[RetrievalResult]:
        """Retrieve relevant resume lines using hybrid search"""
        
        # Get vector search results
        vector_results = self._vector_search_resume(query, self.vector_top_k)
        
        # Get BM25 search results
        bm25_results = self._bm25_search_resume(query, self.bm25_top_k)
        
        # Combine using Reciprocal Rank Fusion
        combined_results = self._reciprocal_rank_fusion(
            vector_results, bm25_results, target_line_id
        )
        
        return combined_results[:self.final_top_k]

    def retrieve_jd_requirements(self, query: str) -> List[RetrievalResult]:
        """Retrieve relevant job description requirements"""
        
        # JD search (usually smaller, so lower K values)
        vector_results = self._vector_search_jd(query, k=4)
        bm25_results = self._bm25_search_jd(query, k=4)
        
        # Combine results
        combined_results = self._reciprocal_rank_fusion(
            vector_results, bm25_results
        )
        
        return combined_results[:5]  # Top 5 JD requirements

    def build_context_pack(self, target_line: str, target_line_id: str, 
                          jd_context: str = None) -> ContextPack:
        """Build complete context package for critiquing a resume line"""
        
        # Extract target line metadata
        target_metadata = self._get_line_metadata(target_line_id)
        
        # Get resume neighbors (similar + nearby lines)
        resume_neighbors = self._get_resume_neighbors(target_line, target_line_id)
        
        # Get relevant JD requirements
        jd_requirements = []
        if jd_context:
            jd_requirements = self.retrieve_jd_requirements(target_line)
        
        # Build section context
        section_context = self._build_section_context(target_line_id, target_metadata)
        
        # Retrieval statistics
        stats = {
            "resume_neighbors": len(resume_neighbors),
            "jd_requirements": len(jd_requirements),
            "vector_results": sum(1 for r in resume_neighbors if r.source_type == "vector"),
            "bm25_results": sum(1 for r in resume_neighbors if r.source_type == "bm25")
        }
        
        return ContextPack(
            target_line=target_line,
            target_line_id=target_line_id,
            resume_neighbors=resume_neighbors,
            jd_requirements=jd_requirements,
            section_context=section_context,
            retrieval_stats=stats
        )

    def _vector_search_resume(self, query: str, k: int) -> List[RetrievalResult]:
        """Vector search in resume collection"""
        try:
            results = self.index_manager.resume_collection.query(
                query_texts=[query],
                n_results=k,
                include=['documents', 'metadatas', 'distances']
            )
            
            vector_results = []
            if results['ids'][0]:  # Check if we got results
                for i in range(len(results['ids'][0])):
                    result = RetrievalResult(
                        id=results['ids'][0][i],
                        text=results['documents'][0][i],
                        score=1.0 - results['distances'][0][i],  # Convert distance to similarity
                        metadata=results['metadatas'][0][i],
                        source_type="vector",
                        section=results['metadatas'][0][i].get('section', 'unknown'),
                        line_number=results['metadatas'][0][i].get('line_number', 0)
                    )
                    vector_results.append(result)
            
            return vector_results
            
        except Exception as e:
            print(f"Vector search error: {e}")
            return []

    def _bm25_search_resume(self, query: str, k: int) -> List[RetrievalResult]:
        """BM25 search in resume collection"""
        try:
            if not self.index_manager.resume_bm25:
                return []
            
            # Tokenize query
            query_tokens = self.index_manager._tokenize_for_bm25(query)
            
            # Get BM25 scores
            scores = self.index_manager.resume_bm25.get_scores(query_tokens)
            
            # Get top K results
            top_indices = np.argsort(scores)[::-1][:k]
            
            bm25_results = []
            for idx in top_indices:
                if scores[idx] > 0:  # Only include positive scores
                    doc = self.index_manager.resume_docs[idx]
                    result = RetrievalResult(
                        id=doc.id,
                        text=doc.text,
                        score=scores[idx],
                        metadata=doc.metadata,
                        source_type="bm25",
                        section=doc.metadata.get('section', 'unknown'),
                        line_number=doc.metadata.get('line_number', 0)
                    )
                    bm25_results.append(result)
            
            return bm25_results
            
        except Exception as e:
            print(f"BM25 search error: {e}")
            return []

    def _vector_search_jd(self, query: str, k: int) -> List[RetrievalResult]:
        """Vector search in JD collection"""
        try:
            results = self.index_manager.jd_collection.query(
                query_texts=[query],
                n_results=k,
                include=['documents', 'metadatas', 'distances']
            )
            
            vector_results = []
            if results['ids'][0]:
                for i in range(len(results['ids'][0])):
                    result = RetrievalResult(
                        id=results['ids'][0][i],
                        text=results['documents'][0][i],
                        score=1.0 - results['distances'][0][i],
                        metadata=results['metadatas'][0][i],
                        source_type="vector",
                        section=results['metadatas'][0][i].get('section', 'unknown'),
                        line_number=results['metadatas'][0][i].get('line_number', 0)
                    )
                    vector_results.append(result)
            
            return vector_results
            
        except Exception as e:
            print(f"JD vector search error: {e}")
            return []

    def _bm25_search_jd(self, query: str, k: int) -> List[RetrievalResult]:
        """BM25 search in JD collection"""
        try:
            if not self.index_manager.jd_bm25:
                return []
            
            query_tokens = self.index_manager._tokenize_for_bm25(query)
            scores = self.index_manager.jd_bm25.get_scores(query_tokens)
            top_indices = np.argsort(scores)[::-1][:k]
            
            bm25_results = []
            for idx in top_indices:
                if scores[idx] > 0:
                    doc = self.index_manager.jd_docs[idx]
                    result = RetrievalResult(
                        id=doc.id,
                        text=doc.text,
                        score=scores[idx],
                        metadata=doc.metadata,
                        source_type="bm25",
                        section=doc.metadata.get('section', 'unknown'),
                        line_number=doc.metadata.get('line_number', 0)
                    )
                    bm25_results.append(result)
            
            return bm25_results
            
        except Exception as e:
            print(f"JD BM25 search error: {e}")
            return []

    def _reciprocal_rank_fusion(self, vector_results: List[RetrievalResult], 
                              bm25_results: List[RetrievalResult],
                              exclude_id: str = None) -> List[RetrievalResult]:
        """Combine vector and BM25 results using Reciprocal Rank Fusion"""
        
        # Create score dictionary
        fusion_scores = {}
        all_results = {}
        
        # Add vector results with rank-based scoring
        for rank, result in enumerate(vector_results):
            if exclude_id and result.id == exclude_id:
                continue  # Skip the target line itself
                
            fusion_scores[result.id] = self.vector_weight / (rank + 1)
            all_results[result.id] = result
        
        # Add BM25 results with rank-based scoring
        for rank, result in enumerate(bm25_results):
            if exclude_id and result.id == exclude_id:
                continue
                
            if result.id in fusion_scores:
                fusion_scores[result.id] += self.bm25_weight / (rank + 1)
            else:
                fusion_scores[result.id] = self.bm25_weight / (rank + 1)
                all_results[result.id] = result
        
        # Apply section weighting
        for doc_id, base_score in fusion_scores.items():
            section = all_results[doc_id].section
            section_boost = self.section_weights.get(section, 0.1)
            fusion_scores[doc_id] = base_score * (1 + section_boost)
        
        # Sort by final score
        sorted_ids = sorted(fusion_scores.keys(), key=lambda x: fusion_scores[x], reverse=True)
        
        # Return ranked results with updated scores
        final_results = []
        for doc_id in sorted_ids:
            result = all_results[doc_id]
            result.score = fusion_scores[doc_id]  # Update with fusion score
            final_results.append(result)
        
        return final_results

    def _get_resume_neighbors(self, target_line: str, target_line_id: str) -> List[RetrievalResult]:
        """Get neighboring resume lines (similar + nearby)"""
        
        # Get semantically similar lines
        similar_lines = self.retrieve_resume_context(target_line, target_line_id)
        
        # Get neighboring lines from same section/job
        nearby_lines = self._get_nearby_lines(target_line_id)
        
        # Combine and deduplicate
        all_neighbors = {result.id: result for result in similar_lines}
        for result in nearby_lines:
            if result.id not in all_neighbors:
                all_neighbors[result.id] = result
        
        # Return top results sorted by relevance
        return sorted(all_neighbors.values(), key=lambda x: x.score, reverse=True)[:6]

    def _get_nearby_lines(self, target_line_id: str) -> List[RetrievalResult]:
        """Get lines that are physically nearby in the resume"""
        try:
            # Parse target line number
            target_line_num = int(target_line_id.split('_L')[1])
            
            # Get lines within +/- 2 positions
            nearby_results = []
            for offset in [-2, -1, 1, 2]:
                nearby_line_num = target_line_num + offset
                nearby_id = target_line_id.replace(f'L{target_line_num:03d}', f'L{nearby_line_num:03d}')
                
                # Try to find this line in our indexes
                line_data = self._get_line_by_id(nearby_id)
                if line_data:
                    result = RetrievalResult(
                        id=nearby_id,
                        text=line_data['text'],
                        score=0.5,  # Medium relevance for nearby lines
                        metadata=line_data['metadata'],
                        source_type="neighbor",
                        section=line_data['metadata'].get('section', 'unknown'),
                        line_number=nearby_line_num
                    )
                    nearby_results.append(result)
            
            return nearby_results
            
        except Exception as e:
            print(f"Error getting nearby lines: {e}")
            return []

    def _get_line_by_id(self, line_id: str) -> Optional[Dict]:
        """Get a specific line by its ID"""
        try:
            # Try vector store first
            results = self.index_manager.resume_collection.get(
                ids=[line_id],
                include=['documents', 'metadatas']
            )
            
            if results['ids']:
                return {
                    'text': results['documents'][0],
                    'metadata': results['metadatas'][0]
                }
            
            return None
            
        except Exception as e:
            return None

    def _get_line_metadata(self, line_id: str) -> Dict[str, Any]:
        """Get metadata for a specific line"""
        line_data = self._get_line_by_id(line_id)
        return line_data['metadata'] if line_data else {}

    def _build_section_context(self, target_line_id: str, target_metadata: Dict) -> Dict[str, Any]:
        """Build section-level context for the target line"""
        return {
            "target_section": target_metadata.get('section', 'unknown'),
            "target_line_number": target_metadata.get('line_number', 0),
            "has_metrics": target_metadata.get('has_metrics', False),
            "is_bullet": target_metadata.get('is_bullet', False),
            "action_verbs": target_metadata.get('action_verbs', [])
        }

    def test_retrieval_quality(self, test_queries: List[str]) -> Dict[str, Any]:
        """Test retrieval quality with sample queries"""
        results = {
            "queries_tested": len(test_queries),
            "avg_results_per_query": 0,
            "vector_vs_bm25_overlap": 0,
            "sample_results": {}
        }
        
        total_results = 0
        total_overlap = 0
        
        for query in test_queries:
            # Get separate results
            vector_results = self._vector_search_resume(query, 5)
            bm25_results = self._bm25_search_resume(query, 5)
            
            # Calculate overlap
            vector_ids = {r.id for r in vector_results}
            bm25_ids = {r.id for r in bm25_results}
            overlap = len(vector_ids & bm25_ids) / max(len(vector_ids | bm25_ids), 1)
            
            total_results += len(vector_results) + len(bm25_results)
            total_overlap += overlap
            
            # Store sample
            results["sample_results"][query] = {
                "vector_count": len(vector_results),
                "bm25_count": len(bm25_results),
                "overlap": overlap,
                "top_result": vector_results[0].text if vector_results else "No results"
            }
        
        results["avg_results_per_query"] = total_results / len(test_queries) if test_queries else 0
        results["vector_vs_bm25_overlap"] = total_overlap / len(test_queries) if test_queries else 0
        
        return results


# Testing and validation functions
def test_hybrid_retrieval():
    """Test the hybrid retrieval system"""
    print("=== TESTING HYBRID RETRIEVAL (Phase 3) ===")
    
    # This assumes you have already run Phases 1 & 2
    from src.index_manager import ATSIndexManager
    
    # Initialize
    index_manager = ATSIndexManager(persist_directory="./indexes")
    index_manager.load_indexes()  # Load existing indexes
    
    retriever = HybridRetriever(index_manager)
    
    # Test queries
    test_queries = [
        "Python machine learning",
        "team leadership management", 
        "database optimization performance",
        "cloud infrastructure AWS",
        "project management agile"
    ]
    
    print("Testing retrieval quality...")
    quality_results = retriever.test_retrieval_quality(test_queries)
    
    print(f"Queries tested: {quality_results['queries_tested']}")
    print(f"Avg results per query: {quality_results['avg_results_per_query']:.1f}")
    print(f"Vector/BM25 overlap: {quality_results['vector_vs_bm25_overlap']:.2f}")
    
    # Test context pack building
    print("\nTesting context pack building...")
    sample_line = "Built scalable Python applications serving 10K+ users daily"
    sample_id = "john_doe_L001"  # Adjust based on your data
    
    try:
        context_pack = retriever.build_context_pack(sample_line, sample_id)
        
        print(f"Context pack created:")
        print(f"  Target line: {context_pack.target_line}")
        print(f"  Resume neighbors: {context_pack.retrieval_stats['resume_neighbors']}")
        print(f"  JD requirements: {context_pack.retrieval_stats['jd_requirements']}")
        print(f"  Vector results: {context_pack.retrieval_stats['vector_results']}")
        print(f"  BM25 results: {context_pack.retrieval_stats['bm25_results']}")
        
        # Show sample neighbors
        print("\nSample neighbors:")
        for i, neighbor in enumerate(context_pack.resume_neighbors[:3]):
            print(f"  {i+1}. [{neighbor.source_type}] {neighbor.text[:60]}...")
            
    except Exception as e:
        print(f"Error building context pack: {e}")

if __name__ == "__main__":
    test_hybrid_retrieval()
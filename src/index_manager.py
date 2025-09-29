# Phase 2: Indexing for RAG - Step by Step Implementation
# Goal: Create searchable vector + BM25 indexes for resume lines and JD bullets

import os
import pickle
from typing import List, Dict, Any, Tuple
from dataclasses import dataclass
import chromadb
from chromadb.config import Settings
from rank_bm25 import BM25Okapi
from sentence_transformers import SentenceTransformer

import re

@dataclass
class IndexedDocument:
    """Represents a document in our indexes"""
    id: str
    text: str
    metadata: Dict[str, Any]
    embedding: List[float] = None

class ATSIndexManager:
    """Manages both vector and BM25 indexes for resume lines and JD bullets"""
    
    def __init__(self, persist_directory: str = "./ats_indexes"):
        self.persist_directory = persist_directory
        os.makedirs(persist_directory, exist_ok=True)
        
        # Initialize embedding model (lightweight but effective)
        print("Loading embedding model...")
        self.embedding_model = SentenceTransformer('all-MiniLM-L6-v2')
        print("✅ Embedding model loaded!")
        
        # Initialize ChromaDB for vector storage
        self.chroma_client = chromadb.PersistentClient(
            path=os.path.join(persist_directory, "chroma_db"),
            settings=Settings(anonymized_telemetry=False)
        )
        
        # Create collections for resume and JD
        self.resume_collection = self._get_or_create_collection("resume_lines")
        self.jd_collection = self._get_or_create_collection("jd_bullets")
        
        # BM25 indexes (will be loaded/saved as pickle files)
        self.resume_bm25 = None
        self.jd_bm25 = None
        self.resume_docs = []  # Store docs for BM25 reference
        self.jd_docs = []
        
        self.stop_words = {
            'the', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 'for', 'of', 'with', 'by',
            'is', 'are', 'was', 'were', 'a', 'an', 'this', 'that', 'these', 'those',
            'i', 'you', 'he', 'she', 'it', 'we', 'they', 'me', 'him', 'her', 'us', 'them'
        }
        
        print("✅ Index Manager initialized!")

    def _get_or_create_collection(self, name: str):
        """Get existing collection or create new one"""
        try:
        # Try to get existing collection
            return self.chroma_client.get_collection(name)
        except Exception:
        # If it doesn't exist, create it
            print(f"Creating new collection: {name}")
            return self.chroma_client.create_collection(
            name=name,
            metadata={"hnsw:space": "cosine"}
            )

    def index_resume(self, processed_lines: List['ProcessedLine'], resume_id: str = "default"):
        """Index all resume lines for retrieval - FIXED VERSION"""
        print(f"Indexing resume: {resume_id}")
    
        # Clear existing data for this resume
        self._clear_resume_index(resume_id)
    
        # Prepare documents for indexing
        resume_docs = []
        vector_docs = []
    
        for line in processed_lines:
            # Only index meaningful content (skip headers, contact info)
            if self._should_index_line(line):
                doc_id = f"{resume_id}_L{line.line_number:03d}"
            
                # FIXED: Convert lists to strings for ChromaDB compatibility
                action_verbs = line.metadata.get("action_verbs", [])
                action_verbs_str = ",".join(action_verbs) if action_verbs else ""
            
                has_metrics_list = line.metadata.get("has_metrics", [])
                has_metrics_str = ",".join(has_metrics_list) if has_metrics_list else ""
            
                doc = IndexedDocument(
                    id=doc_id,
                    text=line.text,
                    metadata={
                        "resume_id": resume_id,
                        "line_number": line.line_number,
                        "section": line.section.value,
                        "is_bullet": line.is_bullet,
                        "has_metrics": bool(has_metrics_list),  # Boolean is OK
                        "metrics_found": has_metrics_str,  # String is OK
                        "action_verbs": action_verbs_str,  # String is OK
                        "word_count": line.metadata.get("word_count", 0)
                    }
                )
            
                resume_docs.append(doc)
            
                # Prepare for vector indexing
                vector_docs.append({
                    "id": doc_id,
                    "text": line.text,
                    "metadata": doc.metadata
                })
    
        # Index in ChromaDB (vector search)
        self._add_to_vector_index(vector_docs, self.resume_collection)
    
        # Index in BM25 (keyword search)
        self._build_bm25_index(resume_docs, index_type="resume")
    
        # Save BM25 index
        self._save_bm25_indexes()
    
        print(f"✅ Indexed {len(resume_docs)} resume lines")
        return len(resume_docs)
    
    def index_job_description(self, processed_lines: List['ProcessedLine'], jd_id: str = "default"):
        """Index job description bullets for retrieval - FIXED VERSION"""
        print(f"Indexing job description: {jd_id}")
    
        # Clear existing JD data
        self._clear_jd_index(jd_id)
    
        # Prepare JD documents
        jd_docs = []
        vector_docs = []
    
        for line in processed_lines:
            if self._should_index_line(line):
                doc_id = f"{jd_id}_JD{line.line_number:03d}"
            
                # FIXED: Convert lists to strings
                industry_terms = line.metadata.get("industry_terms", [])
                industry_terms_str = ",".join(industry_terms) if industry_terms else ""
            
                has_metrics_list = line.metadata.get("has_metrics", [])
                has_metrics_str = ",".join(has_metrics_list) if has_metrics_list else ""
            
                doc = IndexedDocument(
                    id=doc_id,
                    text=line.text,
                    metadata={
                        "jd_id": jd_id,
                        "line_number": line.line_number,
                        "section": line.section.value,
                        "is_bullet": line.is_bullet,
                        "has_metrics": bool(has_metrics_list),
                        "metrics_found": has_metrics_str,
                        "industry_terms": industry_terms_str,
                        "word_count": line.metadata.get("word_count", 0)
                    }
                )
            
                jd_docs.append(doc)
            
                vector_docs.append({
                    "id": doc_id,
                    "text": line.text,
                    "metadata": doc.metadata
                })
    
        # Index in both systems
        self._add_to_vector_index(vector_docs, self.jd_collection)
        self._build_bm25_index(jd_docs, index_type="jd")
        self._save_bm25_indexes()
    
        print(f"✅ Indexed {len(jd_docs)} JD bullets")
        return len(jd_docs)

    def _should_index_line(self, line: 'ProcessedLine') -> bool:
        """Determine if a line should be indexed"""
        # Skip contact info and very short lines
        if line.section.value == "contact" or len(line.text.strip()) < 10:
            return False
        
        # Skip pure section headers
        if not line.is_bullet and line.metadata.get("word_count", 0) < 5:
            return False
        
        return True

    def _add_to_vector_index(self, docs: List[Dict], collection):
        """Add documents to ChromaDB vector index"""
        if not docs:
            return
        
        # Generate embeddings
        texts = [doc["text"] for doc in docs]
        embeddings = self.embedding_model.encode(texts).tolist()
        
        # Add to ChromaDB
        collection.add(
            ids=[doc["id"] for doc in docs],
            documents=texts,
            metadatas=[doc["metadata"] for doc in docs],
            embeddings=embeddings
        )

    def _build_bm25_index(self, docs: List[IndexedDocument], index_type: str):
        """Build BM25 index for keyword search"""
        if not docs:
            return
        
        # Tokenize documents for BM25
        tokenized_docs = []
        for doc in docs:
            tokens = self._tokenize_for_bm25(doc.text)
            tokenized_docs.append(tokens)
        
        # Build BM25 index
        bm25_index = BM25Okapi(tokenized_docs)
        
        if index_type == "resume":
            self.resume_bm25 = bm25_index
            self.resume_docs = docs
        else:
            self.jd_bm25 = bm25_index
            self.jd_docs = docs

    def _tokenize_for_bm25(self, text: str) -> List[str]:
        """Simple tokenizer that doesn't require NLTK"""
        # Convert to lowercase and extract alphanumeric tokens
        tokens = re.findall(r'\b\w+\b', text.lower())
    
        # Filter out stopwords and very short tokens
        filtered_tokens = [
            token for token in tokens 
            if len(token) > 2 and token not in self.stop_words
        ]
        return filtered_tokens

    def _clear_resume_index(self, resume_id: str):
        """Clear existing resume data from indexes"""
        try:
            # Get all documents for this resume
            results = self.resume_collection.get(
                where={"resume_id": resume_id}
            )
            if results["ids"]:
                self.resume_collection.delete(ids=results["ids"])
        except Exception as e:
            print(f"Note: Could not clear existing resume data: {e}")

    def _clear_jd_index(self, jd_id: str):
        """Clear existing JD data from indexes"""
        try:
            results = self.jd_collection.get(
                where={"jd_id": jd_id}
            )
            if results["ids"]:
                self.jd_collection.delete(ids=results["ids"])
        except Exception as e:
            print(f"Note: Could not clear existing JD data: {e}")

    def _save_bm25_indexes(self):
        """Save BM25 indexes to disk"""
        if self.resume_bm25:
            with open(os.path.join(self.persist_directory, "resume_bm25.pkl"), "wb") as f:
                pickle.dump((self.resume_bm25, self.resume_docs), f)
        
        if self.jd_bm25:
            with open(os.path.join(self.persist_directory, "jd_bm25.pkl"), "wb") as f:
                pickle.dump((self.jd_bm25, self.jd_docs), f)

    def load_indexes(self):
        """Load existing BM25 indexes from disk"""
        resume_path = os.path.join(self.persist_directory, "resume_bm25.pkl")
        jd_path = os.path.join(self.persist_directory, "jd_bm25.pkl")
        
        if os.path.exists(resume_path):
            with open(resume_path, "rb") as f:
                self.resume_bm25, self.resume_docs = pickle.load(f)
            print("✅ Loaded resume BM25 index")
        
        if os.path.exists(jd_path):
            with open(jd_path, "rb") as f:
                self.jd_bm25, self.jd_docs = pickle.load(f)
            print("✅ Loaded JD BM25 index")

    def test_search(self, query: str, search_type: str = "both") -> Dict[str, List]:
        """Test search functionality"""
        print(f"\n🔍 Testing search: '{query}'")
        results = {}
        
        if search_type in ["vector", "both"]:
            # Vector search in resume
            vector_results = self.resume_collection.query(
                query_texts=[query],
                n_results=5
            )
            results["vector"] = [
                {
                    "id": vector_results["ids"][0][i],
                    "text": vector_results["documents"][0][i],
                    "distance": vector_results["distances"][0][i],
                    "metadata": vector_results["metadatas"][0][i]
                }
                for i in range(len(vector_results["ids"][0]))
            ]
        
        if search_type in ["bm25", "both"] and self.resume_bm25:
            # BM25 search in resume
            query_tokens = self._tokenize_for_bm25(query)
            bm25_scores = self.resume_bm25.get_scores(query_tokens)
            
            # Get top 5 results
            top_indices = sorted(range(len(bm25_scores)), 
                               key=lambda i: bm25_scores[i], reverse=True)[:5]
            
            results["bm25"] = [
                {
                    "id": self.resume_docs[i].id,
                    "text": self.resume_docs[i].text,
                    "score": bm25_scores[i],
                    "metadata": self.resume_docs[i].metadata
                }
                for i in top_indices if bm25_scores[i] > 0
            ]
        
        return results

    def get_index_stats(self) -> Dict[str, Any]:
        """Get statistics about indexed documents"""
        stats = {}
        
        # ChromaDB stats
        try:
            resume_count = self.resume_collection.count()
            jd_count = self.jd_collection.count()
            stats["vector"] = {
                "resume_lines": resume_count,
                "jd_bullets": jd_count
            }
        except Exception as e:
            stats["vector"] = {"error": str(e)}
        
        # BM25 stats
        stats["bm25"] = {
            "resume_docs": len(self.resume_docs) if self.resume_docs else 0,
            "jd_docs": len(self.jd_docs) if self.jd_docs else 0
        }
        
        return stats


# # Step-by-step implementation guide
# def phase2_implementation_guide():
#     """Step-by-step guide for implementing Phase 2"""
    
#     print("=== PHASE 2 IMPLEMENTATION GUIDE ===\n")
    
#     print("STEP 1: Install dependencies")
#     print("pip install chromadb sentence-transformers rank-bm25 nltk")
#     print()
    
#     print("STEP 2: Initialize the index manager")
#     print("index_manager = ATSIndexManager()")
#     print("# This will download the embedding model (first time only)")
#     print()
    
#     print("STEP 3: Index your resume")
#     print("# Use processed_lines from Phase 1")
#     print("resume_count = index_manager.index_resume(processed_lines)")
#     print()
    
#     print("STEP 4: Index job description")
#     print("jd_count = index_manager.index_job_description(jd_processed_lines)")
#     print()
    
#     print("STEP 5: Test search functionality")
#     print("results = index_manager.test_search('Python machine learning')")
#     print()
    
#     print("STEP 6: Check index statistics")
#     print("stats = index_manager.get_index_stats()")
#     print("print(stats)")


# if __name__ == "__main__":
#     # Example usage
#     phase2_implementation_guide()
    
#     # Quick test if you have processed lines from Phase 1
#     """
#     # Uncomment to test with your data:
    
#     from phase1_processor import UniversalTextProcessor
    
#     # Initialize
#     processor = UniversalTextProcessor()
#     index_manager = ATSIndexManager()
    
#     # Process sample resume
#     sample_resume = '''
#     EXPERIENCE
#     • Built scalable Python applications processing 1M+ requests/day
#     • Improved machine learning model accuracy by 15% using feature engineering
#     • Led team of 4 engineers on microservices migration project
#     '''
    
#     processed_lines = processor.process_resume(sample_resume)
    
#     # Index the resume
#     count = index_manager.index_resume(processed_lines)
#     print(f"Indexed {count} lines")
    
#     # Test search
#     results = index_manager.test_search("Python machine learning")
#     print("Search results:", results)
    
#     # Check stats
#     stats = index_manager.get_index_stats()
#     print("Index stats:", stats)
#     """
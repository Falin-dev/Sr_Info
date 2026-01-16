import os
import chromadb
from chromadb.utils import embedding_functions
from sentence_transformers import SentenceTransformer
import google.generativeai as genai
from pypdf import PdfReader

class ApriliaRAG:
    def __init__(self, gemini_api_key):
        # 1. Configure Gemini LLM
        genai.configure(api_key=gemini_api_key)
        
        # 2. Robust Model Selection
        # Instead of hardcoding, we find an available model that supports generation
        try:
            # We look for a model that supports 'generateContent'
            available_models = [
                m.name for m in genai.list_models() 
                if 'generateContent' in m.supported_generation_methods
            ]
            
            # Priority: 1.5-flash -> 1.5-pro -> gemini-pro -> any available
            if 'models/gemini-1.5-flash' in available_models:
                model_name = 'gemini-1.5-flash'
            elif 'models/gemini-1.5-pro' in available_models:
                model_name = 'gemini-1.5-pro'
            elif 'models/gemini-pro' in available_models:
                model_name = 'gemini-pro'
            else:
                model_name = available_models[0].replace('models/', '')
            
            print(f"✅ Using model: {model_name}")
            self.llm = genai.GenerativeModel(model_name)
            
        except Exception as e:
            print(f"⚠️ Error listing models, defaulting to flash: {e}")
            self.llm = genai.GenerativeModel('gemini-1.5-flash')
        
        # 3. Initialize the Embedding Function
        self.embedding_fn = embedding_functions.SentenceTransformerEmbeddingFunction(
            model_name="all-MiniLM-L6-v2"
        )
        
        # 4. Setup Persistent Vector Database (ChromaDB)
        self.client = chromadb.PersistentClient(path="./chroma_db")
        self.collection = self.client.get_or_create_collection(
            name="aprilia_manual",
            embedding_function=self.embedding_fn
        )
    
    def load_pdf(self, pdf_path):
        """
        Reads a PDF, splits it into chunks, and stores them in the vector DB.
        """
        reader = PdfReader(pdf_path)
        chunks = []
        metadatas = []
        ids = []
        
        for page_num, page in enumerate(reader.pages):
            text = page.extract_text()
            
            # Chunking strategy: 500 characters with a 100-character overlap
            # Overlap ensures sentences cut off between chunks are still understandable
            chunk_size = 500
            overlap = 100
            
            for i in range(0, len(text), chunk_size - overlap):
                chunk = text[i:i + chunk_size]
                
                # Filter out empty or very small noise chunks
                if len(chunk.strip()) > 50:
                    chunks.append(chunk)
                    metadatas.append({"page": page_num + 1})
                    ids.append(f"p{page_num}_c{i}")
        
        # Add the processed text to our vector collection
        if chunks:
            self.collection.add(
                documents=chunks,
                metadatas=metadatas,
                ids=ids
            )
        
        return len(chunks)

    def query(self, question):
        """
        Retrieves relevant manual snippets and generates an answer using Gemini.
        """
        # Search for the top 3 most relevant segments in the manual
        results = self.collection.query(
            query_texts=[question],
            n_results=3
        )
        
        # Check if any relevant text was found
        if not results['documents'] or not results['documents'][0]:
            return {
                "answer": "I'm sorry, I couldn't find any information regarding that in the Aprilia manual.",
                "sources": "No relevant pages found."
            }
        
        # Combine the retrieved chunks into a single context string
        context = "\n\n".join(results['documents'][0])
        pages = [str(m['page']) for m in results['metadatas'][0]]
        
        # Construct the professional prompt for the LLM
        prompt = f"""You are a professional Aprilia SR125 Service Assistant. 
        Your goal is to provide accurate technical advice based ONLY on the manual context provided.

        MANUAL CONTEXT:
        {context}

        USER QUESTION: {question}

        INSTRUCTIONS:
        1. Use the provided context to answer the question.
        2. If the context does not contain the answer, state that the information is unavailable.
        3. Be concise, technical, and helpful.

        ANSWER:"""
        
        # Generate the response from Gemini
        response = self.llm.generate_content(prompt)
        
        return {
            "answer": response.text,
            "sources": f"Manual Pages: {', '.join(set(pages))}"
        }
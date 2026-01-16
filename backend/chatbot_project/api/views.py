import os
from rest_framework.decorators import api_view
from rest_framework.response import Response
from django.core.files.storage import default_storage # <--- THE MISSING LINE
from .rag_engine import ApriliaRAG
from dotenv import load_dotenv

load_dotenv()

# Initialize RAG with API Key
GEMINI_KEY = os.getenv("GEMINI_API_KEY")
rag = ApriliaRAG(GEMINI_KEY)

@api_view(['POST'])
def upload_manual(request):
    if 'file' not in request.FILES:
        return Response({"error": "No file"}, status=400)
    
    file = request.FILES['file']
    # This stores the PDF in a folder named 'manuals'
    file_path = default_storage.save(f"manuals/{file.name}", file)
    full_path = default_storage.path(file_path)
    
    num_chunks = rag.load_pdf(full_path)
    return Response({"message": f"Successfully processed {num_chunks} chunks!"})

@api_view(['POST'])
def ask_question(request):
    question = request.data.get('question')
    if not question:
        return Response({"error": "No question provided"}, status=400)
    
    answer = rag.query(question)
    return Response(answer)

@api_view(['GET'])
def health_check(request):
    return Response({"status": "ready"})
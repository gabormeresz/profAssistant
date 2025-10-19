# File Upload Feature Implementation

## Overview
Added file upload functionality to allow users to upload reference materials (PDF, DOCX, TXT, MD) that will be used to inform the course outline generation.

## Implementation Approach
We chose **simple text extraction** over RAG for now because:
- Simpler implementation for initial version
- Works well for moderately-sized documents
- Faster response times
- Can upgrade to RAG later if needed for larger documents

## Changes Made

### Frontend Changes

#### 1. **InputSection.tsx**
- Added file upload UI with drag-and-drop zone
- File validation (type and size checking - max 10MB)
- Display uploaded files with ability to remove them
- Supported file types: PDF, DOCX, TXT, MD

#### 2. **App.tsx**
- Added `uploadedFiles` state management
- Passes files to the WebSocket hook
- Clears files on new conversation

#### 3. **useWebSocket.ts**
- Modified to handle file uploads via HTTP POST before WebSocket connection
- Uploads files to `/upload` endpoint
- Receives extracted text content
- Sends file contents along with other data via WebSocket

### Backend Changes

#### 1. **main.py**
- Added CORS middleware for frontend communication
- New `/upload` endpoint to handle file uploads
- Processes multiple files and extracts text
- Updated WebSocket endpoint to accept `file_contents` parameter

#### 2. **agent/file_processor.py** (NEW)
- FileProcessor class with text extraction methods:
  - `extract_text_from_pdf()` - Extracts text from PDF files
  - `extract_text_from_docx()` - Extracts text from Word documents
  - `extract_text_from_txt()` - Handles plain text and markdown files
  - `process_file()` - Routes to appropriate extractor
  - `process_multiple_files()` - Batch processing with error handling

#### 3. **agent/graph.py**
- Updated `State` class to include `file_contents` field
- Modified `node_outline_generator()` to incorporate file contents into prompt
- Updated `run_graph()` function to accept and pass file contents

#### 4. **pyproject.toml**
- Added dependencies:
  - `python-multipart` - For file upload handling
  - `pypdf` - For PDF text extraction
  - `python-docx` - For DOCX text extraction

## How It Works

1. **User uploads files** in the frontend UI
2. **File validation** checks file type and size
3. **On submit**, files are sent to `/upload` endpoint via HTTP POST
4. **Backend extracts text** from each file using appropriate parser
5. **Extracted text** is sent back to frontend
6. **WebSocket connection** is established with file contents included
7. **LLM receives** both the user's prompt and file contents
8. **Course outline** is generated using the reference materials

## File Flow

```
Frontend Upload → HTTP POST /upload → FileProcessor.process_file()
                                    ↓
                            Extracted Text Content
                                    ↓
                    WebSocket with file_contents
                                    ↓
                            LangGraph State
                                    ↓
                        Prompt with Reference Materials
                                    ↓
                            LLM Generation
```

## Future Enhancements

If needed, we can upgrade to RAG:
- Add vector database (ChromaDB, Pinecone, etc.)
- Implement document chunking
- Add embeddings generation
- Implement semantic search
- Handle very large documents (100MB+)
- Support multiple document retrieval

## Testing

To test the feature:
1. Start backend: `cd backend && uvicorn main:app --reload`
2. Start frontend: `cd frontend && npm run dev`
3. Upload a PDF, DOCX, TXT, or MD file
4. Add topic and comments
5. Generate course outline
6. Verify the LLM uses content from uploaded files

## File Size Limits
- Maximum file size: 10MB per file
- Supported formats: .pdf, .docx, .doc, .txt, .md, .markdown

#!/usr/bin/env python3
"""
Test specific Docling imports that are failing
"""

def test_docling_imports():
    """Test the exact imports used in the application."""
    
    print("Testing Docling imports...")
    
    try:
        from docling.document_converter import DocumentConverter
        print("[OK] DocumentConverter imported")
    except ImportError as e:
        print(f"[ERROR] DocumentConverter: {e}")
    
    try:
        from docling.datamodel.base_models import InputFormat
        print("[OK] InputFormat imported")
    except ImportError as e:
        print(f"[ERROR] InputFormat: {e}")
    
    try:
        from docling.datamodel.pipeline_options import PdfPipelineOptions
        print("[OK] PdfPipelineOptions imported")
    except ImportError as e:
        print(f"[ERROR] PdfPipelineOptions: {e}")
    
    # Test Document import paths
    print("\nTesting Document import paths:")
    
    try:
        from docling.datamodel.document import Document as DoclingDocument
        print("[OK] Document from docling.datamodel.document")
    except ImportError as e:
        print(f"[ERROR] docling.datamodel.document: {e}")
        
        try:
            from docling.datamodel.base_models import Document as DoclingDocument
            print("[OK] Document from docling.datamodel.base_models")
        except ImportError as e:
            print(f"[ERROR] docling.datamodel.base_models: {e}")
            
            try:
                from docling_core.types.doc import Document as DoclingDocument
                print("[OK] Document from docling_core.types.doc")
            except ImportError as e:
                print(f"[ERROR] docling_core.types.doc: {e}")
                print("[INFO] All Document imports failed")

if __name__ == "__main__":
    test_docling_imports()

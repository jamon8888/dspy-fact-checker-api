#!/usr/bin/env python3
"""
Check Docling installation and available modules
"""

def check_docling():
    """Check what's available in Docling."""
    
    try:
        import docling
        print("[OK] Docling imported successfully")
        print(f"Docling path: {docling.__path__}")

        # Check for common modules
        modules_to_check = [
            'docling.document_converter',
            'docling.datamodel.base_models',
            'docling.datamodel.pipeline_options',
            'docling.datamodel.document',
            'docling_core.types.doc'
        ]

        for module_name in modules_to_check:
            try:
                __import__(module_name)
                print(f"[OK] {module_name} - Available")
            except ImportError as e:
                print(f"[ERROR] {module_name} - Not available: {e}")

        # Try to find what's actually available
        print("\nExploring docling structure:")
        import pkgutil
        for importer, modname, ispkg in pkgutil.iter_modules(docling.__path__, docling.__name__ + '.'):
            print(f"  [MODULE] {modname}")

    except ImportError as e:
        print(f"[ERROR] Docling not available: {e}")

if __name__ == "__main__":
    check_docling()

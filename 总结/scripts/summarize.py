#!/usr/bin/env python3
"""
File Summarizer using OpenAI API
Generates intelligent summaries of any file type.
"""

import os
import sys
import argparse
import json
from pathlib import Path

def check_openai_available():
    """Check if OpenAI package is available and API key is set."""
    try:
        import openai
        return True
    except ImportError:
        return False

def install_dependencies():
    """Install required dependencies."""
    print("Installing required packages...")
    os.system(f"{sys.executable} -m pip install openai PyPDF2 python-docx --break-system-packages -q")
    print("Dependencies installed successfully.")

def get_api_key():
    """Get OpenAI API key from environment."""
    api_key = os.environ.get('OPENAI_API_KEY')
    if not api_key:
        print("ERROR: OPENAI_API_KEY environment variable not set.", file=sys.stderr)
        print("\nPlease set your API key:", file=sys.stderr)
        print("  export OPENAI_API_KEY='sk-...'", file=sys.stderr)
        print("\nOr add to your shell profile (~/.bashrc or ~/.zshrc) for persistence.", file=sys.stderr)
        sys.exit(1)
    return api_key

def read_text_file(file_path):
    """Read a text file with encoding detection."""
    encodings = ['utf-8', 'latin-1', 'cp1252', 'iso-8859-1']
    
    for encoding in encodings:
        try:
            with open(file_path, 'r', encoding=encoding) as f:
                return f.read()
        except UnicodeDecodeError:
            continue
        except Exception as e:
            print(f"Error reading file: {e}", file=sys.stderr)
            return None
    
    print(f"Unable to read file with common encodings", file=sys.stderr)
    return None

def read_pdf(file_path):
    """Extract text from PDF file."""
    try:
        import PyPDF2
        text_parts = []
        with open(file_path, 'rb') as f:
            pdf_reader = PyPDF2.PdfReader(f)
            for page in pdf_reader.pages:
                text_parts.append(page.extract_text())
        return '\n\n'.join(text_parts)
    except ImportError:
        print("PyPDF2 not installed. Installing...", file=sys.stderr)
        install_dependencies()
        return read_pdf(file_path)
    except Exception as e:
        print(f"Error reading PDF: {e}", file=sys.stderr)
        return None

def read_docx(file_path):
    """Extract text from Word document."""
    try:
        from docx import Document
        doc = Document(file_path)
        text_parts = [paragraph.text for paragraph in doc.paragraphs]
        return '\n\n'.join(text_parts)
    except ImportError:
        print("python-docx not installed. Installing...", file=sys.stderr)
        install_dependencies()
        return read_docx(file_path)
    except Exception as e:
        print(f"Error reading DOCX: {e}", file=sys.stderr)
        return None

def read_file(file_path):
    """Read file content based on file type."""
    file_path = Path(file_path)
    
    if not file_path.exists():
        print(f"ERROR: File not found: {file_path}", file=sys.stderr)
        return None
    
    if not file_path.is_file():
        print(f"ERROR: Path is not a file: {file_path}", file=sys.stderr)
        return None
    
    suffix = file_path.suffix.lower()
    
    # PDF files
    if suffix == '.pdf':
        return read_pdf(file_path)
    
    # Word documents
    elif suffix in ['.docx', '.doc']:
        if suffix == '.doc':
            print("WARNING: .doc format may not be fully supported. Consider converting to .docx", file=sys.stderr)
        return read_docx(file_path)
    
    # Text-based files (most common)
    else:
        return read_text_file(file_path)

def get_system_prompt(detail_level):
    """Get system prompt based on detail level."""
    prompts = {
        'brief': """You are a professional summarizer. Provide a concise summary in 2-3 sentences 
highlighting only the most critical points. Be direct and factual.""",
        
        'medium': """You are a professional summarizer. Provide a clear summary in one well-structured 
paragraph covering the main ideas, key takeaways, and most important information. 
Be comprehensive but concise.""",
        
        'detailed': """You are a professional summarizer. Provide a comprehensive summary with 
multiple paragraphs covering:
1. Main themes and purpose
2. Key points and arguments
3. Important details and structure
4. Conclusions or outcomes
Be thorough while maintaining clarity."""
    }
    
    return prompts.get(detail_level, prompts['medium'])

def summarize_content(content, detail_level, model, api_key):
    """Send content to OpenAI for summarization."""
    try:
        from openai import OpenAI
        client = OpenAI(api_key=api_key)
        
        # Truncate very long content to avoid token limits
        max_chars = 100000  # Roughly 25k tokens
        if len(content) > max_chars:
            print(f"NOTE: File is very large ({len(content)} chars). Truncating to {max_chars} chars.", file=sys.stderr)
            content = content[:max_chars] + "\n\n[Content truncated...]"
        
        system_prompt = get_system_prompt(detail_level)
        
        response = client.chat.completions.create(
            model=model,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": f"Please summarize the following content:\n\n{content}"}
            ],
            temperature=0.3,  # Lower temperature for more factual summaries
        )
        
        return response.choices[0].message.content
        
    except ImportError:
        print("OpenAI package not installed. Installing...", file=sys.stderr)
        install_dependencies()
        return summarize_content(content, detail_level, model, api_key)
    except Exception as e:
        print(f"ERROR: Failed to generate summary: {e}", file=sys.stderr)
        print("\nPlease check:", file=sys.stderr)
        print("  1. Your API key is valid", file=sys.stderr)
        print("  2. You have available API credits", file=sys.stderr)
        print("  3. The OpenAI API service is accessible", file=sys.stderr)
        return None

def main():
    parser = argparse.ArgumentParser(
        description='Summarize any file using OpenAI API',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  %(prog)s document.pdf --detail medium
  %(prog)s code.py --detail brief
  %(prog)s report.docx --detail detailed --model gpt-4o

Detail Levels:
  brief    - 2-3 sentences with key points only
  medium   - One paragraph covering main ideas (default)
  detailed - Multiple paragraphs with comprehensive coverage
        """
    )
    
    parser.add_argument('file_path', nargs='?', help='Path to file to summarize')
    parser.add_argument('--detail', choices=['brief', 'medium', 'detailed'], 
                        default='medium', help='Level of detail (default: medium)')
    parser.add_argument('--model', default='gpt-4o-mini',
                        help='OpenAI model to use (default: gpt-4o-mini)')
    parser.add_argument('--check-config', action='store_true',
                        help='Check if API key is configured')
    
    args = parser.parse_args()
    
    # Check configuration only
    if args.check_config:
        api_key = os.environ.get('OPENAI_API_KEY')
        if api_key:
            print("✓ OPENAI_API_KEY is set")
            if check_openai_available():
                print("✓ OpenAI package is available")
            else:
                print("✗ OpenAI package not installed (will auto-install when needed)")
            return 0
        else:
            print("✗ OPENAI_API_KEY is not set")
            print("\nPlease set your API key:")
            print("  export OPENAI_API_KEY='sk-...'")
            return 1
    
    # Normal summarization flow
    if not args.file_path:
        parser.print_help()
        sys.exit(1)
    
    # Get API key
    api_key = get_api_key()
    
    # Read file
    print(f"Reading file: {args.file_path}", file=sys.stderr)
    content = read_file(args.file_path)
    
    if content is None:
        sys.exit(1)
    
    if not content.strip():
        print("ERROR: File appears to be empty or unreadable", file=sys.stderr)
        sys.exit(1)
    
    print(f"File size: {len(content)} characters", file=sys.stderr)
    print(f"Generating {args.detail} summary using {args.model}...", file=sys.stderr)
    
    # Generate summary
    summary = summarize_content(content, args.detail, args.model, api_key)
    
    if summary is None:
        sys.exit(1)
    
    # Output summary
    print("\n" + "="*60)
    print(f"SUMMARY ({args.detail.upper()})")
    print("="*60 + "\n")
    print(summary)
    print("\n" + "="*60)
    
    return 0

if __name__ == '__main__':
    sys.exit(main())

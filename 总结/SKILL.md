---
name: file-summarizer
description: Use this skill whenever the user wants to summarize, get a summary of, create an overview of, or understand the main points of any local file. Trigger on phrases like "summarize this file", "what's in this document", "give me a summary", "tl;dr of this file", "overview of", or any request to condense or explain file contents. Works with all file types including text files, code, documents (PDF, DOCX), spreadsheets, and more. Always use this skill when the user mentions summarizing files, even if they don't explicitly ask for AI-powered summarization.
---

# File Summarizer

This skill uses OpenAI's API to generate intelligent summaries of local files. It handles all file types and allows users to choose the level of detail they need.

## Quick Start

When the user asks to summarize a file:

1. **Identify the file** - Get the file path from the user or from context
2. **Ask for detail level** (if not specified) - Use the `ask_user_input_v0` tool to let them choose:
   - Brief (a few sentences)
   - Medium (one paragraph)
   - Detailed (multiple paragraphs with key points)
3. **Run the summarizer** - Use `scripts/summarize.py`
4. **Present results** - Show the summary to the user

## Prerequisites

The user must have:
- OpenAI API key set as environment variable `OPENAI_API_KEY`
- Python with `openai` package installed

If the API key is not set, guide the user to:
```bash
export OPENAI_API_KEY="sk-..."
```

Or for persistence, add to `~/.bashrc` or `~/.zshrc`.

## Usage

### Basic Usage

```bash
python scripts/summarize.py <file_path> --detail <level>
```

**Parameters:**
- `<file_path>` - Path to the file to summarize (required)
- `--detail` - Level of detail: `brief`, `medium`, or `detailed` (default: medium)
- `--model` - OpenAI model to use (default: gpt-4o-mini)

### Examples

```bash
# Medium detail summary (default)
python scripts/summarize.py /path/to/document.pdf

# Brief summary
python scripts/summarize.py /path/to/code.py --detail brief

# Detailed summary
python scripts/summarize.py /path/to/report.docx --detail detailed

# Use a specific model
python scripts/summarize.py /path/to/file.txt --detail medium --model gpt-4o
```

## Workflow

### Step 1: Validate Prerequisites

Check if the OpenAI API key is set:

```bash
python scripts/summarize.py --check-config
```

If not configured, guide the user to set it up.

### Step 2: Get User Preferences

If the user hasn't specified a detail level, ask them using `ask_user_input_v0`:

```python
{
  "questions": [
    {
      "question": "How detailed should the summary be?",
      "type": "single_select",
      "options": [
        "Brief - just the key points in a few sentences",
        "Medium - a paragraph covering main ideas",
        "Detailed - comprehensive summary with structure"
      ]
    }
  ]
}
```

Map their choice to: `brief`, `medium`, or `detailed`.

### Step 3: Read the File

The script handles different file types automatically:
- **Text files** (.txt, .md, .json, .xml, etc.) - Read directly
- **Code files** (.py, .js, .java, etc.) - Read with syntax awareness
- **PDF files** - Extract text using PyPDF2
- **Word documents** (.docx) - Extract using python-docx
- **Other formats** - Attempt text extraction or read as plain text

### Step 4: Generate Summary

The script sends the file content to OpenAI with a system prompt tailored to the detail level:

- **Brief**: "Provide a concise summary in 2-3 sentences highlighting only the most critical points."
- **Medium**: "Provide a clear summary in one paragraph covering the main ideas and key takeaways."
- **Detailed**: "Provide a comprehensive summary with multiple paragraphs, including main themes, key points, structure, and important details."

### Step 5: Present Results

Display the summary to the user. For very long summaries, consider saving to a file and using `present_files`.

## Error Handling

Common issues and solutions:

1. **API Key Missing**: Guide user to set `OPENAI_API_KEY`
2. **File Not Found**: Verify the file path and check permissions
3. **API Error**: Show the error message and suggest checking API key validity
4. **Unsupported File**: Try to read as text, or inform user if binary/encrypted

## File Type Support

The script attempts to handle:
- Plain text: .txt, .md, .csv, .log
- Code: .py, .js, .java, .cpp, .go, .rs, etc.
- Documents: .pdf, .docx
- Data: .json, .xml, .yaml
- Any other text-based format

For binary files that can't be read as text, the script will report an error with suggestions.

## Tips for Best Results

- For large files (>10MB), the script may truncate content to fit token limits
- PDF files work best when they contain actual text (not scanned images)
- Code files benefit from "medium" or "detailed" summaries to capture logic
- For multiple files, run the script separately for each and then ask Claude to combine insights

## Example Interaction

```
User: Can you summarize this report for me? /home/user/quarterly_report.pdf

Claude: I'll summarize that report for you. 
[Uses ask_user_input_v0 to get detail level]
[Runs: python scripts/summarize.py /home/user/quarterly_report.pdf --detail medium]
[Displays the summary]

Here's a summary of your quarterly report:

[Summary content from OpenAI]
```

## Advanced Options

The script supports additional flags (modify as needed):
- `--max-tokens` - Limit summary length (default: auto-calculated)
- `--temperature` - Control creativity (default: 0.3 for factual summaries)

## Troubleshooting

If summarization fails:
1. Check file path exists and is readable
2. Verify `OPENAI_API_KEY` is set correctly
3. Test with a small text file first
4. Check OpenAI API status and rate limits
5. Try a different model (e.g., gpt-3.5-turbo for faster/cheaper summaries)

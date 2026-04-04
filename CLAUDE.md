# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

PDF to HWP Converter — a Python agent that converts PDF files to HWP (한글) format by rendering PDF pages as high-resolution images and embedding them into HWP/HWPX documents.

## Setup & Commands

```bash
# Install dependencies
pip install -r requirements.txt

# Install as editable package (enables `pdf-to-hwp` CLI command)
pip install -e .
```

### CLI Usage

```bash
# Single conversion
python main.py convert document.pdf
python main.py convert document.pdf -o output.hwp -d 150 --margin 5

# Batch conversion
python main.py batch *.pdf -o ./converted/

# Merge multiple PDFs into one HWP (interactive reordering by default)
python main.py merge doc1.pdf doc2.pdf -o merged.hwp
python main.py merge *.pdf -o output.hwp --no-reorder

# PDF info
python main.py info document.pdf
```

No linting or test commands are configured in this project.

## Architecture

Three-stage pipeline:

1. **PDF Extraction** (`pdf_to_hwp/converter.py` — `PDFConverter`) — Renders PDF pages to PIL Images using PyMuPDF at configurable DPI.
2. **Document Generation** (`pdf_to_hwp/hwp_generator.py` — `HWPGenerator`) — Embeds images into HWP/HWPX. Uses `pyhwpx` for native `.hwp` on Windows with Hangul Office installed; falls back to a hand-built HWPX ZIP structure (XML + binary images) on other platforms.
3. **Orchestration** (`pdf_to_hwp/agent.py` — `PDFToHWPAgent`) — Coordinates the pipeline, manages temp directories, handles batch/merge workflows, and exposes a context manager API.

The CLI in `main.py` also implements an interactive reordering system (swap/move/reverse) for the merge command.

### Public API

```python
from pdf_to_hwp import PDFToHWPAgent, convert_pdf_to_hwp, merge_pdfs_to_hwp

with PDFToHWPAgent(dpi=150) as agent:
    agent.convert("input.pdf", "output.hwp")
    agent.convert_batch(["a.pdf", "b.pdf"], output_dir="./out/")
    agent.merge_pdfs(["a.pdf", "b.pdf"], "merged.hwp")
```

## Key Platform Note

`pyhwpx` (native HWP output) only works on **Windows with Hangul Office installed**. On other platforms the agent automatically falls back to HWPX format.

# KAVACH frontend

This directory contains the React/Vite chat interface for KAVACH, the
privacy-aware LLM router.

## Development

From this directory:

```powershell
npm install
npm run dev -- --host 127.0.0.1
```

Open `http://127.0.0.1:5173`. The backend must be running at
`http://127.0.0.1:8000`.

For the easiest Windows setup, run [`start-kavach.ps1`](../start-kavach.ps1)
from the repository root. It starts both services and opens the browser.

## Scripts

```powershell
npm run dev      # Start the development server
npm run build    # Create a production build
npm run lint     # Run ESLint
npm run preview  # Preview the production build
```

The interface supports named chats, text prompts, document uploads, PNG/JPG
images, webcam photos, OCR-backed file analysis, and Markdown-rendered
assistant responses. It displays the model, decision, processing time, and
risk summary for each response.

Markdown support includes headings, lists, tables, links, inline code, and
fenced code blocks through the `react-markdown` package.

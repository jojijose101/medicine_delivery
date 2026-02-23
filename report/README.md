MediDelivery Report — Export & Conversion

This folder contains `MediDelivery_Report.html` — an interactive HTML report with embedded Mermaid diagrams.

Open the HTML in a browser to view diagrams (Mermaid is loaded via CDN).

Export to PDF using the browser:
- File → Print → Save as PDF (or press Ctrl+P on Windows).

Convert to DOCX using pandoc (optional):
1. Install pandoc (https://pandoc.org/installing.html).
2. Run:

```bash
pandoc MediDelivery_Report.html -o MediDelivery_Report.docx --extract-media=.
```

Notes:
- The HTML relies on the Mermaid CDN; an internet connection is required to render diagrams.
- If you need a self-contained PDF generated server-side, I can attempt to generate one (requires wkhtmltopdf or headless Chrome on your machine).
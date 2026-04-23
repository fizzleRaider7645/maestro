# /property-intake

Classify and ingest rental property documents into Maestro. Reads PDFs, spreadsheets, and text files; classifies each by type (lease, invoice, mortgage statement, tax doc, maintenance record); extracts key financial figures; and updates persistent KPI state for the property.

## Usage

```
/property-intake <path-to-file-or-directory> [--project <property-id>]
```

## Examples

```
/property-intake ~/Documents/properties/123-main-st/
/property-intake ~/Downloads/new-lease.pdf --project 123-main-st
/property-intake ~/Documents/properties/ --project my-portfolio
```

## Instructions

1. **Extract the path and project ID** from the user's message.
   - If no project ID is provided, ask: "What property ID should I use? (e.g., '123-main-st' or 'my-portfolio')"
   - Use a URL-safe, hyphenated ID (no spaces).

2. **Verify the path exists:**
   ```bash
   ls -la "<path>"
   ```
   If it doesn't exist, tell the user and stop.

3. **Invoke the property_manager agent:**
   ```bash
   cd /Users/douglasuretsky/Projects/maestro/runtime && maestro invoke property_manager \
     --message "Ingest and classify all documents at: <path>

   Property ID: <project-id>

   Instructions:
   1. Use list_dir to enumerate the directory (if a directory was provided)
   2. Read each file using read_pdf (for .pdf), read_spreadsheet (for .xlsx/.csv), or read_file (for .txt/.md)
   3. Classify each document by type and confidence level
   4. Extract key financial figures from each document
   5. Calculate any KPIs you can derive from the available data
   6. Call update_property_kpis with mode='update' to persist the extracted figures
   7. Produce a classification report with Document Inventory, KPI Summary (if calculable), and Open Questions" \
     --project <project-id>
   ```

4. **Display the classification report** returned by the agent.

5. **Show where artifacts were saved:**
   ```
   Artifacts saved to: ~/.maestro/projects/<project-id>/artifacts/
   ```

6. **Suggest next steps:**
   - Run `/property-analyze --project <project-id>` to generate a full financial analysis
   - Run `/property-intake` again as new documents arrive — KPI state is merged, not overwritten

## Notes

- Supported formats: PDF, XLSX, XLS, CSV, TXT, MD
- Scanned PDFs (image-only) will produce empty or low-quality text — the agent will flag these
- Run per property for best results; pointing at a large multi-property archive may hit turn limits
- KPI data persists in `~/.maestro/projects/<project-id>/context.json` between sessions

# /property-analyze

Run a financial analysis on a rental property or underwrite a new acquisition deal. Two modes:

- **portfolio** (default) — full P&L, KPI dashboard, and rent roll for an existing property using stored data
- **deal** — new acquisition underwriting: cap rate, cash-on-cash return, IRR, DSCR, 3-scenario analysis, due diligence checklist, risk register

## Usage

```
/property-analyze [--project <property-id>] [--mode portfolio|deal] [--input <file>]
```

## Examples

```
# Portfolio analysis for an existing property
/property-analyze --project 123-main-st

# Deal analysis from a file
/property-analyze --mode deal --input ~/Downloads/deal-summary.md --project new-acquisition

# Deal analysis from inline description
/property-analyze --mode deal --project eastside-duplex
```

## Instructions

1. **Determine the mode and project ID** from the user's message.
   - Default mode is `portfolio` if not specified.
   - If no project ID is given, ask for one.

2. **Portfolio mode** — invoke property_manager:
   ```bash
   cd /Users/douglasuretsky/Projects/maestro/runtime && maestro invoke property_manager \
     --message "Generate a full financial analysis for property '<project-id>'.

   Instructions:
   1. Call update_property_kpis with mode='read' and property_id='<project-id>' to retrieve stored KPI data
   2. Call read_artifact to check for any previously stored documents or reports
   3. Produce a complete report including: KPI Summary, P&L Statement, Rent Roll, and any Open Questions
   4. Flag any metrics that are outside normal ranges (expense ratio >45%, occupancy <90%, DSCR <1.25)" \
     --project <project-id>
   ```

3. **Deal mode:**

   a. If `--input <file>` is provided, verify it exists:
   ```bash
   ls -la "<file>"
   ```

   b. If no input file and no inline deal details, ask the user:
   > "Please provide the deal details. At minimum I need: asking price, current or expected monthly rent, estimated annual operating expenses, and financing terms (down payment %, interest rate, loan term) — or let me know if it's an all-cash purchase."

   c. Write inline deal details to a temp file if provided inline:
   ```bash
   cat > /tmp/deal-details.md << 'EOF'
   [deal details here]
   EOF
   ```

   d. Invoke deal_analyst:
   ```bash
   cd /Users/douglasuretsky/Projects/maestro/runtime && maestro invoke deal_analyst \
     --message "Analyze this real estate acquisition deal.

   Deal details are in: <file-path>

   Instructions:
   1. Read the deal details file
   2. Confirm all required inputs are present (purchase price, rent, expenses, financing)
   3. Produce a full underwriting analysis: Deal Summary Card, three-scenario model (base/upside/downside), IRR projection, due diligence checklist, and risk register
   4. Flag prominently if DSCR < 1.25 in any scenario" \
     --project <project-id>
   ```

4. **Display the analysis output.**

5. **Show artifact location:**
   ```
   Analysis saved to: ~/.maestro/projects/<project-id>/artifacts/
   ```

## Notes

- For portfolio analysis, run `/property-intake` first to load documents and populate KPI state
- Deal analysis minimum inputs: asking price, monthly rent, annual expenses, financing terms
- All analysis is informational — the agent presents numbers and flags risks, it does not make buy/pass recommendations
- KPI state is persistent — you can update a property's data over time and re-run analysis each month

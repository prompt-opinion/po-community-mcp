# Local development

Create and activate a virtual environment first:

On macOS/Linux:
```bash
python3 -m venv venv
source venv/bin/activate
```

On Windows:
```bash
python -m venv venv
venv\Scripts\activate
```

Then install dependencies:

```bash
pip install -r requirements.txt
```

And then run `uvicorn main:app --reload`.

The server will be available at `http://localhost:8000`. Test it:

```bash
curl -i http://localhost:8000/mcp
```

# Owned clinical workflow tools

This Python server also exposes the owned Prompt Opinion clinical workflow MCP tools used for:

- shared workflow output validation, risk scoring, and audit event shaping
- chart summary and patient snapshot normalization
- medication review
- care gap evaluation
- lab/vitals trend analysis
- prior authorization packet and appeal drafting
- clinical coding support with coder-review and licensing guardrails
- referral readiness/routing
- transition-of-care briefs, patient instructions, and follow-up tasks

The deterministic implementation is vendored in `marketplace_agents/`, and the FastMCP upload wrappers live in `tools/clinical_workflow_tools.py`.

Useful tool entry points:

- `ListOwnedClinicalWorkflowTools`
- `CallOwnedClinicalWorkflowTool`
- `GetClinicalChartSummary`
- `ReviewClinicalMedications`
- `EvaluatePatientCareGaps`
- `AnalyzePatientLabVitalsTrends`
- `CheckPriorAuthorizationRequirement`
- `SuggestClinicalCodeCandidates`
- `EvaluatePatientReferralNeed`
- `BuildTransitionDischargeBrief`

Most tools can use Prompt Opinion FHIR context headers, or accept an explicit `fhirPayload` Bundle for local testing. All high-impact clinical, coding, prior-auth, referral, and patient-facing outputs remain draft/review-only.

# Running with Docker

From the repository root, run:

```bash
docker compose -f docker-compose-local.yml up python --build
```

The server will be available at `http://localhost:55002`. Test it:

```bash
curl -i http://localhost:55002/mcp
```

To stop:

```bash
docker compose -f docker-compose-local.yml down
```

# Debugging with vscode

We use the built-in [Python Debugger](https://marketplace.visualstudio.com/items?itemName=ms-python.debugpy) extension to debug the server locally. To debug in vscode:

- (Optional) Add your breakpoints in vscode now. You can always do this later.
- Ensure `main.py` is opened and it is the current active tab.
- On the left hand navigation pane in vscode, select the `Run and Debug` tab.
- Ensure `Python Debugger: FastAPI` is the selected configuration in the dropdown.
- Click on the green play (Start Debugging) button.

# Local development

Start with `npm install`.

And then run `npm run start`.

# Available tools

- `FindPatientId`: finds a patient id from a first/last name search
- `GetPatientAge`: reads a patient and returns the current age
- `CreatePatientWithConditionsFromPrompt`: accepts natural language such as `Create the patient John Doe that is 57 years old with high cholesterol that started last week.` and creates a `Patient` plus linked `Condition` resources

# Verification

Fast local verification:

```bash
npm run verify:natural-language-patient-tool
```

Real end-to-end verification through the actual MCP HTTP server against a live FHIR server:

```bash
PORT=56000 npm run start
```

In a second shell:

```bash
REAL_FHIR_SERVER_URL=http://hapi.fhir.org/baseR4 \
MCP_BASE_URL=http://localhost:56000/mcp \
npm run verify:real:natural-language-patient-tool
```

The real verification script:

- connects to the running MCP server over HTTP
- calls `CreatePatientWithConditionsFromPrompt`
- reads the created `Patient` and `Condition` back from the FHIR server
- fails if the resources cannot be retrieved or do not match the expected linkage

# Debugging with vscode

We use [tsx](https://tsx.is/vscode) to debug the server locally. To debug in vscode:

- (Optional) Add your breakpoints in vscode now. You can always do this later.
- Ensure `index.ts` is opened and it is the current active tab.
- On the left hand navigation pane in vscode, select the `Run and Debug` tab.
- Ensure `tsx` is the selected configuration in the dropdown.
- Click on the green play (Start Debugging) button.

# Local development

Create and activate a virtual environment first:

```bash
python3 -m venv venv
source venv/bin/activate
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

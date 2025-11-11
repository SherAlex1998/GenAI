# Steam LLM Assistant

A Streamlit web application that lets you explore a Steam games database and interact with an OpenAI-powered agent. The agent can query the local SQLite database, provide insights, and even create GitHub issues on your behalf.

## Features
- Chat interface built with Streamlit and backed by `LLMAgent`.
- Access to a curated Steam dataset stored in `steam.sqlite`.
- Function calling for database queries and genre statistics.
- GitHub issue creation via `create_github_issue`, using credentials from environment variables.
- Sidebar with a live log of agent actions for easier debugging.

## Project Structure
- `streamlit_app.py` — Streamlit entry point with chat UI and logging sidebar.
- `llm_agent.py` — Business logic for interacting with OpenAI and tool calls.
- `db_manager.py` — Thin wrapper around the Steam SQLite database.
- `issue_manager.py` — Minimal helper for creating GitHub issues.
- `requirements.txt` — Dependencies needed to run the app.
- `steam.sqlite` — Steam games dataset (ensure the file is present locally).

## Getting Started
1. **Clone the repository**
   ```bash
   git clone <your-repo-url>
   cd <your-repo-folder>
   ```
2. **Create and activate a virtual environment (optional but recommended)**
   ```bash
   python -m venv venv
   source venv/bin/activate      # Linux/macOS
   venv\Scripts\activate         # Windows
   ```
3. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```
4. **Prepare environment variables**
   Create a `.env` file in the project root:
   ```
   OPENAI_API_KEY=your-openai-key
   STEAM_DB_PATH=steam.sqlite          # optional, defaults to steam.sqlite in project root
   GITHUB_TOKEN=your-github-token
   GITHUB_REPO=owner/repo              # e.g. octocat/Hello-World
   GITHUB_API_URL=https://api.github.com  # optional override
   ```

## Running Locally
```bash
streamlit run streamlit_app.py
```

The application starts in your default browser. Use the chat box to ask about Steam games or request creation of GitHub issues. Logs appear in the sidebar for transparency.

## Deploying to Hugging Face Spaces
1. Create a new Space and select the **Streamlit** template.
2. Push the project files (including `steam.sqlite`) to the Space repository.
3. Add secrets under *Settings → Secrets*:
   - `OPENAI_API_KEY`
   - `GITHUB_TOKEN`
   - `GITHUB_REPO`
   - Any additional variables you need (`STEAM_DB_PATH`, `GITHUB_API_URL`).
4. Hugging Face will install dependencies and launch the app automatically.

## Screenshots
Add usage examples here:
```
![Chat view](path/to/screenshot1.png)
![Issue creation](path/to/screenshot2.png)
```

## Troubleshooting
- **Missing tokens or database**: The app will display errors if required environment variables or the SQLite file are absent.
- **GitHub 403/404 errors**: Ensure `GITHUB_REPO` is correct and the token has `repo` (or `Issues: Read and write` for fine-grained tokens) permissions.

## License
Specify your preferred license here (MIT, Apache, proprietary, etc.).


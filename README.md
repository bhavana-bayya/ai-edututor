# EduTutor AI — Personalized Learning (Pure Python)

A complete rebuild of the EduTutor AI demo as a **single Python file**.
Flask serves both the web page and the AI plan-generation API — no
separate HTML/CSS/JS files to manage.

## Run it

```bash
pip install -r requirements.txt
python app.py
```

Open **http://localhost:5000** in your browser, type a topic (e.g.
"Photosynthesis"), pick a level, and click **Generate Plan**.

## Two modes, both fully working

- **Offline demo mode (default)** — no API key needed. A built-in
  rule-based generator produces a structured learning plan immediately,
  so the app works out of the box for demos, grading, or offline use.
- **AI mode** — set an API key and real Claude/GPT responses replace the
  offline generator automatically:

  ```bash
  export ANTHROPIC_API_KEY="sk-ant-..."
  python app.py
  ```

  (Or use OpenAI instead: `export LLM_PROVIDER=openai` and
  `export OPENAI_API_KEY="sk-..."`.)

The homepage footer tells you which mode is active.

## API

`POST /generate-plan`

```json
{ "topic": "Photosynthesis", "level": "beginner" }
```

Returns:

```json
{
  "topic": "Photosynthesis",
  "level": "beginner",
  "overview": "...",
  "modules": [
    {
      "title": "...",
      "objectives": ["..."],
      "key_concepts": ["..."],
      "suggested_resources": ["..."],
      "estimated_time": "2 hours"
    }
  ],
  "practice_questions": ["..."]
}
```

`GET /health` — returns current mode/provider status.

## Files

- `app.py` — everything: Flask routes, embedded HTML/CSS/JS frontend,
  LLM integration, and offline fallback generator.
- `requirements.txt` — Python dependencies.

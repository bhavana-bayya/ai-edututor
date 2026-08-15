"""
EduTutor AI - Personalized Learning (single-file, all-Python)
================================================================
A complete, self-contained rebuild of the EduTutor AI demo
(https://bhavana-bayya.github.io/ai-edututor-with-generative-ai/) as one
Python/Flask application. Flask serves both the web page (HTML/CSS/JS,
embedded as strings below) AND the API that generates the personalized
learning plan. There are no separate .html/.js/.css files to manage.

FEATURES
--------
- Single command to run: `python app.py`
- One page UI: enter a topic, pick a level, click "Generate Plan"
- Plan generation calls the Anthropic Claude API when ANTHROPIC_API_KEY
  is set (OpenAI supported too, see LLM_PROVIDER below)
- If no API key is configured, an offline rule-based generator produces a
  reasonable plan automatically, so the app always works out of the box
  for demos/grading without requiring any external service or key.

SETUP
-----
1. pip install -r requirements.txt
2. (optional, for real AI-generated plans)
       export ANTHROPIC_API_KEY="sk-ant-..."
3. python app.py
4. Open http://localhost:5000 in a browser
"""

import json
import os
import re
import textwrap

from flask import Flask, jsonify, render_template_string, request

# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------

LLM_PROVIDER = os.environ.get("LLM_PROVIDER", "anthropic")  # "anthropic" or "openai"
ANTHROPIC_MODEL = os.environ.get("ANTHROPIC_MODEL", "claude-sonnet-4-6")
OPENAI_MODEL = os.environ.get("OPENAI_MODEL", "gpt-4o-mini")

HAS_ANTHROPIC_KEY = bool(os.environ.get("ANTHROPIC_API_KEY"))
HAS_OPENAI_KEY = bool(os.environ.get("OPENAI_API_KEY"))

app = Flask(__name__)


# ---------------------------------------------------------------------------
# Frontend (HTML + CSS + JS as a single Python string, served by Flask)
# ---------------------------------------------------------------------------

PAGE_TEMPLATE = """
<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>EduTutor AI - Personalized Learning</title>
<style>
  :root {
    --bg: #0f172a;
    --card: #1e293b;
    --accent: #6366f1;
    --accent-hover: #818cf8;
    --text: #e2e8f0;
    --muted: #94a3b8;
  }
  * { box-sizing: border-box; }
  body {
    margin: 0;
    font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif;
    background: linear-gradient(160deg, var(--bg), #1e1b4b);
    color: var(--text);
    min-height: 100vh;
    padding: 40px 16px;
  }
  .wrap { max-width: 760px; margin: 0 auto; }
  header { text-align: center; margin-bottom: 32px; }
  header h1 { font-size: 2.2rem; margin-bottom: 4px; }
  header p { color: var(--muted); margin-top: 0; }
  .card {
    background: var(--card);
    border-radius: 14px;
    padding: 24px;
    box-shadow: 0 10px 30px rgba(0,0,0,0.3);
    margin-bottom: 24px;
  }
  .row { display: flex; gap: 12px; flex-wrap: wrap; }
  input[type=text], select {
    flex: 1;
    min-width: 200px;
    padding: 12px 14px;
    border-radius: 8px;
    border: 1px solid #334155;
    background: #0f172a;
    color: var(--text);
    font-size: 1rem;
  }
  button {
    background: var(--accent);
    color: white;
    border: none;
    padding: 12px 22px;
    border-radius: 8px;
    font-size: 1rem;
    font-weight: 600;
    cursor: pointer;
    transition: background 0.15s ease;
  }
  button:hover { background: var(--accent-hover); }
  button:disabled { opacity: 0.6; cursor: not-allowed; }
  .status { color: var(--muted); margin-top: 10px; font-size: 0.9rem; }
  .module {
    border-left: 3px solid var(--accent);
    padding-left: 14px;
    margin-bottom: 18px;
  }
  .module h3 { margin: 0 0 6px 0; }
  .module .meta { color: var(--muted); font-size: 0.85rem; margin-bottom: 8px; }
  .module ul { margin: 4px 0; padding-left: 20px; }
  .badge {
    display: inline-block;
    background: #312e81;
    color: #c7d2fe;
    padding: 2px 10px;
    border-radius: 999px;
    font-size: 0.75rem;
    margin-bottom: 8px;
  }
  footer { text-align: center; color: var(--muted); font-size: 0.85rem; margin-top: 32px; }
  #error { color: #fca5a5; margin-top: 10px; }
</style>
</head>
<body>
<div class="wrap">
  <header>
    <h1>🎓 EduTutor AI</h1>
    <p>Personalized Learning with Generative AI</p>
  </header>

  <div class="card">
    <div class="row">
      <input type="text" id="topic" placeholder="Enter a topic you want to learn about (e.g. Photosynthesis)">
      <select id="level">
        <option value="beginner">Beginner</option>
        <option value="intermediate">Intermediate</option>
        <option value="advanced">Advanced</option>
      </select>
      <button id="generateBtn" onclick="generatePlan()">Generate Plan</button>
    </div>
    <div class="status" id="status"></div>
    <div id="error"></div>
  </div>

  <div id="results"></div>

  <footer>© 2025 EduTutor AI | Smart Personalized Learning — {{ mode }}</footer>
</div>

<script>
async function generatePlan() {
  const topic = document.getElementById('topic').value.trim();
  const level = document.getElementById('level').value;
  const btn = document.getElementById('generateBtn');
  const status = document.getElementById('status');
  const errorBox = document.getElementById('error');
  const results = document.getElementById('results');

  errorBox.textContent = '';
  results.innerHTML = '';

  if (!topic) {
    errorBox.textContent = 'Please enter a topic first.';
    return;
  }

  btn.disabled = true;
  status.textContent = 'Generating your personalized plan...';

  try {
    const res = await fetch('/generate-plan', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ topic, level })
    });
    const data = await res.json();

    if (!res.ok) {
      throw new Error(data.error || 'Something went wrong.');
    }

    renderPlan(data);
    status.textContent = '';
  } catch (err) {
    errorBox.textContent = err.message;
    status.textContent = '';
  } finally {
    btn.disabled = false;
  }
}

function renderPlan(plan) {
  const results = document.getElementById('results');

  let html = `<div class="card">
      <span class="badge">${plan.level}</span>
      <h2>${plan.topic}</h2>
      <p>${plan.overview}</p>
    </div>`;

  html += `<div class="card"><h2>Learning Modules</h2>`;
  plan.modules.forEach((m, i) => {
    html += `<div class="module">
        <h3>${i + 1}. ${m.title}</h3>
        <div class="meta">⏱ ${m.estimated_time}</div>
        <strong>Objectives</strong>
        <ul>${m.objectives.map(o => `<li>${o}</li>`).join('')}</ul>
        <strong>Key Concepts</strong>
        <ul>${m.key_concepts.map(c => `<li>${c}</li>`).join('')}</ul>
        <strong>Suggested Resources</strong>
        <ul>${m.suggested_resources.map(r => `<li>${r}</li>`).join('')}</ul>
      </div>`;
  });
  html += `</div>`;

  if (plan.practice_questions && plan.practice_questions.length) {
    html += `<div class="card"><h2>Practice Questions</h2>
        <ul>${plan.practice_questions.map(q => `<li>${q}</li>`).join('')}</ul>
      </div>`;
  }

  results.innerHTML = html;
}
</script>
</body>
</html>
"""


# ---------------------------------------------------------------------------
# Plan generation: real LLM call, with an offline fallback generator
# ---------------------------------------------------------------------------

def build_prompt(topic: str, level: str) -> str:
    return f"""You are an expert curriculum designer building a personalized
learning plan for a student.

Topic: {topic}
Learner level: {level}

Return ONLY valid JSON (no markdown fences, no commentary) matching this
exact shape:

{{
  "topic": "{topic}",
  "level": "{level}",
  "overview": "2-3 sentence overview of what the learner will get out of this plan",
  "modules": [
    {{
      "title": "Module title",
      "objectives": ["objective 1", "objective 2"],
      "key_concepts": ["concept 1", "concept 2", "concept 3"],
      "suggested_resources": ["resource or resource type 1", "resource 2"],
      "estimated_time": "e.g. 2 hours"
    }}
  ],
  "practice_questions": ["question 1", "question 2", "question 3"]
}}

Produce 3 to 5 modules, ordered from foundational to advanced. Keep it
concrete and specific to the topic, not generic filler."""


def call_anthropic(prompt: str) -> str:
    import anthropic

    client = anthropic.Anthropic()
    response = client.messages.create(
        model=ANTHROPIC_MODEL,
        max_tokens=2000,
        messages=[{"role": "user", "content": prompt}],
    )
    return "".join(block.text for block in response.content if block.type == "text")


def call_openai(prompt: str) -> str:
    from openai import OpenAI

    client = OpenAI()
    response = client.chat.completions.create(
        model=OPENAI_MODEL,
        messages=[{"role": "user", "content": prompt}],
        temperature=0.7,
    )
    return response.choices[0].message.content


def extract_json(text: str) -> dict:
    cleaned = re.sub(r"^```(?:json)?|```$", "", text.strip(), flags=re.MULTILINE).strip()
    return json.loads(cleaned)


def offline_generate_plan(topic: str, level: str) -> dict:
    """
    Rule-based fallback used when no LLM API key is configured, so the app
    is fully functional out of the box without any external dependency.
    """
    stage_names = {
        "beginner": ["Foundations", "Core Ideas", "Guided Practice"],
        "intermediate": ["Refresher", "Core Concepts", "Applied Practice", "Common Pitfalls"],
        "advanced": ["Advanced Theory", "Edge Cases & Nuance", "Real-World Application", "Synthesis Project"],
    }
    stages = stage_names.get(level, stage_names["beginner"])

    modules = []
    for i, stage in enumerate(stages, start=1):
        modules.append({
            "title": f"{stage}: {topic}",
            "objectives": [
                f"Understand the {stage.lower()} of {topic}",
                f"Be able to explain {topic} concepts from this stage in your own words",
            ],
            "key_concepts": [
                f"{topic} - core terminology",
                f"{topic} - stage {i} principles",
                f"How {stage.lower()} connects to the next stage",
            ],
            "suggested_resources": [
                f"Introductory article or textbook chapter on {topic}",
                f"Short video lecture covering {stage.lower()} of {topic}",
            ],
            "estimated_time": f"{1 + i} hours",
        })

    return {
        "topic": topic,
        "level": level,
        "overview": (
            f"This is an offline, auto-generated starter plan for learning {topic} "
            f"at the {level} level. Connect an LLM API key for richer, "
            f"AI-personalized content."
        ),
        "modules": modules,
        "practice_questions": [
            f"In your own words, define the core concept behind {topic}.",
            f"Give one real-world example where {topic} applies.",
            f"What is one common misconception about {topic}, and why is it wrong?",
        ],
    }


def generate_plan(topic: str, level: str) -> dict:
    use_llm = (LLM_PROVIDER == "anthropic" and HAS_ANTHROPIC_KEY) or (
        LLM_PROVIDER == "openai" and HAS_OPENAI_KEY
    )

    if not use_llm:
        return offline_generate_plan(topic, level)

    prompt = build_prompt(topic, level)
    raw = call_openai(prompt) if LLM_PROVIDER == "openai" else call_anthropic(prompt)
    return extract_json(raw)


# ---------------------------------------------------------------------------
# Routes
# ---------------------------------------------------------------------------

@app.route("/")
def index():
    mode = "AI mode" if (HAS_ANTHROPIC_KEY or HAS_OPENAI_KEY) else "Offline demo mode"
    return render_template_string(PAGE_TEMPLATE, mode=mode)


@app.route("/health")
def health():
    return jsonify({
        "status": "ok",
        "provider": LLM_PROVIDER,
        "ai_enabled": HAS_ANTHROPIC_KEY or HAS_OPENAI_KEY,
    })


@app.route("/generate-plan", methods=["POST"])
def generate_plan_route():
    data = request.get_json(silent=True) or {}
    topic = (data.get("topic") or "").strip()
    level = (data.get("level") or "beginner").strip().lower()

    if not topic:
        return jsonify({"error": "Please provide a 'topic' in the request body."}), 400

    if level not in ("beginner", "intermediate", "advanced"):
        level = "beginner"

    try:
        plan = generate_plan(topic, level)
    except json.JSONDecodeError:
        return jsonify({"error": "The model returned content that wasn't valid JSON. Try again."}), 502
    except Exception as exc:  # noqa: BLE001 - surface provider/auth errors to the client
        return jsonify({"error": f"Failed to generate plan: {exc}"}), 500

    return jsonify(plan)


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    mode = "AI mode (LLM connected)" if (HAS_ANTHROPIC_KEY or HAS_OPENAI_KEY) else "Offline demo mode (no API key set)"
    print(textwrap.dedent(f"""
        EduTutor AI starting...
        Mode: {mode}
        Open: http://localhost:{port}
    """))
    app.run(host="0.0.0.0", port=port, debug=True)

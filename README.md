<picture>
  <source media="(prefers-color-scheme: dark)" srcset="assets/dark/hero.svg">
  <img src="assets/light/hero.svg" width="100%" alt="Akshay Bajpai. Wrangling AI, mostly after dark. I build production LLM systems that answer to humans: agents, retrieval, and text-to-SQL that shows its work and waits for a person before it runs.">
</picture>

<p align="center">
  <a href="https://www.akshaybajpai.com"><b>akshaybajpai.com</b></a>
  &nbsp;&nbsp;✦&nbsp;&nbsp;
  <a href="https://github.com/ax5hay"><b>github.com/ax5hay</b></a> <sub>(personal)</sub>
</p>

<br>

> [!NOTE]
> **About this page.** This is my work account, and this README covers only the work I do at Telomere. It is not my full tech stack or a record of everything I build. My personal projects, open-source work and the wider set of tools I use are on my [personal GitHub](https://github.com/ax5hay) and [website](https://www.akshaybajpai.com), and they cover a good deal more than this page does.
>
> Apart from this page, everything on this account is private. The plates below are drawn from its git history.

<br>

## ✦ Field notes

I'm an AI engineer at **Telomere**. Most of my time goes into a **multi-tenant AI platform for fertility and surrogacy agencies**. It has three assistants behind one API:

- **Intake** turns long application forms into a conversation.
- **Knowledge** answers questions from each agency's own documents.
- **Reports** lets an admin ask for a report in plain English. It writes the SQL, shows a preview, and runs the query only after the admin confirms.

I wrote most of that codebase: two of every three commits, the agent loops, the safety gates, the AWS infrastructure, and the tests and runbooks around them. Most of it was written at night, as the sky chart below shows.

<br>

<picture>
  <source media="(prefers-color-scheme: dark)" srcset="assets/dark/magnitudes.svg">
  <img src="assets/light/magnitudes.svg" width="100%" alt="Magnitudes. 775 contributions this year, all since May. 662 commits to the AI platform, 68% of every commit in that repository. 107 pull requests opened, 76 merged. 2,683 files touched. 8,000+ columns across 193 tables that the reports agent can read. 80% of commits land between 18:00 and 05:00 IST.">
</picture>

<br><br>

<picture>
  <source media="(prefers-color-scheme: dark)" srcset="assets/dark/sky.svg">
  <img src="assets/light/sky.svg" width="100%" alt="Sky chart, June to November 2026. 540 commits plotted by day and hour, with night at the top. 433 of them, 80%, were made between 18:00 and 05:00 IST. The busiest hour is 21:00. A light curve underneath shows commits per week, brightest in October.">
</picture>

<br><br>

<picture>
  <source media="(prefers-color-scheme: dark)" srcset="assets/dark/orrery.svg">
  <img src="assets/light/orrery.svg" width="100%" alt="Orrery. An LLM gateway at the centre, with three assistants in orbit. Reports: plain English in, SQL out, with a preview and an admin's confirmation before anything runs. Knowledge: answers from each agency's own documents, scoped to who is asking. Intake: long forms as a conversation, with personas, risk flags and CRM sync. Underneath: one chat API where the token picks the bot and the tenant, on AWS CDK, Lambda, RDS, Redis, SQS and WebSockets across three US regions.">
</picture>

<details>
<summary><b>The orrery, in words</b></summary>
<br>

| Body | What it does | How it stays honest |
| :--- | :--- | :--- |
| **LLM gateway** | One gateway for every model call: per-bot keys, routing, prompt caching, fallbacks | Self-heals when a model disappears; no bot calls a provider directly |
| **Reports** | An agentic tool loop that turns an admin's question into SQL over a 193-table schema | Grammar-checked against the product's own report builder; preview first, and nothing runs until an admin confirms; long turns go async over SQS and WebSockets |
| **Knowledge** | Answers from the agency's knowledge base, scraped pages and uploaded documents | Scoped by audience (intended parents, surrogates, donors); a grounding pass checks each reply against its sources |
| **Intake** | Walks applicants through the agency's real forms as a chat, in the right persona | Deterministic YAML rules plus LLM consistency checks raise risk flags, and every answer syncs back to the CRM |
| **Underneath** | JWT tenant routing, Python and FastAPI, React and TypeScript, MySQL, Redis | AWS CDK per environment, staging plus up to three production regions, pytest and Playwright end to end |

</details>

<br>

<picture>
  <source media="(prefers-color-scheme: dark)" srcset="assets/dark/spectra.svg">
  <img src="assets/light/spectra.svg" width="100%" alt="Spectra. 78 technologies across 7 domains in this codebase, each domain drawn as an emission spectrum with one line per technology: languages, AI and LLM systems, backend, data stores, cloud and infrastructure, frontend, and testing.">
</picture>

<details>
<summary><b>Every line in the spectra, as text</b> <sub>(this codebase only)</sub></summary>
<br>

- **Languages.** Python, TypeScript, SQL (MySQL), Bash, PowerShell, YAML
- **AI & LLM systems.** OpenRouter, Anthropic Claude, LLM gateway, Prompt caching, Agentic tool loop, Text-to-SQL agent, Workflow RAG, Knowledge-base RAG, Grounding pipeline, BM25 retrieval, Embeddings, Reranking, Persona engine, LLM consistency checks, Multi-slot extraction, PII redaction, pypdf, python-docx
- **Backend & APIs.** FastAPI, Uvicorn, Pydantic, pydantic-settings, httpx, requests, PyJWT, JWT tenant routing, python-multipart, Mangum, WebSockets, Webhooks, cryptography
- **Data stores & SQL.** MySQL 8, Redis 7, SQLAlchemy 2.0, Alembic, PyMySQL, sqlglot (SQL ASTs), Per-tenant schema routing
- **Cloud & infrastructure.** AWS CDK, AWS Lambda, API Gateway, API Gateway WebSockets, Amazon SQS, Amazon RDS, ElastiCache, VPC & security groups, IAM, Secrets Manager, SSM Parameter Store, KMS, Amazon S3, CloudWatch, boto3, aws-vault, Docker, Docker Compose, Multi-region deploys
- **Frontend.** React 18, Preact, Vite, Fontsource
- **Testing & quality.** pytest, pytest-asyncio, pytest-cov, Playwright, Vitest, Ruff, mypy, pre-commit, Schema test harness, GitHub Actions, Streamlit (deploy console)

</details>

<br>

## ✦ Catalogue

The objects in the plates above, numbered the way astronomers number theirs. Both are private, so they are described here rather than linked.

| No. | Object | What it is | Instruments |
| :-- | :-- | :-- | :-- |
| `BJP 001` | **Agency AI platform** <sub>private · work</sub> | The system in the orrery: intake, knowledge and reports assistants for fertility and surrogacy agencies, with one gateway and one API | Python · FastAPI · React · AWS CDK · MySQL · Redis |
| `BJP 002` | **Reports agent** <sub>private · work</sub> | Plain-English reporting over 193 tables and 8,000+ approved columns. Every query is grammar-checked, previewed, and confirmed by an admin before it runs | sqlglot · agentic tool loop · SQS · WebSockets |

<br>

## ✦ Observing rules

1. **Preview before it runs.** When an AI writes against real data, it shows its work and waits for a person.
2. **No model where a rule will do.** A deterministic check is cheaper, faster, and never hallucinates.
3. **Numbers come with their conditions.** Every figure on this page is computed from git history or a results file.
4. **Write it down.** Specs, decision records and handoff notes ship with the code, so the next person starts where I stopped.

<br>

<picture>
  <source media="(prefers-color-scheme: dark)" srcset="assets/dark/dawn.svg">
  <img src="assets/light/dawn.svg" width="100%" alt="Dawn over the horizon. Lights off at dawn. Shipped by morning.">
</picture>

<p align="center"><sub>Every plate is drawn by <a href="scripts/draw.py"><code>scripts/draw.py</code></a> from <a href="data/">data/</a>, and switches between a night sky and a printed star atlas with your theme. Observed 12 Nov 2026. Personal work: <a href="https://github.com/ax5hay">github.com/ax5hay</a> · <a href="https://www.akshaybajpai.com">akshaybajpai.com</a></sub></p>

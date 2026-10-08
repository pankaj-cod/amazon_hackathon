# Carbon Offset Analyser

A full-stack land analysis application for estimating environmental metrics,
carbon stock, sequestration potential, and project risk.

## Repository Structure

```text
.
├── apps/
│   ├── api/                  # FastAPI service, ML models, tests, and data tools
│   └── web/                  # Next.js user interface
├── infrastructure/
│   └── supabase/             # Supabase schema and database migrations
├── docs/                     # Methodology and dataset documentation
├── scripts/                  # Repository setup, startup, and verification tools
├── .env.example              # Shared local runtime settings
└── package.json              # Root developer commands
```

## Local Setup

Requirements:

- Python 3.10-3.12
- Node.js 18 or newer
- npm

Install all dependencies and create local environment files:

```bash
npm run setup
```

Then configure:

- `.env` for shared ports and startup behavior
- `apps/api/.env` for Supabase and Google Earth Engine credentials
- `apps/web/.env.local` for the public Supabase values and API URL

Start both services:

```bash
npm run dev
```

Local URLs:

- Web application: <http://localhost:3000>
- API: <http://localhost:8000>
- Interactive API documentation: <http://localhost:8000/docs>

## Common Commands

```bash
npm run dev:web
npm run build:web
npm run test:api
npm run verify:api
```

The API can also be started independently:

```bash
cd apps/api
./.venv/bin/uvicorn app.main:app --reload --port 8000
```

See [`docs/PARAMETERS_DOCUMENTATION.md`](docs/PARAMETERS_DOCUMENTATION.md)
for calculation methodology and data-source details.

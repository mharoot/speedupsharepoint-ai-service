# Speed Up SharePoint AI Service - Local Development Kit

Speed Up SharePoint AI-powered quote generation service.

## Quick Start

```bash
# 1. Create virtual environment
python3.11 -m venv .venv
source .venv/bin/activate

# 2. Install dependencies
pip install -r requirements.txt

# 3. Configure environment
cp .env.example .env
# Edit .env and add your OpenAI API key

# 4. Test locally
python test_local.py

# 5. Run as Azure Function
func start
```

## Project Structure

```
speedupsharepoint-ai-service/
├── function_app.py         # Azure Function entry point
├── requirements.txt        # Python dependencies
├── .env.example           # Environment template
├── ai_service/            # Core AI logic
│   ├── quote_generator.py
│   ├── context_builder.py
│   └── models.py
├── data/                  # Sample data
│   └── closet_world_catalog.json
└── tests/                 # Tests
    └── test_local.py
```

## Deployment

```bash
# Deploy to Azure
func azure functionapp publish speedupsharepoint-ai-service
```

See SETUP_GUIDE.md for detailed instructions.

# Speed Up SharePoint AI Service - Complete Setup Guide

## 🎯 What You're Building

An AI-powered quote generation service that:
- Uses GPT-4 to generate accurate quotes based on historical data
- Runs locally for development
- Deploys to Azure Functions for production
- Costs ~$0.03 per quote generation

---

## 📋 Prerequisites

### 1. Install Homebrew (if not installed)
```bash
/bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"
```

### 2. Install Python 3.11
```bash
brew install python@3.11
python3.11 --version  # Should show 3.11.x
```

### 3. Install Visual Studio Code
```bash
brew install --cask visual-studio-code
```

### 4. Install Azure Functions Core Tools
```bash
brew tap azure/functions
brew install azure-functions-core-tools@4
func --version  # Should show 4.x
```

### 5. Install Azure CLI
```bash
brew install azure-cli
az login  # Opens browser to login
```

### 6. Get OpenAI API Key
1. Go to https://platform.openai.com/api-keys
2. Click "Create new secret key"
3. Name it: `speedupsharepoint-ai-service-dev`
4. **Copy the key immediately** (you won't see it again!)
5. Save it in a safe place (1Password, etc.)

---

## 🚀 Local Setup (20 minutes)

### Step 1: Navigate to the Project
```bash
cd ~/Documents/projects  # or wherever you keep projects
cd speedupsharepoint-ai-service-starter
```

### Step 2: Create Virtual Environment
```bash
# Create virtual environment
python3.11 -m venv .venv

# Activate it (you'll need to do this every time you open a new terminal)
source .venv/bin/activate

# Your prompt should now show (.venv) at the start
# Example: (.venv) michael@MacBook speedupsharepoint-ai-service-starter %

# Upgrade pip
pip install --upgrade pip
```

### Step 3: Install Dependencies
```bash
pip install -r requirements.txt

# This will take 2-3 minutes
# You should see messages like:
# Successfully installed azure-functions-1.19.0 openai-1.10.0 ...
```

### Step 4: Configure Environment
```bash
# Copy the example .env file
cp .env.example .env

# Open .env in your editor
code .env  # or use nano, vim, etc.

# Replace sk-your-key-here with your actual OpenAI API key
# Save and close
```

Your `.env` should look like:
```
OPENAI_API_KEY=sk-proj-abc123...xyz
OPENAI_MODEL=gpt-4-turbo
ENVIRONMENT=development
LOG_LEVEL=DEBUG
```

### Step 5: Test Locally (Simple Test)
```bash
# Make the test script executable
chmod +x test_local.py

# Run it
python test_local.py
```

**Expected Output:**
```
🚀 Testing Speed Up SharePoint AI Service Locally

✅ Loaded 5 catalog items

📝 Quote Request:
  Tenant: closet-world
  Type: closet
  Notes: I need to organize my master bedroom closet...

🤖 Calling OpenAI API...

✅ Quote Generated Successfully!

Quote ID: quote_closet-world_1736789012
Total: $1,234.56
Margin: 38.5%
Confidence: 0.85

📋 Line Items:
  - 6x CW-SHELF-16-36: Wire Shelf 16" x 36"
    $45.00 each = $270.00
    💡 6 shelves provide adequate storage for 8ft width

  - 3x CW-ROD-36: Hanging Rod 36"
    $25.00 each = $75.00
    💡 Multiple hanging rods for different clothing types
...
```

### Step 6: Run as Azure Function Locally
```bash
# Start the function runtime
func start

# You should see:
# Azure Functions Core Tools
# Core Tools Version: 4.x.x
# Function Runtime Version: 4.x.x
# 
# Functions:
#   GenerateQuote: [POST] http://localhost:7071/api/ai/generate-quote
#   HealthCheck: [GET] http://localhost:7071/api/health
```

**Keep this terminal open!** The function is now running.

### Step 7: Test the Function (In a NEW Terminal)
Open a new terminal window and run:

```bash
# Test health check
curl http://localhost:7071/api/health

# Should return: {"status":"healthy","service":"speedupsharepoint-ai-service"}

# Test quote generation
curl -X POST http://localhost:7071/api/ai/generate-quote \
  -H "Content-Type: application/json" \
  -d '{
    "tenant_id": "closet-world",
    "project_type": "closet",
    "customer_notes": "8x8 master closet, need more shoe storage",
    "square_footage": 64,
    "ceiling_height": 8,
    "budget_range": "standard"
  }'
```

You should get back a JSON response with the generated quote!

---

## ☁️ Deploy to Azure (30 minutes)

### Step 1: Create Azure Resources
```bash
# Set variables (customize these!)
RESOURCE_GROUP="speedupsharepoint-ai-rg"
LOCATION="westus2"
STORAGE_ACCOUNT="speedupsharepointaistorage$(date +%s)"
FUNCTION_APP="speedupsharepoint-ai-service-michael"  # Change 'michael' to your name

# Create resource group
az group create \
  --name $RESOURCE_GROUP \
  --location $LOCATION

# Create storage account
az storage account create \
  --name $STORAGE_ACCOUNT \
  --resource-group $RESOURCE_GROUP \
  --location $LOCATION \
  --sku Standard_LRS

# Create Function App
az functionapp create \
  --resource-group $RESOURCE_GROUP \
  --consumption-plan-location $LOCATION \
  --runtime python \
  --runtime-version 3.11 \
  --functions-version 4 \
  --name $FUNCTION_APP \
  --storage-account $STORAGE_ACCOUNT \
  --os-type Linux
```

### Step 2: Configure Application Settings
```bash
# Set OpenAI API key (IMPORTANT: Use your real key!)
az functionapp config appsettings set \
  --name $FUNCTION_APP \
  --resource-group $RESOURCE_GROUP \
  --settings "OPENAI_API_KEY=sk-your-actual-key"

# Set model
az functionapp config appsettings set \
  --name $FUNCTION_APP \
  --resource-group $RESOURCE_GROUP \
  --settings "OPENAI_MODEL=gpt-4-turbo"
```

### Step 3: Deploy!
```bash
func azure functionapp publish $FUNCTION_APP

# This takes 2-3 minutes
# You should see:
# Getting site publishing info...
# Uploading package...
# Upload completed successfully.
# Deployment completed successfully.
# 
# Functions in speedupsharepoint-ai-service-michael:
#   GenerateQuote - https://speedupsharepoint-ai-service-michael.azurewebsites.net/api/ai/generate-quote
#   HealthCheck - https://speedupsharepoint-ai-service-michael.azurewebsites.net/api/health
```

### Step 4: Test in Azure
```bash
# Test health endpoint
curl https://speedupsharepoint-ai-service-michael.azurewebsites.net/api/health

# Test quote generation (need function key for security)
# Get the function key from Azure Portal or:
FUNCTION_KEY=$(az functionapp keys list \
  --name $FUNCTION_APP \
  --resource-group $RESOURCE_GROUP \
  --query "functionKeys.default" -o tsv)

# Now test it:
curl -X POST "https://speedupsharepoint-ai-service-michael.azurewebsites.net/api/ai/generate-quote?code=$FUNCTION_KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "tenant_id": "closet-world",
    "project_type": "closet",
    "customer_notes": "8x8 master closet, lots of shoes",
    "square_footage": 64
  }'
```

🎉 **It's live!** Your AI service is now running in Azure.

---

## 📁 Project Structure Explained

```
speedupsharepoint-ai-service-starter/
│
├── function_app.py              # Main entry point (Azure Function)
│   └── Defines HTTP endpoints (/api/ai/generate-quote, /health)
│
├── ai_service/                  # Core AI logic (the brain)
│   ├── models.py               # Data structures (QuoteRequest, QuoteResponse)
│   ├── context_builder.py     # Builds prompts from historical data
│   ├── quote_generator.py     # Calls OpenAI API
│   └── __init__.py            # Makes it a Python package
│
├── data/                        # Sample data for testing
│   └── closet-world_catalog.json  # Product catalog
│
├── tests/                       # Tests (future)
│
├── requirements.txt             # Python dependencies
├── .env                        # Local secrets (NOT committed to git)
├── .env.example               # Template for .env
├── .gitignore                 # Files to ignore in git
├── host.json                  # Azure Functions config
├── local.settings.json        # Local development settings
├── test_local.py             # Simple test script
└── README.md                 # Quick reference
```

---

## 🧪 Development Workflow

### Daily Workflow:
```bash
# 1. Open terminal, navigate to project
cd ~/Documents/projects/speedupsharepoint-ai-service-starter

# 2. Activate virtual environment
source .venv/bin/activate

# 3. Run local tests
python test_local.py

# 4. Start function for API testing
func start

# 5. Make changes, test, repeat
# 6. When ready, deploy to Azure
func azure functionapp publish speedupsharepoint-ai-service-michael
```

### When You Open a New Terminal:
```bash
cd ~/Documents/projects/speedupsharepoint-ai-service-starter
source .venv/bin/activate  # Don't forget this!
```

---

## 🐛 Troubleshooting

### Error: "ModuleNotFoundError: No module named 'openai'"
**Fix:** You forgot to activate the virtual environment
```bash
source .venv/bin/activate
```

### Error: "openai.AuthenticationError: Invalid API key"
**Fix:** Check your .env file has the correct API key
```bash
cat .env  # Should show OPENAI_API_KEY=sk-proj-...
```

### Error: "az: command not found"
**Fix:** Azure CLI not installed
```bash
brew install azure-cli
```

### Error: "func: command not found"
**Fix:** Azure Functions Core Tools not installed
```bash
brew tap azure/functions
brew install azure-functions-core-tools@4
```

### Function returns "AI returned invalid JSON"
**Fix:** GPT-4 sometimes returns markdown-wrapped JSON. Check logs:
```bash
# In the terminal running `func start`, you'll see the raw response
# Look for lines like: "Raw AI response: ```json..."
```

---

## 💰 Cost Breakdown

### Development (Local):
- **Cost:** $0 (using your OpenAI account)
- **Per Quote:** ~$0.03 (GPT-4 Turbo pricing)

### Production (Azure):
- **Function App (Consumption):** $0/month + $0.20 per 1M executions
- **Storage Account:** ~$2/month
- **OpenAI API:** $0.03 per quote
- **Total at 1,000 quotes/month:** ~$32/month

### At Scale:
- **10,000 quotes/month:** ~$302/month
- **100,000 quotes/month:** ~$3,020/month

Fine-tuning will reduce this by 60% (Week 4+).

---

## 🎯 Next Steps

### Week 1: Get Basic AI Working ✅ (You are here!)
- [x] Set up local environment
- [x] Test with sample catalog
- [x] Deploy to Azure
- [ ] Test with real customer requests

### Week 2: Add Real Data
- [ ] Connect to Azure SQL Database
- [ ] Fetch catalog from database
- [ ] Add Redis caching
- [ ] Load 100 historical quotes

### Week 3: Add Vector Search
- [ ] Set up Pinecone or Azure AI Search
- [ ] Embed historical quotes
- [ ] Implement similarity search
- [ ] Test: "Find 50 similar quotes"

### Week 4: Fine-Tune Model
- [ ] Prepare 2,000+ training examples
- [ ] Fine-tune GPT-4 on your data
- [ ] A/B test vs baseline
- [ ] Measure: cost, speed, accuracy

---

## 📞 Getting Help

### OpenAI Issues:
- Dashboard: https://platform.openai.com/
- Docs: https://platform.openai.com/docs/

### Azure Issues:
- Portal: https://portal.azure.com/
- Docs: https://learn.microsoft.com/azure/azure-functions/

### Python Issues:
- Official Docs: https://docs.python.org/3.11/
- Pydantic: https://docs.pydantic.dev/

---

## ✅ Success Checklist

You're ready to show Nick when:
- [ ] `python test_local.py` generates a reasonable quote
- [ ] `func start` runs without errors
- [ ] Can call the local endpoint with curl
- [ ] Deployed to Azure successfully
- [ ] Can call the Azure endpoint with curl
- [ ] Quote generates in under 5 seconds
- [ ] Total cost per quote is under $0.05

---

Good luck! 🚀

**Pro Tip:** Keep a log of interesting quotes the AI generates. You'll use these for fine-tuning and as demo material for investors.

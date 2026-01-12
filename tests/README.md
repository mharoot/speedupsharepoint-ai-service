# Test End to End
This is a clean, production‑ready, end‑to‑end test script that exercises all four AI endpoints in one run. It’s designed to:

- Run locally or against Azure

- Validate response shapes

- Pretty‑print results

- Fail loudly if any endpoint breaks

- Keep the flow simple enough for onboarding new engineers



## 🧪 How to Run It
```sh
chmod +x test_end_to_end.py
python test_end_to_end.py
```


If your Azure Function requires a key:
```python
BASE_URL = "https://speedupsharepoint-ai-service-michael.azurewebsites.net/api"
FUNCTION_KEY = "your-key-here"
HEADERS = {
    "Content-Type": "application/json",
    "x-functions-key": FUNCTION_KEY
}
```


## 🧠 What This Script Gives You
- A single command to validate your entire AI pipeline

- Confidence that your models, context builder, QuoteGenerator, and function_app.py are wired correctly

- A clean output you can paste into Slack or Notion

- A foundation for future automated integration tests


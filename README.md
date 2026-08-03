# AI GitHub Engineering Assistant

AI GitHub Engineering Assistant is a FastAPI service that builds a consistent,
structured review package from GitHub pull requests and supports deterministic
and provider-based code review workflows.

## Local development

1. Create and activate a Python virtual environment.
2. Install dependencies:

   ```bash
   pip install -r requirements.txt
   ```

3. Copy `.env.example` to `.env` and set only the credentials needed for the
   feature being exercised.
4. Start the service:

   ```bash
   python -m uvicorn app.main:app --reload
   ```

5. Check `GET http://127.0.0.1:8000/health`.

## Current Development Status

Completed:

- GitHub pull request metadata and changed-file retrieval
- Deterministic review rules
- Project and code context construction
- Base SHA and Head SHA version consistency, including fork pull requests
- ReviewPolicy
- Prompt Builder
- Prompt injection boundaries
- Prompt character budgets and truncation records
- Mock AI Provider
- Async OpenAI Provider
- Responses API Structured Outputs
- Mocked automated tests

Current limitation:

Real OpenAI API end-to-end validation has not yet been performed because API
billing/account access is not currently available.

The paid-provider endpoint remains explicit:

```text
POST /github/repos/{owner}/{repo}/pulls/{pull_number}/ai-review/openai
```

The default Mock review path remains unchanged and does not automatically call
the paid provider:

```text
GET /github/repos/{owner}/{repo}/pulls/{pull_number}/ai-review
```

### Resume real API validation

After API access is available:

1. Configure `OPENAI_API_KEY` and `OPENAI_REVIEW_MODEL`.
2. Create a small controlled pull request containing known review issues.
3. Call the real OpenAI review endpoint.
4. Verify finding accuracy, file paths, line locations, false positives, and omissions.
5. Decide whether to improve Prompt policy, context coverage, or related-file discovery.

The model ID must be one that is actually available to the configured OpenAI
account. Calling the real endpoint can incur API charges. The following commands
are examples only and are not run as part of automated tests:

```powershell
$env:OPENAI_API_KEY="your-api-key"
$env:OPENAI_REVIEW_MODEL="your-available-model-id"
$env:OPENAI_TIMEOUT_SECONDS="60"
$env:OPENAI_MAX_OUTPUT_TOKENS="3000"

python -m uvicorn app.main:app --reload

Invoke-RestMethod `
  -Method Post `
  -Uri "http://127.0.0.1:8000/github/repos/{owner}/{repo}/pulls/{pull_number}/ai-review/openai"
```

Do not commit `.env` or real API credentials.

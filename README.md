# Gmail Reaper - Composio SDK Example

AI-powered Gmail automation using [Composio SDK](https://composio.dev). Automatically label emails based on custom prompts.

## <“ What You'll Learn

- Authenticate and use Gmail tools via Composio SDK
- Implement OAuth flows with connection tracking
- Build AI agents that interact with authenticated APIs
- Set up real-time triggers for email processing

## =€ Quick Start

### Prerequisites
- Python 3.13+ with [uv](https://github.com/astral-sh/uv)
- Node.js 18+ with pnpm
- [Composio](https://app.composio.dev) API key
- [Supabase](https://supabase.com) project
- [ngrok](https://ngrok.com) for webhooks

### 1. Clone & Setup Database

```bash
git clone https://github.com/composiohq/demos
cd demos/gmail-labeller

# Create Supabase project and run migrations from:
# supabase/migrations/20250126220821_create_tables.sql
```

### 2. Backend Setup

```bash
cd apps/backend
uv sync

# Create .env
COMPOSIO_API_KEY=your-key
SUPABASE_URL=https://your-project.supabase.co
SUPABASE_SERVICE_KEY=your-service-key
GMAIL_AUTH_CONFIG_ID=your-gmail-config
ANTHROPIC_API_KEY=your-llm-key

# Run server
uvicorn main:app --reload
```

### 3. Frontend Setup

```bash
cd apps/frontend
pnpm install

# Create .env.local
NEXT_PUBLIC_API_URL=http://localhost:8000
NEXT_PUBLIC_SUPABASE_URL=https://your-project.supabase.co
NEXT_PUBLIC_SUPABASE_ANON_KEY=your-anon-key
NEXT_PUBLIC_ENABLE_CONNECTION_MODAL=true

# Run app
pnpm dev
```

### 4. Enable Webhooks

```bash
# Expose local backend for Gmail webhooks
ngrok http 8000

# Use the ngrok URL in your Composio webhook configuration
```

## =Ú Key Concepts

### Gmail Tool Usage
```python
# Get authenticated Gmail tools
tools = composio.tools.get(user_id, tools=[
    "GMAIL_ADD_LABEL_TO_EMAIL",
    "GMAIL_CREATE_LABEL"
])

# Create AI agent
agent = Agent(name="Gmail Reaper", tools=tools)
await Runner.run(agent, email_content)
```

### Connection Flow
```typescript
// Status values: INITIATED ’ ACTIVE ’ FAILED/EXPIRED/REVOKED
const status = await checkConnectionStatus(connectionId)
```

### Trigger Setup
```python
composio.triggers.create(
    user_id=user_id,
    slug="GMAIL_NEW_GMAIL_MESSAGE",
    trigger_config={"interval": 1, "labelids": "INBOX"}
)
```

## <× Architecture

```
Next.js Frontend ’ FastAPI Backend ’ Composio SDK ’ Gmail API
                         “
                    Supabase DB
```

## =Ý License

MIT - Use freely in your projects!

---

Built by [Composio](https://composio.dev) to demonstrate AI tool integration.
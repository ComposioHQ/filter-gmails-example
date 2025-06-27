# Gmail Reaper - Composio SDK Example

AI-powered Gmail automation using [Composio SDK](https://composio.dev). Automatically label emails based on custom prompts.

## Tech Stack

- **Frontend**: Next.js 15, React 19, TypeScript, Tailwind CSS
- **Backend**: Python/FastAPI, OpenAI Agents SDK
- **Database**: Supabase (PostgreSQL with RLS)
- **AI Integration**: Composio SDK for Gmail tools

## What You'll Learn

- Authenticate and use Gmail tools via Composio SDK
- Implement OAuth flows with connection tracking
- Build AI agents that interact with authenticated APIs
- Set up real-time triggers for email processing

## Prerequisites

1. **System Requirements**
   - Python 3.13+ with [uv](https://github.com/astral-sh/uv) package manager
   - Node.js 18+ with pnpm
   - [ngrok](https://ngrok.com) for local webhook testing

2. **API Keys & Accounts**
   - **Composio API Key**: Get it from [app.composio.dev/developers](https://app.composio.dev/developers)
   - **Supabase Project**: Create at [supabase.com](https://supabase.com)
   - **Anthropic API Key**: For Claude models (or use OpenAI/other LLMs)

## Environment Variables

### Backend (.env)
```bash
COMPOSIO_API_KEY=          # From app.composio.dev/developers
SUPABASE_URL=              # Your Supabase project URL
SUPABASE_SERVICE_KEY=      # Service role key (not anon key!)
GMAIL_AUTH_CONFIG_ID=      # From Composio Gmail integration
ANTHROPIC_API_KEY=         # Your LLM provider key
```

### Frontend (.env.local)
```bash
NEXT_PUBLIC_API_URL=http://localhost:8000
NEXT_PUBLIC_SUPABASE_URL=  # Same as backend SUPABASE_URL
NEXT_PUBLIC_SUPABASE_ANON_KEY=  # Anon key (not service key!)
NEXT_PUBLIC_ENABLE_CONNECTION_MODAL=true
```

## Quick Start

### 1. Clone & Setup Database

```bash
git clone https://github.com/composiohq/demos
cd demos/gmail-labeller
```

Set up your Supabase database by following the instructions in [apps/SUPABASE_SETUP.md](apps/SUPABASE_SETUP.md)

### 2. Get Your API Keys

1. **Composio API Key**
   - Go to [app.composio.dev/developers](https://app.composio.dev/developers)
   - Create new API key
   - Set up Gmail integration in Composio dashboard

2. **Supabase Keys**
   - Create project at [supabase.com](https://supabase.com)
   - Get both `anon` key (frontend) and `service_role` key (backend)
   - Note your project URL

### 3. Backend Setup

```bash
cd apps/backend
uv sync

# Create .env with your keys
cp .env.example .env
# Edit .env with your actual keys

# Run server
uvicorn main:app --reload
```

### 4. Frontend Setup

```bash
cd apps/frontend
pnpm install

# Create .env.local with your keys
cp .env.example .env.local
# Edit .env.local with your actual keys

# Run app
pnpm dev
```

### 5. Enable Webhooks

```bash
# Expose local backend for Gmail webhooks
ngrok http 8000

# Use the ngrok URL in your Composio webhook configuration
```

## Key Concepts

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
// Status values: INITIATED -> ACTIVE -> FAILED/EXPIRED/REVOKED
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

## Architecture

```
Next.js Frontend -> FastAPI Backend -> Composio SDK -> Gmail API
                         |
                    Supabase DB
```

## License

MIT - Use freely in your projects\!

---

Built by [Composio](https://composio.dev) to demonstrate AI tool integration.

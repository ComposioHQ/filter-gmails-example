# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

This is Gmail Reaper - an AI-powered Gmail labelling application using Composio SDK. It's structured as a monorepo with a Python/FastAPI backend and Next.js/TypeScript frontend. Users can create custom prompts to train an AI agent to automatically categorize their Gmail inbox.

## Commands

### Backend (Python/FastAPI)

```bash
cd apps/backend
uv sync                    # Install dependencies (requires SSH access to composiohq/py-sdk-v3)
# No run command defined yet - FastAPI server implementation pending
```

### Frontend (Next.js)

```bash
cd apps/frontend
pnpm install              # Install dependencies
pnpm dev                  # Start development server with Turbopack at http://localhost:3000
pnpm build                # Build for production
pnpm start                # Start production server
pnpm lint                 # Run Next.js ESLint
pnpm gen:types            # Generate TypeScript types from Supabase schema
```

## Architecture

### Monorepo Structure

- `/apps/backend/` - Python 3.13+ FastAPI backend (uses uv package manager)

  - Depends on private Composio SDK from GitHub
  - Currently only contains hello.py placeholder

- `/apps/frontend/` - Next.js 15.3.3 + React 19 + TypeScript frontend (uses pnpm)
  - Uses Next.js App Router with Turbopack for fast development
  - Implements authentication flow with Supabase OAuth
  - Tailwind CSS 4 for styling with tw-animate-css for animations
  - Component architecture using shadcn/ui primitives

### Frontend Architecture

- **Authentication**: Supabase client configured in `/src/lib/supabase/` with SSR support and TypeScript types
- **Routing**: Next.js App Router in `/src/app/` with:
  - `/` - Main dashboard (authenticated) with prompt editor
  - `/auth/` - Authentication routes (login, callback)
- **Components**:
  - `/src/components/ui/` - Reusable UI components (Button, Card, Input, Textarea, etc.)
  - `/src/components/login-form.tsx` - OAuth login implementation
  - `/src/components/prompt-editor.tsx` - Main prompt management component
- **Middleware**: Authentication middleware redirects unauthenticated users to `/auth/login`
- **Path Aliases**: `@/` configured for `/src/` directory
- **Database**:
  - TypeScript types generated from Supabase schema in `/src/lib/supabase/database.types.ts`
  - Prompts table storing user AI prompts

### Key Dependencies

- Backend: `composio` (private SDK), `fastapi[standard]>=0.115.12`
- Frontend:
  - Core: `next@15.3.3`, `react@^19.0.0`, `typescript@^5`
  - Auth: `@supabase/supabase-js@^2.50.0`, `@supabase/ssr@^0.6.1`
  - Styling: `tailwindcss@^4`, `tw-animate-css@^1.3.4`
  - UI: `@radix-ui/react-slot`, `class-variance-authority`, `clsx`, `tailwind-merge`
  - Icons: `lucide-react@^0.515.0`

## Development Notes

1. The Composio backend dependency requires SSH access to `git@github.com:composiohq/py-sdk-v3`
2. No tests are configured in either backend or frontend
3. Frontend prompt management is implemented - backend Gmail integration pending
4. Frontend uses ESLint 9 with Next.js configuration
5. Supabase project ID: `eweoycxhqpmmihbujhdc`
6. Database schema includes `prompts` and `connections` tables - see `/apps/SUPABASE_SETUP.md` for schema
7. **IMPORTANT**: When making changes to database schema, always update `/apps/SUPABASE_SETUP.md` to keep documentation in sync

## Composio

You are building with Composio's Python SDK. Composio is platform for building with authenticated tools for AI agents and workflows.
It lets you build agents that that can work across a user's apps like Gmail, Notion, Slack.

Below is a list of Composio documentation. Use your web and fetch capabilities to read the documentation you need.
[Composio Documentation](https://v3.docs.composio.dev)

- [Quickstart](https://v3.docs.composio.dev/docs/quickstart.mdx): Add authenticated tool-calling to any LLM agent in three steps.
- [Configuration](https://v3.docs.composio.dev/docs/configuration.mdx)
- [Providers](https://v3.docs.composio.dev/docs/toolsets.mdx)
- [Executing Tools](https://v3.docs.composio.dev/docs/executing-tools.mdx): Learn how to execute Composio's tools with different providers and frameworks
- [Authenticating Tools](https://v3.docs.composio.dev/docs/authenticating-tools.mdx): Learn how to authenticate tools
- [Fetching and Filtering Tools](https://v3.docs.composio.dev/docs/fetching-tools.mdx): Learn how to fetch and filter Composio's tools and toolsets
- [Schema Modifiers](https://v3.docs.composio.dev/docs/modifiers/schema-modifiers.mdx): Learn how to use schema modifiers to transform tool schemas before they are seen by agents.
- [Before Execution Modifiers](https://v3.docs.composio.dev/docs/modifiers/before-execution.mdx): Learn how to use before execution modifiers to modify tool arguments before execution.
- [After Execution Modifiers](https://v3.docs.composio.dev/docs/modifiers/after-execution.mdx): Learn how to use after execution modifiers to transform tool results after execution.
- [Creating custom tools](https://v3.docs.composio.dev/docs/custom-tools.mdx): Learn how to extend Composio's toolkits with your own tools
- [Custom Auth Configs](https://v3.docs.composio.dev/docs/custom-auth-configs.mdx): Guide to using customising auth configs for a toolkit
- [Programmatic Auth Configs](https://v3.docs.composio.dev/docs/programmatic-auth-configs.mdx): Guide to creating auth configs programmatically
- [Custom Auth Parameters](https://v3.docs.composio.dev/docs/custom-auth-params.mdx): Guide to injecting custom credentials in headers or parameters for a toolkit
- [Using Triggers](https://v3.docs.composio.dev/docs/using-triggers.mdx): Send payloads to your system based on external events
- [OpenAI Providers](https://v3.docs.composio.dev/providers/openai.mdx)
- [Anthropic Provider](https://v3.docs.composio.dev/providers/anthropic.mdx)
- [LangGraph Provider](https://v3.docs.composio.dev/providers/langgraph.mdx)
- [CrewAI Provider](https://v3.docs.composio.dev/providers/crewai.mdx)
- [Vercel AI SDK Provider](https://v3.docs.composio.dev/providers/vercel.mdx)
- [Google ADK Provider](https://v3.docs.composio.dev/providers/google-adk.mdx)
- [OpenAI Agents Provider](https://v3.docs.composio.dev/providers/openai-agents.mdx)
- [Mastra Provider](https://v3.docs.composio.dev/providers/mastra.mdx)
- [Custom Providers](https://v3.docs.composio.dev/toolsets/custom.mdx)

## Memory Notes

- For FastAPI, use Context7 to get latest, up-to-date docs.
- `/fastapi/fastapi` is the Context7 Library ID name. Make sure to use Context7 for referring to FastAPI docs.
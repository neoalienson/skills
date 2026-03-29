---
name: opencode
description: "Use OpenCode as the primary coding agent. OpenCode is an open-source AI coding agent with specialized agent modes (plan/build), subagent system, MCP servers, and headless server capabilities. Use for: (1) planning and analysis, (2) building/implementing features, (3) code reviews, (4) long-running background tasks, (5) MCP server automation, (6) ACP protocol for IDE integration. Supports Kimi, Claude, GPT, Gemini, and 75+ providers. Requires bash tool with pty:true for interactive mode."
metadata:
  {
    "openclaw": {
      "emoji": "🦾",
      "requires": { "anyBins": ["opencode"] },
      "tags": ["coding", "agent", "automation", "planning", "execution", "mcp", "acp"]
    },
  }
---

# OpenCode Skill

**OpenCode** is an open-source AI coding agent designed for terminal, IDE, and headless automation use. It features a unique multi-agent architecture with specialized modes for planning vs execution, native MCP server support, and an ACP server for A2A communication.

## Why OpenCode?

- **Multi-agent system**: Separate \`plan\` (analysis) and \`build\` (execution) agents
- **Provider agnostic**: Works with Kimi, Claude, GPT, Gemini, and 75+ providers
- **MCP native**: Built-in MCP server support via \`opencode mcp\`
- **ACP native**: Built-in ACP server for A2A via \`opencode acp\`
- **Headless automation**: Server mode (\`serve\`) for programmatic access
- **Local first**: Privacy-focused, no code sent to external servers
- **Default model**: Pre-configured to use \`kimi-for-coding/k2p5\`

---

## ⚠️ PTY Mode Required

OpenCode requires a pseudo-terminal (PTY) for proper interaction. Without PTY, output breaks or the session hangs.

\`\`\`bash
# ✅ Correct - with PTY
bash pty:true command:"opencode run 'Your task'"

# ❌ Wrong - will break or hang
bash command:"opencode run 'Your task'"
\`\`\`

### Bash Parameters for OpenCode

| Parameter    | Type    | Description                                           |
| ------------ | ------- | ----------------------------------------------------- |
| \`command\`    | string  | The opencode command to run                            |
| \`pty\`        | boolean | **REQUIRED** for interactive TUI mode                 |
| \`workdir\`    | string  | Working directory (agent context)                      |
| \`background\` | boolean | Run in background, returns sessionId for monitoring   |
| \`timeout\`    | number  | Timeout in seconds (kills process on expiry)           |
| \`elevated\`   | boolean | Run on host instead of sandbox                         |

### Process Tool Actions (for background sessions)

| Action   | Description                                          |
| -------- | ---------------------------------------------------- |
| \`list\`   | List all running sessions                            |
| \`poll\`   | Check if session is still running                    |
| \`log\`    | Get session output (with optional offset/limit)      |
| \`write\`  | Send raw data to stdin                               |
| \`submit\` | Send data + newline (like typing and pressing Enter) |
| \`kill\`   | Terminate the session                               |


---

## Core Concepts: Agent Architecture

OpenCode has **Primary Agents** and **Subagents**:

### Primary Agents (switch with Tab or \`--prompt\`)

| Agent  | Mode     | Tools                       | Use Case                              |
| ------ | -------- | --------------------------- | -------------------------------------- |
| \`build\` | primary  | ALL (write, edit, bash)     | **Default** - implementation & changes |
| \`plan\`  | primary  | READ-ONLY                   | Analysis and planning (no changes)     |

**Switch agents:**
\`\`\`bash
# Plan mode (analysis only)
bash pty:true command:"opencode run --prompt plan 'Analyze this codebase'"

# Build mode (makes changes) - default
bash pty:true command:"opencode run --prompt build 'Implement the feature'"
\`\`\`

### Subagents (invoke with @mention)

| Agent         | Mode     | Purpose                             |
| ------------- | -------- | ----------------------------------- |
| \`@explore\`    | subagent | Fast codebase exploration (read-only) |
| \`@general\`    | subagent | Research and multi-step tasks       |
| \`@compaction\` | system   | Context compaction (auto-invoked)  |

---

## MCP (Model Context Protocol)

OpenCode has native MCP server support. MCP lets OpenCode connect to external tools and data sources.

### Manage MCP Servers

\`\`\`bash
# List available MCP servers
opencode mcp list

# Add an MCP server
opencode mcp add <server-name> <command> [args...]

# Remove an MCP server
opencode mcp remove <server-name>

# Start an MCP server and use it in a session
bash pty:true command:"opencode run 'Use the filesystem MCP to list all files in /project'"
\`\`\`

### Common MCP Configurations

\`\`\`bash
# Filesystem MCP
opencode mcp add filesystem npx -y @modelcontextprotocol/server-filesystem /path/to/directory

# GitHub MCP
opencode mcp add git npx -y @modelcontextprotocol/server-github --token \$GITHUB_TOKEN

# Brave Search MCP
opencode mcp add search npx -y @modelcontextprotocol/server-brave-search --api-key \$BRAVE_API_KEY
\`\`\`

### Using MCP in OpenCode Sessions

Once an MCP server is configured, it is available in all OpenCode sessions. Just refer to it in your prompt:

\`\`\`bash
bash pty:true command:"opencode run 'Search the web using MCP to find the latest OpenCode release notes'"
\`\`\`

---

## ACP (Agent Client Protocol) — A2A Communication

ACP enables OpenCode to act as an A2A agent — exposed as a server that other agents or tools can communicate with programmatically.

### Start ACP Server

\`\`\`bash
# Start ACP server (background)
bash pty:true background:true command:"opencode acp"

# ACP server on custom port/host
bash pty:true background:true command:"opencode acp --port 8080 --hostname 0.0.0.0"
\`\`\`

### ACP Session Interaction

\`\`\`bash
# Create a new session
curl -X POST http://localhost:8080/api/session   -H 'Content-Type: application/json'   -d '{"title": "My task"}'

# Send a prompt to a session
curl -X POST http://localhost:8080/api/session/{sessionId}/prompt   -H 'Content-Type: application/json'   -d '{"parts": [{"type": "text", "text": "Implement auth"}]}'

# List sessions
curl http://localhost:8080/api/sessions

# Get session status
curl http://localhost:8080/api/session/{sessionId}
\`\`\`

### SDK Usage (JavaScript/TypeScript)

\`\`\`javascript
import { createOpencodeClient } from "@opencode-ai/sdk"

const client = createOpencodeClient({ baseUrl: "http://localhost:8080" })

// Create session
const session = await client.session.create({ body: { title: "My task" }})

// Send prompt
const result = await client.session.prompt({
  path: { id: session.id },
  body: { parts: [{ type: "text", text: "Implement auth" }] }
})

console.log(result)
\`\`\`

### Editor Integration (Zed, JetBrains, Neovim)

ACP is compatible with:
- **Zed** — via CodeCompanion or native ACP client
- **JetBrains IDEs** — via ACP plugin
- **Neovim** — via Avante or CodeCompanion

\`\`\`bash
# Start ACP server for IDE integration
bash pty:true background:true command:"opencode acp"
\`\`\`

---

## Serve Mode (Headless Server)

For programmatic integration without ACP:

\`\`\`bash
# Start headless server
bash pty:true background:true command:"opencode serve --port 8080 --hostname 127.0.0.1"

# Interact via curl
curl -X POST http://localhost:8080/api/session   -H 'Content-Type: application/json'   -d '{"message":"Hello"}'
\`\`\`


---

## Configuration

OpenCode is pre-configured in \`~/.config/opencode/opencode.json\`:

\`\`\`json
{
  "\$schema": "https://opencode.ai/config.json",
  "model": "kimi-for-coding/k2p5"
}
\`\`\`

**Override per command:**
\`\`\`bash
bash pty:true command:"opencode run -m kimi-for-coding/kimi-k2-thinking 'Complex task'"
\`\`\`

### Project Configuration

Create \`.opencode/opencode.json\` in your project:

\`\`\`json
{
  "\$schema": "https://opencode.ai/config.json",
  "model": "kimi-for-coding/k2p5",
  "agent": {
    "build": {
      "temperature": 0.1,
      "permission": {
        "edit": "allow",
        "bash": "ask"
      }
    }
  }
}
\`\`\`

Initialize project analysis:
\`\`\`bash
# Creates AGENTS.md with project context
bash pty:true workdir:~/project command:"opencode run '/init'"
\`\`\`

---

## Usage Patterns

### Pattern 1: Planning → Execution (Recommended)

\`\`\`bash
# Step 1: Planning (read-only)
bash pty:true workdir:~/project background:true command:"opencode run --prompt plan 'Design a user authentication system with JWT tokens'"
# Returns sessionId: PLAN_SESSION

# Monitor plan
process action:log sessionId:PLAN_SESSION

# Step 2: Execution (with the plan)
bash pty:true workdir:~/project background:true command:"opencode run --prompt build 'Implement the authentication system based on the plan'"
\`\`\`

### Pattern 2: One-Shot Tasks

\`\`\`bash
# Direct execution with default build agent
bash pty:true workdir:~/project command:"opencode run 'Add error handling to the API routes'"

# With specific model
bash pty:true workdir:~/project command:"opencode run -m kimi-for-coding/k2p5 'Refactor the auth module'"
\`\`\`

### Pattern 3: Background Long-Running Tasks

\`\`\`bash
# Start in background with PTY
bash pty:true workdir:~/project background:true command:"opencode run --prompt build 'Refactor the entire codebase to TypeScript'"
# Returns: sessionId

# Check progress
process action:log sessionId:XXX offset:0 limit:50

# Check if still running
process action:poll sessionId:XXX

# Kill if needed
process action:kill sessionId:XXX
\`\`\`

### Pattern 4: Code Review

\`\`\`bash
# Review PR in temp directory (never in live project!)
REVIEW_DIR=\$(mktemp -d)
git clone https://github.com/user/repo.git \$REVIEW_DIR
cd \$REVIEW_DIR && gh pr checkout 123

bash pty:true workdir:\$REVIEW_DIR command:"opencode run --prompt plan 'Review this PR for bugs, security issues, and best practices'"

# Cleanup
bash command:"rm -rf \$REVIEW_DIR"
\`\`\`


---

## Lead Dev → Coding Agent Integration

### 1. Lead Dev Planning Phase

\`\`\`bash
# Lead dev spawns OpenCode in plan mode for analysis
bash pty:true workdir:~/project background:true command:"opencode run --prompt plan 'Analyze requirements and create implementation plan for [FEATURE]'"
# Returns: PLAN_SESSION

# Lead dev monitors and extracts plan
process action:log sessionId:PLAN_SESSION

# Lead dev updates project management with plan
\`\`\`

### 2. Coding Agent Execution Phase

\`\`\`bash
# Coding agent receives plan from Lead Dev
bash pty:true workdir:~/project background:true command:"opencode run --prompt build 'Implement [FEATURE] according to the approved plan. Plan: [PASTE_PLAN_HERE]'"
# Returns: BUILD_SESSION

# Monitor implementation
process action:log sessionId:BUILD_SESSION

# Report completion to Lead Dev
\`\`\`

### 3. Parallel Execution (Multiple Features)

\`\`\`bash
# Multiple coding agents working in parallel
bash pty:true workdir:/tmp/feature-a background:true command:"opencode run --prompt build 'Implement feature A'"
bash pty:true workdir:/tmp/feature-b background:true command:"opencode run --prompt build 'Implement feature B'"

# Monitor all
process action:list
\`\`\`

---

## Commands Reference

### Core Commands

| Command              | Purpose                                   |
| -------------------- | ----------------------------------------- |
| \`opencode\`           | Start TUI (interactive)                  |
| \`opencode run [msg]\` | Execute single command                    |
| \`opencode serve\`     | Start headless server                    |
| \`opencode acp\`       | Start ACP server for A2A/IDE integration |
| \`opencode mcp\`       | Manage MCP servers                       |
| \`opencode models\`    | List available models                     |
| \`opencode agent list\` | List configured agents                   |

### Flags

| Flag      | Description                              |
| --------- | ---------------------------------------- |
| \`-m\`      | Specify model (provider/model format)    |
| \`-c\`      | Continue last session                    |
| \`-s\`      | Continue specific session                |
| \`--fork\`  | Fork session when continuing             |
| \`--prompt\` | Specify agent to use (plan/build)        |

---

## Progress Updates & Notifications

Always keep Lead Dev informed when running background tasks:

\`\`\`bash
# Start task
bash pty:true workdir:~/project background:true command:"opencode run --prompt build 'Build feature X'"

# Periodically check and report
process action:poll sessionId:XXX
process action:log sessionId:XXX
\`\`\`

### Auto-Notify on Completion

Append wake trigger to prompt for immediate notification:

\`\`\`bash
bash pty:true workdir:~/project background:true command:"opencode run --prompt build 'Implement user authentication.

When completely finished, notify with:
openclaw system event --text "Done: Implemented JWT auth with login/logout endpoints" --mode now'"
\`\`\`

---

## Important Rules

1. **✅ Always use \`pty:true\`** - OpenCode needs terminal for proper output
2. **✅ Plan before building** - Use \`--prompt plan\` for analysis, \`--prompt build\` for changes
3. **✅ Use workdir** - Set proper context to prevent wandering
4. **✅ Monitor background tasks** - Check logs with \`process action:log\`
5. **✅ Clean up temp dirs** - After PR reviews or experiments
6. **❌ Never run in ~/.openclaw/** - OpenCode will read soul docs and get confused
7. **❌ Don't kill sessions early** - Be patient with long tasks
8. **❌ Don't mix modes mid-task** - Plan first, then build, don't switch arbitrarily

---

## Troubleshooting

### Session Hangs
\`\`\`bash
# Check if running
process action:poll sessionId:XXX

# View recent output
process action:log sessionId:XXX offset:-20

# Kill if stuck
process action:kill sessionId:XXX
\`\`\`

### Permission Denied
OpenCode may ask for permission on file edits. Use project config to pre-approve:
\`\`\`json
{
  "permission": {
    "edit": "allow",
    "bash": "ask"
  }
}
\`\`\`

### Model Not Available
\`\`\`bash
# List available models
bash command:"opencode models | grep kimi"

# Check current config
bash command:"cat ~/.config/opencode/opencode.json"
\`\`\`

---

**Version**: 1.0.0
**Last Updated**: 2026-03-29
**Compatible OpenCode**: >=1.0.0

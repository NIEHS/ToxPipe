# Using ToxPipe models with Claude Code

ToxPipe's Anthropic models are compatible with the Claude Code desktop and command line applications.

_(The following guide was written by Jennifer Serafini and edited for formatting by Parker Combs)_

# Setting Up Claude Code via ToxPipe LiteLLM Proxy 
Documented by Jennifer Serafini, April 2026 For use by other NIEHS/AFDS developers on Windows GFE 

_A note on authorship: This document was developed collaboratively with Claude (Anthropic), an AI assistant, which assisted with drafting, structure, and technical documentation. All decisions, testing, and validation reflect the judgment and domain expertise of the author. The author takes full responsibility for the content of this document._

## Overview 
This document covers two installation methods: 
****Method A****: Native (recommended) - requires Node.js installed by IT 
****Method B****: Docker - use if Node.js is not available 

Both methods connect Claude Code to the ToxPipe LiteLLM proxy instead of directly to Anthropic’s API. 

## Prerequisites 
- ToxPipe API key 
- NIH CA Bundle PEM file (certs/NIH_CA_Bundle.pem) - for Docker method 
- Node.js installed (Method A) or Docker Desktop 27.0.3+ (Method B) 

## Step 1: Verify the /v1/messages Endpoint is Working 
PowerShell encodes strings with a BOM by default which breaks JSON parsing. Write the body to a file first: 
1a. Write request body to file: 
```
'{"model":"claude-4.6-sonnet","max_tokens":100,"messages":[{"role":"user","content":"hello"}]}' | Out-File -FilePath test_body.json -Encoding ascii -NoNewline
``` 

1b. Send the request: 
```
curl.exe -v -X POST "https://litellm.toxpipe.niehs.nih.gov/v1/messages" -H "x-api-key: your_key_here" -H "Content-Type: application/json" --cacert "certs/NIH_CA_Bundle.pem" -d "@test_body.json" 
```

Expected result: ```HTTP 200 with JSON response containing “role”:“assistant”```

Troubleshooting notes:
- Use curl.exe not curl - PowerShell aliases curl to Invoke-WebRequest
- SSL cert warning lines (did not match against certificate name) are normal
- Empty response with no error = BOM encoding issue, use the file approach above
- Content-Length: 2 in verbose output = same issue 

## Step 2: Check Available Models 
```
curl.exe -X GET "https://litellm.toxpipe.niehs.nih.gov/v1/models" -H "x-api-key: your_key_here" --cacert "certs/NIH_CA_Bundle.pem" 
```
Use the exact model string from this response in all requests. At time of writing: claude-4.6-sonnet 

## Method A: Native Installation (Recommended) 
Use this method if IT has installed Node.js on your GFE. No Docker required. 

### Step 3A: Confirm Node.js is installed 
Run from PyCharm terminal (not a standalone PowerShell window - execution policy may block npm outside PyCharm): 
```
node --version 
npm --version 
```
Both should return version numbers. 

### Step 4A: Install Claude Code 
Important: Pin to version 2.1.45. Newer versions have a known incompatibility with the ToxPipe LiteLLM proxy that causes every prompt to fail with ```API Error: Content block is not a text block.```
```
npm install -g @anthropic-ai/claude-code@2.1.45 
```

**Prevent auto-updates**: Claude Code may auto-update to a newer incompatible version. To prevent this, run once after installing: 
```
New-Item -ItemType Directory -Force "$env:USERPROFILE\.claude" 
'{"autoUpdate": false}' | Out-File -FilePath "$env:USERPROFILE\.claude\settings.json" -Encoding utf8 
```

### Step 5A: Set Environment Variables 
In Powershell (or compatible style, i.e., PyCharm) terminal: 
```
$env:ANTHROPIC_BASE_URL = "https://litellm.toxpipe.niehs.nih.gov" 
$env:ANTHROPIC_API_KEY = "your_key_here" 
$env:NODE_EXTRA_CA_CERTS = "C:\path\to\your\project\certs\NIH_CA_Bundle.pem" 
```
Replace the NODE_EXTRA_CA_CERTS path with the actual path to your NIH CA Bundle file. 

### Step 6A: Launch Claude Code 
```
claude --model claude-4.6-sonnet 
```

### Step 7A: Make Environment Variables Persistent 
To avoid setting environment variables every session, add them to your PyCharm run configuration or Windows user environment variables: 
1. Search “environment variables” in Windows Start 
2. Click “Edit environment variables for your account” 
3. Add each variable under User variables 
4. No admin rights required for user-level variables 

## Method B: Docker Installation 
Use this method if Node.js is not available on your GFE. 

### Step 3B: Add .env File to Project Root 
Create .env at project root. **Never commit this file**: 
```
ANTHROPIC_API_KEY=your_key_here 
```
Confirm .gitignore includes: 
```
.env 
config.json 
```

### Step 4B: Create Dockerfile.claudecode 
Create a file named Dockerfile.claudecode at your project root: 
```
FROM node:20-slim 
 
COPY certs/NIH_CA_Bundle.pem /usr/local/share/ca-certificates/NIH_CA_Bundle.crt 
RUN apt-get update && apt-get install -y --no-install-recommends ca-certificates \ 
    && update-ca-certificates \ 
    && rm -rf /var/lib/apt/lists/* 
 
RUN npm install -g @anthropic-ai/claude-code@2.1.45 
 
WORKDIR /app 
```
Notes:
- PEM format is what update-ca-certificates expects - renaming to .crt requires no conversion
- Version pinned to 2.1.45 - see Known Issues 

### Step 5B: Add claude_code Service to docker-compose.yml 
```
claude_code: 
  build: 
    context: . 
    dockerfile: Dockerfile.claudecode 
  image: genai-pipeline-claudecode:latest 
  volumes: 
    - "./:/app" 
  environment: 
    - ANTHROPIC_BASE_URL=https://litellm.toxpipe.niehs.nih.gov 
    - ANTHROPIC_API_KEY 
    - NODE_EXTRA_CA_CERTS=/usr/local/share/ca-certificates/NIH_CA_Bundle.crt 
  stdin_open: true 
  tty: true 
  command: claude --model claude-4.6-sonnet 
```
Notes:
- ```ANTHROPIC_BASE_URL``` does not include the path. Claude Code appends /v1/messages automatically
- ```ANTHROPIC_API_KEY``` with no value tells Compose to pull from .env
- ```NODE_EXTRA_CA_CERTS``` is the Node.js equivalent of curl’s ```–cacert``` flag
- ```stdin_open``` and ```tty``` make the container interactive
- ```ANTHROPIC_MODEL``` environment variable is not reliable - always use –model flag 

### Step 6B: Build the Image 
```
docker-compose build claude_code 
```
Expected build time: approximately 4 minutes. All steps should complete with no ERR! lines. 

### Step 7B: Launch Claude Code 
```
docker-compose run --rm claude_code 
```

# Session Management (Both Methods) 

## Method A - Resume after disconnect: 
```
claude --model claude-4.6-sonnet --continue 
claude --model claude-4.6-sonnet --resume 
```

## Method B - Resume after disconnect: 
```
docker-compose run --rm claude_code claude --model claude-4.6-sonnet --continue 
docker-compose run --rm claude_code claude --model claude-4.6-sonnet --resume 
```

**Important**: If a session crashes or ends unexpectedly, do not use ```--resume``` with the old session ID. This can carry corrupted state including remapped model names which causes the Invalid model name error. Start a fresh session instead. 

# First Launch Setup 
On first launch Claude Code will: 
1. Ask you to select a color theme - choose your preference 
2. Show a marketplace/plugins prompt - dismiss it, no plugins needed 
3. Prompt about a custom API key - select Yes - this is your ToxPipe key and is intentional 

# Useful Claude Code Commands 
- Exit Claude Code: ```/exit```
- Change color theme: ```/theme```
- Interrupt current operation: ```Ctrl+C```

# How It Works 
```
Your codebase 
      | 
      v 
Claude Code (native or container) 
      | 
      v 
ANTHROPIC_BASE_URL -> litellm.toxpipe.niehs.nih.gov/v1/messages 
      | 
      v 
LiteLLM proxy -> Anthropic Claude API 
      | 
      v 
Response back through proxy -> Claude Code 
```
All traffic routes through ToxPipe. No direct Anthropic API calls. 

# Known Issues 

| Issue | Symptom | Resolution 
| :--- | :---: | ---: |
| Claude Code version incompatibility | API Error: Content block is not a text block on every prompt | Pin to v2.1.45: ```npm install -g @anthropic-ai/claude-code@2.1.45```. Versions above 2.1.45 have a known incompatibility with ToxPipe LiteLLM proxy. 
| Claude Code auto-update | Reverts to incompatible version after install; Content block is not a text block returns after previously working | Disable auto-update - see Troubleshooting: My Version Keeps Auto-Updating below 
| Corrupted resume session | 400: Invalid model name passed in model=claude-sonnet-4-6 after using ```--resume``` | Do not use ```--resume``` with a session ID from a crashed session. Start a fresh session instead. 
| BOM encoding in PowerShell | Content-Length: 2 or empty response from curl | Use ```Out-File -Encoding ascii -NoNewline``` approach in Step 1 
| Wrong model name | Invalid model name passed in ```model=claude-sonnet-4-6``` | Always use ```--model``` flag at launch. Never rely on ```ANTHROPIC_MODEL``` env var. 
| ```npm``` blocked outside PyCharm | running scripts is disabled on this system | Run ```npm``` from PyCharm terminal only. PowerShell execution policy blocks it in standalone windows. 
| Docker - ```ANTHROPIC_MODEL``` ignored | Model name not passed correctly | Use ```--model``` flag in command, not environment variable 

# Troubleshooting: Which Version Am I Running? 
```
claude --version 
```
If above 2.1.45: 
```
npm install -g @anthropic-ai/claude-code@2.1.45 
```

# Troubleshooting: My Version Keeps Auto-Updating 

Claude Code has a built-in auto-updater that can override your pinned version. If you find it keeps updating past 2.1.45: 

## Step 1: Check your current version 
```
claude --version 
```

## Step 2: Reinstall the pinned version 
```
npm install -g @anthropic-ai/claude-code@2.1.45 
```

## Step 3: Disable auto-updates permanently 
```
New-Item -ItemType Directory -Force "$env:USERPROFILE\.claude" 
'{"autoUpdate": false}' | Out-File -FilePath "$env:USERPROFILE\.claude\settings.json" -Encoding utf8 
```

## Step 4: Verify the settings file was created 
```
Get-Content "$env:USERPROFILE\.claude\settings.json" 
```
Should return: 
```
{"autoUpdate": false} 
```

## Step 5: Launch and verify version again 
```
claude --version 
```
Should still show 2.1.45 after the next launch. 

_Tested on: Windows GFE, Node.js v24.14.1, npm 11.11.0, Claude Code v2.1.45, LiteLLM proxy, April 2026 _

_Docker tested on: Docker Desktop 27.0.3, Docker Compose v2.28.1 _

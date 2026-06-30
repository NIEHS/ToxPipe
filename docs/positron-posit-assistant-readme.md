# Using Positron with Posit Assistant via the ToxPipe API

[Positron](https://positron.posit.co/) is the next-generation data science IDE from Posit (the makers of RStudio), built for both R and Python. **Posit Assistant** is its built-in AI coding experience, with chat, inline assistance, and code completions that are aware of your interactive work — loaded data, plots, and console history.

This guide configures Posit Assistant to route through the ToxPipe LiteLLM proxy as a custom OpenAI-compatible provider, so you can use ToxPipe-provisioned models directly inside Positron.

> **Note: This works only in Positron, not in RStudio.** The classic RStudio IDE and RStudio Server do not support custom LLM providers — their AI assistant currently requires signing in through Posit's own AI login, with no option to point it at a custom OpenAI-compatible endpoint like the ToxPipe LiteLLM proxy. To use ToxPipe models with a Posit IDE, you must use Positron.

## Why use Posit Assistant with ToxPipe

- **Live data-science context** that terminal-based agents do not have: the assistant can reason about your loaded data frames, plots, and console history inside the IDE where you already work.
- **One IDE for R, Python, and AI** — no context switching between an editor and a separate chat tool.
- **All model traffic routes through the ToxPipe LiteLLM proxy**, keeping AI usage within NIEHS governance instead of calling a model vendor directly.
- **Access to ToxPipe-provisioned models** (e.g., Claude Opus 4.8, GPT 5.5) through a single API key and base URL.

## Prerequisites

- [Positron](https://positron.posit.co/download.html) installed
- A provisioned ToxPipe LiteLLM API key

## Step 1: Open `settings.json`

Open Positron's user settings in JSON form using one of these methods:

- Open the Command Palette with `Ctrl+Shift+P` (Windows/Linux) or `Cmd+Shift+P` (macOS), then run **Preferences: Open User Settings (JSON)**.
- Or open the Settings menu with `Ctrl+,` and click the **Open Settings (JSON)** icon in the top-right corner.

!["Open Settings (JSON)"](img/json-menu.png)

## Step 2: Add the configuration

Add the following configuration. If your `settings.json` already contains entries, merge these keys into the existing outermost curly braces `{}` rather than replacing the whole file.

```json
{
  "assistant.enabled": true,
  "assistant.sidebarView": true,

  "remote.autoForwardPortsSource": "hybrid",

  "positron.assistant.provider.customProvider.enable": true,

  "authentication.openai-compatible.baseUrl": "https://litellm.toxpipe.niehs.nih.gov/v1",

  "positron.assistant.models.overrides.customProvider": [
    {
      "name": "Claude Opus 4.8 (NIEHS)",
      "identifier": "azure-claude-opus-4.8"
    },
    {
      "name": "GPT 5.5 (NIEHS)",
      "identifier": "azure-gpt-5.5"
    }
  ],

  "files.associations": {
    "renv.lock": "json"
  }
}
```

Save your changes.

## Step 3: Configure the provider in the Posit Assistant sidebar

Open the Posit Assistant sidebar. You now have the option to configure LLM providers with a **Custom Provider**. Enter:

- **API key:** your provisioned ToxPipe LiteLLM API key
- **Base URL:** `https://litellm.toxpipe.niehs.nih.gov/v1`

## Step 4: Restart

Restart Positron, or run **Developer: Reload Window** from the Command Palette, to apply the configuration. The ToxPipe models should now be available in Posit Assistant.

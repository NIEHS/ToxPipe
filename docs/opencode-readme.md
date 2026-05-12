# Using ToxPipe with OpenCode

This guide is for setting up OpenCode on OSX (Mac) and Linux/Unix/etc. systems. [The Windows guide is here](https://github.com/NIEHS/ToxPipe/blob/Deployment/docs/opencode-esl2-r-readme.md).

This guide shows how to manually create an OpenCode config on a new installation without hard-coding a specific username.

It covers two setups:

- standard global config at `~/.config/opencode/opencode.json`
- fallback custom config using `OPENCODE_CONFIG` when `~/.config` is not writable

## Prerequisites

- OpenCode is already installed (OpenCode may be installed with [this guide](https://opencode.ai/docs#install))
- You know the provider settings you want to add
- You have the API key or token for that provider

This guide uses `~` for the current user's home directory. For example:

- macOS user `alice`: `~` means `/Users/alice`
- Linux user `alice`: `~` means `/home/alice`

## Recommended Layout

Use these paths:

- config file: `~/.config/opencode/opencode.json`
- optional TUI config: `~/.config/opencode/tui.json`
- secret file: `~/.secrets/<provider-key-name>`

Example secret path:

- `~/.secrets/niehs-litellm-key`

## Option 1: Standard Global Config

Use this when `~/.config` is writable.

### 1. Create the config and secret directories

```bash
mkdir -p ~/.config/opencode ~/.secrets
chmod 700 ~/.secrets
```

### 2. Save the API key in a secret file

Replace `<your-api-key>` with the real key.

```bash
printf '%s' '<your-api-key>' > ~/.secrets/niehs-litellm-key
chmod 600 ~/.secrets/niehs-litellm-key
```

### 3. Create `~/.config/opencode/opencode.json`

Use a config like this:

```json
{
  "$schema": "https://opencode.ai/config.json",
  "provider": {
    "niehs-litellm": {
      "name": "NIEHS LiteLLM",
      "npm": "@ai-sdk/openai-compatible",
      "options": {
        "baseURL": "https://litellm.toxpipe.niehs.nih.gov/v1",
        "apiKey": "{file:~/.secrets/niehs-litellm-key}",
        "timeout": 300000
      },
      "models": {
        "azure-gpt-5": {
          "name": "Azure GPT-5"
        },
        "azure-gpt-5.4": {
          "name": "Azure GPT-5.4"
        }
      }
    }
  }
}
```

### 4. Verify the config

```bash
opencode models
```

If the provider is configured correctly, the expected models should appear in the output.

## Option 2: Custom Config With `OPENCODE_CONFIG`

Use this when `~/.config` is not writable or when you want a config in a different location.

### 1. Create the secret directory

```bash
mkdir -p ~/.secrets
chmod 700 ~/.secrets
```

### 2. Save the API key in a secret file

Replace `<your-api-key>` with the real key.

```bash
printf '%s' '<your-api-key>' > ~/.secrets/niehs-litellm-key
chmod 600 ~/.secrets/niehs-litellm-key
```

### 3. Create a writable config file

One practical location is:

- `~/.opencode/opencode.json`

Create the directory if needed:

```bash
mkdir -p ~/.opencode
```

Create `~/.opencode/opencode.json` with the same JSON as in Option 1.

### 4. Run OpenCode with the custom config

```bash
OPENCODE_CONFIG="$HOME/.opencode/opencode.json" opencode models
```

### 5. Make `OPENCODE_CONFIG` persistent

Add it to your shell startup file.

For Fish:

```fish
set -x OPENCODE_CONFIG "$HOME/.opencode/opencode.json"
```

For Zsh:

```bash
export OPENCODE_CONFIG="$HOME/.opencode/opencode.json"
```

For Bash:

```bash
export OPENCODE_CONFIG="$HOME/.opencode/opencode.json"
```

Then restart the shell or reload the shell config.

## How OpenCode Chooses Config Files

OpenCode loads config from multiple locations. Common ones are:

1. `~/.config/opencode/opencode.json`
2. `OPENCODE_CONFIG`
3. `opencode.json` in the current project or a parent directory

Project config can override global config. If OpenCode behaves unexpectedly, check whether there is an `opencode.json` in the current directory tree.

## How To Check For A Project Config

From inside a project directory:

```bash
pwd
ls -la ./opencode.json
ls -la ../opencode.json
```

If a parent folder contains `opencode.json`, OpenCode may load it as the project config.

## Security Recommendations

- Do not store API keys directly in `opencode.json`
- Prefer `"{file:...}"` references for secrets
- Keep secret files under `~/.secrets`
- Use `chmod 600` on secret files
- Do not commit secret files to Git
- If you copied a config from somewhere else, remove old plaintext keys after migration

## Troubleshooting

### `~/.config` is not writable

Use Option 2 with `OPENCODE_CONFIG`.

### `opencode models` does not show the expected provider

Check:

- the JSON is valid
- the secret file exists
- the secret path in `"{file:...}"` is correct
- the provider `npm` entry is correct
- a project-level `opencode.json` is not overriding your config

### The shell does not see `OPENCODE_CONFIG`

Check it with:

```bash
printenv OPENCODE_CONFIG
```

If it is empty, add it to the correct shell startup file and restart the shell.

## Minimal Example For Another Provider

This pattern also works for other providers.

```json
{
  "$schema": "https://opencode.ai/config.json",
  "provider": {
    "my-provider": {
      "options": {
        "apiKey": "{file:~/.secrets/my-provider-key}"
      },
      "models": {
        "my-model": {
          "name": "My Model"
        }
      }
    }
  },
  "model": "my-provider/my-model"
}
```

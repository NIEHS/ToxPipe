# Setting Up ChemLint to Work With OpenCode and ToxPipe

**ChemLint** is a powerful suite of MCP tools that allow a user to perform chemical processing, analysis, modeling, visualization, reporting, and more. ChemLint's code repository may be accessed here: [https://github.com/molML/ChemLint](https://github.com/molML/ChemLint).

This guide will walk you through how to use ChemLint alongside OpenCode with ToxPipe models to create an end-to-end chemical analysis pipeline.

## Install OpenCode
Follow the [official OpenCode documentation](https://opencode.ai/) to install OpenCode on your system.

## Add ToxPipe models to OpenCode
Follow [our guide here](https://github.com/NIEHS/ToxPipe/blob/Deployment/docs/opencode-readme.md) for setting up OpenCode to use ToxPipe's AI models.

## Install ChemLint
ChemLint may be installed locally using the instructions [in the `README.md` of the repository](https://github.com/molML/ChemLint). Refer to the "manual" installation instructions, which state to run the following:
```
# 1. Clone and install dependencies
git clone https://github.com/derekvantilborg/ChemLint.git
cd ChemLint
uv sync

# 2. Run tests to verify installation
uv run pytest -m server -q
```

## Add ChemLint MCP to OpenCode
Finally, you will need to add the MCP config to OpenCode. You can simply just ask your model in OpenCode to append the below specifications to its list of MCP servers. Alternatively, you can append the specifications yourself to your `opencode.json` configuration file:
```
"chemlint": {
  "type": "local",
  "command": [
    "uv",
    "run",
    "--with",
    "mcp[cli]",
    "--directory",
    "/path/to/your/local/ChemLint", # CHANGEME, use absolute path
    "mcp",
    "run",
    "./src/chemlint/server.py"
  ],
  "enabled": true
}
```

When this step is done, your `opencode.json` file should look like the following:

```
{
  "$schema": "https://opencode.ai/config.json",
  "mcp": {
    "chemlint": {
      "type": "local",
      "command": [
        "uv",
        "run",
        "--with",
        "mcp[cli]",
        "--directory",
        "/path/to/your/local/ChemLint", # CHANGEME, use absolute path
        "mcp",
        "run",
        "./src/chemlint/server.py"
      ],
      "enabled": true
    }
  }
}
```

If OpenCode is running, restart it, and OpenCode should be able to see the ChemLint MCP server.

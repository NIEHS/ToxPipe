# Integrating ToxPipe Models into Visual Studio Code (VSCode)

__Note: This is tested and confirmed working on VSCode version 1.120.0.__

VSCode's Copilot can be configured to use models from ToxPipe using these steps:
1. Install the [LiteLLM Connector for Copilot extension for VSCode](https://marketplace.visualstudio.com/items?itemName=Gethnet.litellm-connector-copilot).
2. When prompted, provide [`https://litellm.toxpipe.niehs.nih.gov/`](https://litellm.toxpipe.niehs.nih.gov/) as the LiteLLM server URL and your provisioned API key for the API key.
3. The available models from ToxPipe should now populate the "other models" list. You may select the any of the models there to use them with Copilot's chat feature.

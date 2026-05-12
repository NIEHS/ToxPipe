# Miscellaneous Guides & Helpful Links

This document compiles links to various external guides and resources (as well as general guidance) that may be helpful when using or developing with ToxPipe. This document was written by Parker Combs and is, in part, based on his personal testing and experimentation with LLMs.

## OpenCode
[OpenCode](https://opencode.ai/docs/) is an agent that can perform powerful, multi-step coding processes and includes features like:
- Running code
- Parallel processing of LLMs
- Filesystem interaction
- MCP server integration
- Agent "skills" definition

### OpenCode agent skills
[https://opencode.ai/docs/skills/](https://opencode.ai/docs/skills/)

Agent skills are markdown files that provide structured steps to an LLM on how to perform certain tasks. They do not involve code (outside of example code provided as text to the model). Alternatively, you may provide the above link to OpenCode and ask it to generate skills for itself following that specification. Note that you must restart OpenCode for changes to the available skills to take effect.

### OpenCode MCP server support
[https://opencode.ai/docs/mcp-servers/](https://opencode.ai/docs/mcp-servers/)

OpenCode can connect to MCP servers to integrate external tools as context to its AI models. Note that many models have a maximum tool limit (i.e., GPT-5.4 may only load up to 128 tools simultaneously). Alternatively, You can ask OpenCode directly to write its own MCP server(s), enhanced by also providing it access to the specifications for a certain framework (like [FastMCP](https://gofastmcp.com/getting-started/welcome)). Note that you must restart OpenCode for changes to the MCP configuration to take effect.

### OpenCode general guidance
OpenCode appears to be quite adept at generating its own skills and tools. I was able to get Claude 4.6 Sonnet running through OpenCode to do the following:
- Write its own skills, specifically geared toward scientific web application generation
- "Think" about possible ways to improve expand an existing application it had written and implement those changes autonomously
- Write its own MCP server based on the FastMCP specifications and add it to its own configuration so it could use it in future queries. I provided it just links to the EPA EpiSuite's and PubChem's APIs, and gave it free reign to pull in other related sources as needed: EPA COmpTox, UniProt, NCBI, ChEMBL.
- Audit its own code for accessibility/508 compliance issues and fix them
- Audit its own code for bugs and fix them
- Write unit tests for bug detection
- Write thorough documentation about the above in Markdown format with examples

Overall, I have found it helpful to treat working with OpenCode simialrly to the typical software design process, and outline the steps for the OpenCode agent to follow:
1. Write code based on the user's specifications
2. Write tests to test new code
3. Run tests and detect bugs/issues
4. Fix detected bugs
5. Audit code for accessibility and fix as needed
6. Identify possible enhancements to the software
7. Implement enhancements
8. Repeat as needed until tests pass, all TODO features are implemented, and software complies with accessibility standards

<a name="readme-top"></a>

<!--
*** Thanks for checking out the Best-README-Template. If you have a suggestion
*** that would make this better, please fork the repo and create a pull request
*** or simply open an issue with the tag "enhancement".
*** Don't forget to give the project a star!
*** Thanks again! Now go create something AMAZING! :D
-->

<!-- PROJECT LOGO -->
<div align="center">
  <img src="./toxpipe-logo-v2.png" alt="ToxPipe Logo" width="412" height="178">
  <h1 align="center">ToxPipe: Semi-autonomous AI integration of diverse toxicological data streams</h1>
</div>

<!-- PROJECT SHIELDS -->
<!--
*** I'm using markdown "reference style" links for readability.
*** Reference links are enclosed in brackets [ ] instead of parentheses ( ).
*** See the bottom of this document for the declaration of the reference variables
*** for contributors-url, forks-url, etc. This is an optional, concise syntax you may use.
*** https://www.markdownguide.org/basic-syntax/#reference-style-links
-->

[![](https://img.shields.io/badge/Microsoft%20Teams-6264A7?logo=microsoftteams&logoColor=fff&style=plastic)](https://teams.microsoft.com/l/channel/19%3a5aa8e5c5ac6a400da6b57916a96083ee%40thread.skype/ToxPipe?groupId=af61690e-7397-48d4-947c-8a0444e36e90&tenantId=14b77578-9773-42d5-8507-251ca2dc2b06)

[![Python application](https://github.com/NIEHS/ToxPipe/actions/workflows/run_toxpipe_api.yml/badge.svg)](https://github.com/NIEHS/ToxPipe/actions/workflows/run_toxpipe_api.yml)

<!-- TABLE OF CONTENTS -->
<details>
  <summary>🗂️ Table of Contents</summary>
  <ol>
    <li><a href="#what-is-toxpipe">What is ToxPipe?</a></li>
    <li><a href="#approach">Approach</a></li>
    <li><a href="#system-architecture">System Architecture</a></li>
    <li><a href="#deployment">Deployment</a></li>
    <li><a href="#useful-links">Useful Links</a></li>
    <li><a href="#repo-structure">Repo Structure</a></li>
    <li><a href="#%EF%B8%8F-built-with">🛠️ Built With</a></li>
    <li><a href="#funding-sources">Funding Sources</a></li>
  </ol>
</details>

## 🤔 What is ToxPipe?

ToxPipe aims to explore the use of expert entrained AI-based systems for the rapid analysis and interpretation of toxicological properties of various compounds. By leveraging cutting-edge semi-autonomous AI systems, ToxPipe will enable scientists and toxicologists to explore diverse types of toxicologically relevant data through natural language instructions. Further, through use of expert entrainment ToxPipe will provide context generation that will act as a guide to novel, contemporary data streams that were previously challenging to access and integrate into toxicological characterization.

ToxPipe is meant to be a platform for interacting with various toxicological data streams. It comprises multiple components and like any agentic retrieval augmented generation (RAG) system, requires managing agents, state, prompts, database connections, APIs, and other systems.

<p align="right" style="font-size: 14px; color: #555; margin-top: 20px;">
    <a href="#readme-top" style="text-decoration: none; color: #007bff; font-weight: bold;">
        ↑ Back to Top ↑
    </a>
</p>

## Approach

Large language models (LLMs), such as [OpenAI’s GPT-based models](https://openai.com/blog/chatgpt), can be used to solve complicated tasks with natural language as a generic interface. By using techniques like retrieval augmented generation (RAG), LLMs can be given a set of instructions and can (semi-)autonomously explore various data sources. The LLMs will then generate responses or interpretations based on information stored inside the models along with the contextual data retrieved through RAG.

ToxPipe aims to repurpose (semi-)autonomous AI agents for AI-augmented exploration of existing toxicological data and literature. Some of the tasks that we believe are possible with autonomous agents and RAG are:

- Generation of toxicological narratives with deep explanatory context
- Analysis of chemical structure
- Analysis of biological assay results
- Summarization of journal abstracts
- Biological database exploration using text-to-SQL AI models
- A variety of other tasks that currently require large amounts of human time and labor.

By offloading these tasks to ToxPipe, it would allow toxicologists to repurpose their time towards higher-level cognitive tasks of directing the AI towards specific outputs.

<p align="right" style="font-size: 14px; color: #555; margin-top: 20px;">
    <a href="#readme-top" style="text-decoration: none; color: #007bff; font-weight: bold;">
        ↑ Back to Top ↑
    </a>
</p>

## System Architecture

The following diagram demonstrates an overall structure of ToxPipe. This model is subject to change as the project develops.

![ToxPipe Overview](toxpipe-ecosystem-new-2025.png)

Architecture documentation is in [`docs/architecture`](docs/architecture/index.qmd). Stack decisions are saved in [`docs/decisions`](docs/decisions/index.md). This is where we will document the reasoning behind our stack decisions.

<p align="right" style="font-size: 14px; color: #555; margin-top: 20px;">
    <a href="#readme-top" style="text-decoration: none; color: #007bff; font-weight: bold;">
        ↑ Back to Top ↑
    </a>
</p>

## Deployment

Deployment information is contained in [`docs/deployment`](docs/deployment/index.md).

<p align="right" style="font-size: 14px; color: #555; margin-top: 20px;">
    <a href="#readme-top" style="text-decoration: none; color: #007bff; font-weight: bold;">
        ↑ Back to Top ↑
    </a>
</p>

## Related Repositories

- [ToxPipe LLM Model Comparisons](https://github.com/NIEHS/toxpipe-model-comparison)
- [LibreChat](https://github.com/NIEHS/LibreChat)

## Useful Links

- [ToxPipe | 2024 NCBI AIxML Codeathon]

<p align="right" style="font-size: 14px; color: #555; margin-top: 20px;">
    <a href="#readme-top" style="text-decoration: none; color: #007bff; font-weight: bold;">
        ↑ Back to Top ↑
    </a>
</p>

## Repo Structure

- `.build`: This folder should contain all scripts related to build process (PowerShell, Docker compose…).
- `.config`: It should contain local configuration related to setup on local machine.
- `dep`: This is the directory where all your dependencies should be stored.
- `doc`: The documentation folder.
- `res`: For all static resources in your project. For example, images.
- `samples`: Providing “Hello World” & Co code that supports the documentation.
- `src`: The source code folder! However, in languages that use headers (or if you have a framework for your application) don’t put those files in here.
- `test`: Unit tests, integration tests… go here.
- `tools`: Convenience directory for your use. Should contain scripts to automate tasks in the project, for example, build scripts, rename scripts. Usually contains .sh, .cmd files for example.

<p align="right" style="font-size: 14px; color: #555; margin-top: 20px;">
    <a href="#readme-top" style="text-decoration: none; color: #007bff; font-weight: bold;">
        ↑ Back to Top ↑
    </a>
</p>

## 🛠️ Built With

![FastAPI Badge](https://img.shields.io/badge/FastAPI-009688?logo=fastapi&logoColor=fff&style=plastic)

- [NIEHS Librechat](https://github.com/NIEHS/LibreChat)
- [NIEHS LLM Comparison](https://github.com/NIEHS/ToxPipe-Model-Comparison)

<p align="right" style="font-size: 14px; color: #555; margin-top: 20px;">
    <a href="#readme-top" style="text-decoration: none; color: #007bff; font-weight: bold;">
        ↑ Back to Top ↑
    </a>
</p>

## Funding Sources

This work was funded by the National Institutes Health (NIH) under the following grants:

- [NOT-OD-23-070: Notice of Special Interest (NOSI): Administrative Supplements to Support the Exploration of Cloud in NIH-supported Research](https://grants.nih.gov/grants/guide/notice-files/NOT-OD-23-070.html)

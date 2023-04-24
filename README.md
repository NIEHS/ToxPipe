# ToxPipe

ToxPipe is a project that aims to use large language models to perform a variety of tasks in toxicology. The project is currently in the early stages of development, and is not yet ready for use.

# Overview

The following diagram demonstrates an overall structure of ToxPipe. This model is subject to change as the project develops.

# GitLab Repo is source of truth

Terraform deployment will be mananged from here. Build tools are all through GitLabs. Gitlab was chosen due to GitLabs CI/CD capabilities. Azure Cloud is needed for OpenAI API access for the orchestrator agent.

Following in the steps of [ChemCrow](https://arxiv.org/abs/2304.05376), ToxPipe will build and experiment with various language models as expert agents. The agents will be trained on a variety of toxicology data sets, and will be able to perform a variety of tasks in toxicology. The agents will be able to perform tasks such as:

-  Predicting toxicity of a compound given a set of conditions
-  Generate toxicological narratives
-  Answer questions about toxicology

# Tech Stack

- Terraform for Azure deployment management
    - https://gitlab.niehs.nih.gov/help/user/infrastructure/iac/terraform_state.md
    - https://aztfmod.github.io/documentation/
    - Ansible for machine management
- Gitlab for CI/CD
- MLFlow for model management and experiment documentation
- FastAPI for ToxPipe orchestration agents
- Milvus for vector search
- Auto-GPT, JARVIS for orchistration agents
- Posit Connect for front end, either Shiny or Shiny for Python for MVP
    - golem is a good framework for building production shiny apps in R
    - https://engineering-shiny.org/index.html
- Kubernetes on Azure for inference endpoints?
    - Trying to figure out how to make sure that inference endpoints have access to GPUs through MLFlow and Kubernetes
- Need to figoure out the best structure for storing pdf documents like NTP Technical Reports

# Useful Links

- https://github.com/Azure/azure-quickstart-templates
- https://aztfmod.github.io/documentation/
- https://github.com/microsoft/JARVIS
- https://github.com/Azure/Azurite
- https://github.com/mlflow/mlflow
- https://github.com/microsoft/DeepSpeed

# Repo Structure

- src Folder: The source code folder! However, in languages that use headers (or if you have a framework for your application) don’t put those files in here.
- test Folder: Unit tests, integration tests… go here.
- .config Folder: It should local configuration related to setup on local machine.
- .build Folder: This folder should contain all scripts related to build process (PowerShell, Docker compose…).
- dep Folder: This is the directory where all your dependencies should be stored.
- doc Folder: The documentation folder
- res Folder: For all static resources in your project. For example, images.
- samples Folder: Providing “Hello World” & Co code that supports the documentation.
- tools Folder: Convenience directory for your use. Should contain scripts to automate tasks in the project, for example, build scripts, rename scripts. Usually contains .sh, .cmd files for example.
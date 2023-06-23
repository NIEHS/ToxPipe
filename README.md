# ToxPipe

Our research project aims to explore the use of expert entrained AI-based systems for the rapid analysis and interpretation of toxicological properties of various compounds. By leveraging cutting-edge semi-autonomous AI systems, ToxPipe will enable scientists and toxicologists to explore diverse types of toxicologically relevant data through natural language instructions. Further, through use of expert entrainment ToxPipe will provide context generation that will act as an expert guide to novel, contemporary data streams that were previously challenging to access and integrate into toxicological characterization.  Examples of success in the area of expert entrained AI models include Auto-GPT and JARVIS (aka HuggingGPT) both of which employ OpenAI’s GPT-based models as a controller to connect fine-tuned, expert AI models. These projects enable AI to solve complicated tasks using plain language as a generic interface. As a world leader in toxicological assessment and reporting, the Division of Translational Toxicology at NIEHS is ideally positioned to identify the diverse and relevant domain space training data and to critically evaluate the expert entrained AI model. We will also investigate the ethical considerations of using generative AI for these purposes.

Following in the steps of [ChemCrow](https://arxiv.org/abs/2304.05376), ToxPipe will build and experiment with various language models as expert agents. The agents will be trained on a variety of toxicology data sets, and will be able to perform a variety of tasks in toxicology. The agents will be able to perform tasks such as:

- Predicting toxicity of a compound given a set of conditions
- Generate toxicological narratives
- Answer questions about toxicology

ToxPipe aims to repurpose semi-autonomous AI agents to explore existing toxicological data and literature using in-context learning. Some of the tasks that we believe are possible with this system are generation of toxicological narratives with deep explanatory context, analysis of chemical structure, analysis of biological assay results, summarization of journal abstracts, biological database exploration using text-to-SQL AI models, and a variety of other tasks that currently require large amounts of human time and labor. By offloading these tasks to autonomous agents, it would allow toxicologists to repurpose their time towards higher-level cognitive tasks of directing the AI towards specific outputs.

## System Architecture

The following diagram demonstrates an overall structure of ToxPipe. This model is subject to change as the project develops.

![ToxPipe Overview](res/diagrams/overview.svg)

ToxPipe aims to repurpose semi-autonomous AI agents to explore existing toxicological data and literature using in-context learning. Some of the tasks that we believe are possible with this system are generation of toxicological narratives with deep explanatory context, analysis of chemical structure, analysis of biological assay results, summarization of journal abstracts, biological database exploration using text-to-SQL AI models, and a variety of other tasks that currently require large amounts of human time and labor. By offloading these tasks to autonomous agents, it would allow toxicologists to repurpose their time towards higher-level cognitive tasks of directing the AI towards specific outputs.

## GitLab Repo is source of truth

Terraform deployment will be mananged from here. Build tools are all through GitLabs. Gitlab was chosen due to GitLabs CI/CD capabilities. Azure Cloud is needed for OpenAI API access for the orchestrator agent.

### Azure Cloud

Hosting inference endpoints, documents, databases, orchistrator agent, etc.

### BioWulf and NIEHS HPC

Will be used to train the expert models using apptainer, mlflow, and DeepSpeed.

## Tech Stack

- Gitlab for CI/CD
- nginx for reverse proxy
- Heimdall for landing page (Subject to change)
- Dialoqbase for chatbot interface
- Supabase for database
  - Postgres base
  - Realtime
  - Storage
  - Auth
  - Vector
  - Edge functions
- Terraform for Azure deployment management
  - <https://gitlab.niehs.nih.gov/help/user/infrastructure/iac/terraform_state.md>
  - <https://aztfmod.github.io/documentation/>
  - Ansible for machine management
- MLFlow for model management and experiment documentation
- Kubernetes on Azure for inference endpoints?
  - Trying to figure out how to make sure that inference endpoints have access to GPUs through MLFlow and Kubernetes
- Need to figure out the best structure for storing pdf documents like NTP Technical Reports
  - This is a LlamaIndex hierarchical storage problem to be solved

## Useful Links

- <https://github.com/Azure/azure-quickstart-templates>
- <https://aztfmod.github.io/documentation/>
- <https://github.com/microsoft/JARVIS>
- <https://github.com/Azure/Azurite>
- <https://github.com/mlflow/mlflow>
- <https://github.com/microsoft/DeepSpeed>
- <https://codeql.github.com/>

## Repo Structure

- `.build`: This folder should contain all scripts related to build process (PowerShell, Docker compose…).
- `.config`: It should local configuration related to setup on local machine.
- `dep`: This is the directory where all your dependencies should be stored.
- `doc`: The documentation folder
- `res`: For all static resources in your project. For example, images.
- `samples`: Providing “Hello World” & Co code that supports the documentation.
- `src`: The source code folder! However, in languages that use headers (or if you have a framework for your application) don’t put those files in here.
- `test`: Unit tests, integration tests… go here.
- `tools`: Convenience directory for your use. Should contain scripts to automate tasks in the project, for example, build scripts, rename scripts. Usually contains .sh, .cmd files for example.

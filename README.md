# ToxPipe

Our research project aims to explore the use of expert entrained AI-based systems for the rapid analysis and interpretation of toxicological properties of various compounds. By leveraging cutting-edge semi-autonomous AI systems, ToxPipe will enable scientists and toxicologists to explore diverse types of toxicologically relevant data through natural language instructions. Further, through use of expert entrainment ToxPipe will provide context generation that will act as an expert guide to novel, contemporary data streams that were previously challenging to access and integrate into toxicological characterization.  Examples of success in the area of expert entrained AI models include Auto-GPT and JARVIS (aka HuggingGPT) both of which employ OpenAI’s GPT-based models as a controller to connect fine-tuned, expert AI models. These projects enable AI to solve complicated tasks using plain language as a generic interface. As a world leader in toxicological assessment and reporting, the Division of Translational Toxicology at NIEHS is ideally positioned to identify the diverse and relevant domain space training data and to critically evaluate the expert entrained AI model. We will also investigate the ethical considerations of using generative AI for these purposes.

## Project Components and Workflow

JARVIS’s workflow consists of task planning, model selection, task execution, and response generation. For example, researchers gave JARVIS the input “please generate an image where a girl is reading a book, and her pose is the same as the boy in the provided example image. Then please describe the new image with your voice.” JARVIS was able to break the request down into individual tasks, such as analyzing the pose of the boy in the example image using OpenCV’s openpose control model, generating a new image using Stable Diffusion’s Controlnet Openpose model, then performing object detection to confirm the output of the previous models. JARVIS then used an image caption model to generate a caption for the new image, and finally used a text-to-speech model to generate an audio file of the previously generated caption.

ToxPipe aims to repurpose JARVIS and Auto-GPT for AI-augmented exploration of existing toxicological data and literature. Some of the tasks that we believe are possible with a system like JARVIS are generation of toxicological narratives with deep explanatory context, analysis of chemical structure, analysis of biological assay results, summarization of journal abstracts, biological database exploration using text-to-SQL AI models, and a variety of other tasks that currently require large amounts of human time and labor. By offloading these tasks to JARVIS, it would allow toxicologists to repurpose their time towards higher-level cognitive tasks of directing the AI towards specific outputs.

## System Architecture

The following diagram demonstrates an overall structure of ToxPipe. This model is subject to change as the project develops.

### Azure Cloud

Hosting inference endpoints, documents, databases, orchistrator agent, etc.

### Posit Connect

Front-end for ToxPipe. Will be used to interact with the AI agents. Built using Shiny or Shiny for Python.

### BioWulf and NIEHS HPC

Will be used to train the expert models using apptainer, mlflow, and DeepSpeed.

## GitLab Repo is source of truth

Terraform deployment will be mananged from here. Build tools are all through GitLabs. Gitlab was chosen due to GitLabs CI/CD capabilities. Azure Cloud is needed for OpenAI API access for the orchestrator agent.

Following in the steps of [ChemCrow](https://arxiv.org/abs/2304.05376), ToxPipe will build and experiment with various language models as expert agents. The agents will be trained on a variety of toxicology data sets, and will be able to perform a variety of tasks in toxicology. The agents will be able to perform tasks such as:

- Predicting toxicity of a compound given a set of conditions
- Generate toxicological narratives
- Answer questions about toxicology

## Tech Stack

- Terraform for Azure deployment management
  - <https://gitlab.niehs.nih.gov/help/user/infrastructure/iac/terraform_state.md>
  - <https://aztfmod.github.io/documentation/>
  - Ansible for machine management
- Gitlab for CI/CD
- MLFlow for model management and experiment documentation
- FastAPI for ToxPipe orchestration agents
- Milvus for vector search
- Auto-GPT, JARVIS for orchistration agents
- Posit Connect for front end, either Shiny or Shiny for Python for MVP
  - golem is a good framework for building production shiny apps in R
  - <https://engineering-shiny.org/index.html>
- Kubernetes on Azure for inference endpoints?
  - Trying to figure out how to make sure that inference endpoints have access to GPUs through MLFlow and Kubernetes
- Need to figoure out the best structure for storing pdf documents like NTP Technical Reports

## Useful Links

- <https://github.com/Azure/azure-quickstart-templates>
- <https://aztfmod.github.io/documentation/>
- <https://github.com/microsoft/JARVIS>
- <https://github.com/Azure/Azurite>
- <https://github.com/mlflow/mlflow>
- <https://github.com/microsoft/DeepSpeed>
- <https://codeql.github.com/>

## Repo Structure

- src Folder: The source code folder! However, in languages that use headers (or if you have a framework for your application) don’t put those files in here.
- test Folder: Unit tests, integration tests… go here.
- .config Folder: It should local configuration related to setup on local machine.
- .build Folder: This folder should contain all scripts related to build process (PowerShell, Docker compose…).
- dep Folder: This is the directory where all your dependencies should be stored.
- doc Folder: The documentation folder
- res Folder: For all static resources in your project. For example, images.
- samples Folder: Providing “Hello World” & Co code that supports the documentation.
- tools Folder: Convenience directory for your use. Should contain scripts to automate tasks in the project, for example, build scripts, rename scripts. Usually contains .sh, .cmd files for example.

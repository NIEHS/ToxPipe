# 🚀 Docker Stack Setup Guide

This guide will walk you through how to spin up and use the full Docker stack.

---

## 📦 Prerequisites

Make sure you have the following installed:
- [Git](https://git-scm.com/) Optional, but helps to easily download ToxPipe code to your server

- [Docker](https://docs.docker.com/get-started/get-docker/) Required

---

## 🛠️ Setup Instructions

### 1. Clone the Repository
Clone or download the repository to your server.

```
git clone https://github.com/NIEHS/ToxPipe.git
```
---

### 2. Configure Environment Variables
ToxPipe should work out of the box, with the only changes required being to the environment file. An example environment is provided with all required variables at env.example. Please copy this as .env and replace all example keys with your keys. If any keys are not provided, the specified model or feature will not work. All required changes are contained within < >; however, it is strongly recommended to change all default usernames, passwords, and secrets as well. While Langfuse and MCP variables are marked as optional, we suggest changing these as well for inclusion of the corresponding features into your stack. 

Note: NUM_WORKERS is set to 1. Increasing this is suggested, as it will increase efficiency and speed of requests. However, this is dependent on specifications (ie. CPU cores, memory) of your server. Increasing it too much will cause the stack to fail upon creation with no clear warning, as your server may be incapable of handling the load. We suggest first setting it to the number of cores on your server and increasing/decreasing from there.

#### Example copy and edit command
```
cp .env.example .env
nano .env
```

---

### 3. Optionally Configure Services/Add Models
Preset service and model cofigurations are already provided for use, with only .env variables needing to be changed for their function. However, if you would like to add new models or configure existing models, this can be done from within librechat.yaml and .litellm/litellm-config.yaml. If you would like to further configure the dashy dashboard, edits can be made to user-data/conf.yml. Finally, if you would like to configure existing services or add new services, you can create a docker-compose.override.yml file and include any desired changes or additions there. For more info on how using multiple compose files see [Docker](https://docs.docker.com/compose/how-tos/multiple-compose-files/merge/#merge-compose-files).

### 4. Deploy With Desired Servicess
This project includes multiple docker compose files for use.  
- docker-compose.yml (the default file)
- docker-compose.langfuse.yml (optional compose file for including langfuse)
- docker-compose.mcp.yml (optional compose for including mcp)

Docker compose is the main way to set up the stack with your desired services. Docker compose pull must be used first to obtain the specified images for each service. If using the ToxPipeMCP service in your stack, docker compose build must be used to manually build that image. Finally, docker compose up -d must be used to create and host the containers in a detached state so that others can access your stack. If you only care about the default services, no files will need to be specified when running compose. Additionally, if you want all features and combine the optional compose file services into a single docker-compose.override.yml file (see [Docker](https://docs.docker.com/compose/how-tos/multiple-compose-files/merge/#merge-compose-files)), then once again no files will need to be specified when running compose. However, if you want to use only some of the optional features, or keep the docker service files separated by function (ie. mcp, langfuse), then all desired compose files will have to be specified with -f each time docker compose is used. For example:

#### Default docker file only, or default + override file
```
docker compose pull
docker compose build (if using mcp)
docker compose up -d
```

#### Individual service files 
```
docker compose -f docker-compose.yml -f docker-compose.langfuse.yml -f docker-compose.mcp.yml pull
docker compose -f docker-compose.yml -f docker-compose.langfuse.yml -f docker-compose.mcp.yml build
docker compose -f docker-compose.yml -f docker-compose.langfuse.yml -f docker-compose.mcp.yml up -d 
```

---

## 🌐 Accessing the Application

Once the stack is running, access the services using your server’s IP address:

Dashy: http://<SERVER_IP>:8082  
LibreChat: http://<SERVER_IP>:3080  
LangFuse: http://<SERVER_IP>:3000  
Langflow: http://<SERVER_IP>:7860  

## Maintaing the Application
For more tips on running, maintaining, and updating your docker stack, please refer to the offical [Docker](https://docs.docker.com/guides/) manuals.


# 🚀 Docker Stack Setup Guide

This guide will walk you through how to spin up and use the full Docker stack. A list of steps is shown below, with in depth descriptions provided later for those unfamiliar with any of the methods.

**Warning: ToxPipe is a _large_ project. Make sure you have at least 40GB of free space before following these steps.**


1. Install docker and clone the repository onto your server
2. Copy env.example to .env and edit required variables
3. Copy dozzle/users.yml.example to dozzle/users.yml and provide any desired user info
4. Copy dashy/user-data.yml.example to dashy/user-data.yml and set the domain paths for all services
5. Optionally configure services or add new models
6. Set up Docker's network
7. Run Docker Compose to create and start all containers defined in the configuration
8. Access the application at the hosted url

---

## 1. Installing Docker and downloading the repo

Make sure you have the following installed on your server:

- [Docker](https://docs.docker.com/get-started/get-docker/) Required
- [Git](https://git-scm.com/) 
Optional, but helps to easily download ToxPipe code to your server with the following command
```
git clone https://github.com/NIEHS/ToxPipe.git
```

Note that if using Docker Desktop, you must ensure Docker Desktop is fully installed and the Docker Engine is running before setting up ToxPipe.

---

## 2. Copying and configuring the env file 
An example environment is provided with all required variables. Please copy this to .env and replace all example keys with your keys. If any keys are not provided, the specified model or feature will not work. All required changes are contained within < >; however, it is strongly recommended to change all default usernames, passwords, and secrets as well. MCP variables are marked as optional, and are only required if you plan to host the provided mcp services within your stack. 

Note: NUM_WORKERS is set to 1. Increasing this is suggested, as it will increase efficiency and speed of requests. However, this is dependent on specifications (ie. CPU cores, memory) of your server. Increasing it too much will cause the stack to fail upon creation with no clear warning, as your server may be incapable of handling the load. We suggest first setting it to the number of cores on your server and increasing/decreasing from there.

### Example copy and edit command
```
cp env.example .env
nano .env
```

---

## 3. Copying and configuring dozzle users
The dozzle users example file is contained at dozzle/users.yml.example. Please copy this to dozzle/users.yml, and add any desired users to the file. Users can be added by running the following command and copying the resulting user info into the file. For more help see the [Dozzle](https://dozzle.dev/guide/authentication#file-based-user-management) help page.
```
# Note: username is the desired login name and my_password is the desired login password. The password will be returned as a hash and should be stored that way in the file security purposes.
docker run -it --rm amir20/dozzle generate username --password my_password --email me@email.net --name "Admin" 
```

## 4. Copying and configuring the dashy config
The dashy config file is contained at dashy/conf.yml.example. Please copy this to dashy/conf.yml, and edit the required url. Do this by replacing any <my-server-ip> with your server's ip address. Alternatively, if you setup custom domains or security, change all urls accordingly to match your domain new domains. This file can also be edited for further dashboard customization. See [Dashy](https://dashy.to/) for more details.

## 5. Optionally Configure Services/Add Models
Preset service and model cofigurations are already provided for use, with only .env variables needing to be changed for their function. However, if you would like to add new models or configure existing models, this can be done from within librechat.yaml and .litellm/litellm-config.yaml.  Finally, if you would like to configure existing services or add new services, you can create a docker-compose.override.yml file and include any desired changes or additions there. For more info on how using multiple compose files see [Docker](https://docs.docker.com/compose/how-tos/multiple-compose-files/merge/#merge-compose-files).

Note: Ollama models will require extra configuration to make them work, as these models require custom downloads and access to a gpu server. Please see our [Ollama setup guide](ollama-readme.md) for help setting these models up. Also, setting up additional security measures is highly recommended, as by default the services are hosted publicly such that anyone with the url can access and use them. Please see our [security guide](toxpipe-security-readme.md) for help setting up additional security measures.

## 6. Set Up Docker's Network
We recommend that ToxPipe be used with a dedicated bridged network for its Docker containers. This can easily be done with:
```
docker network create autonomous
```
Note that by default, this network's name is ```autonomous```, but this may be changed as desired.

## 8. Running Docker Compose
This project includes two docker compose files for use.  
- docker-compose.yml (the default file)
- docker-compose.mcp.yml (optional compose for including mcp)

Docker compose is the main way to set up the stack with your desired services. Docker Compose must be used to create and host the containers in a detached state so that others can access your stack. If you only care about the default services, no files will need to be specified when running compose. Additionally, if you want mcp or any other new services and combine them into a single docker-compose.override.yml file (see [Docker](https://docs.docker.com/compose/how-tos/multiple-compose-files/merge/#merge-compose-files)), then once again no files will need to be specified when running compose. However, if you want to keep the optional docker service files separated by function (ie. mcp), and want to use those optional services, then all desired compose files will have to be specified with -f each time docker compose is used. For example:

**Note: multiple images will need to be pulled simultaneously if setting up ToxPipe for the first time. This may take a while (~30 min.). If this process fails due to a connection error, try pulling the images again, or try pulling each image individually.**

### Default docker file only, or default + override file
Note: This command pulls, builds, creates, and starts all services if any of those steps have not been done prior. 
```
docker compose up -d
```
Each step can be done individually with docker commands if desired.
```
docker compose litellm up -d
```

#### Individual service files 
```
docker compose -f docker-compose.yml -f docker-compose.langfuse.yml up -d 
```

#### Shutting down Docker containers
All containers may be shut down with:
```
docker compose down
```
Individual containers may be shut down with:
```
docker compose litellm down
```

---

## 9. Accessing the application

Once the stack is running, access the services using your server’s IP address and each services host port unless you have configured custom domains. The default url for each publicly hosted service is shown below:

Dashy: http://<SERVER_IP>:8082  
LibreChat: http://<SERVER_IP>:3080  
LiteLLM: http://<SERVER_IP>:8000  
LangFuse: http://<SERVER_IP>:3000  
Langflow: http://<SERVER_IP>:7860  
Dozzle: http://<SERVER_IP>:8888

## (Optional) Deploy the ToxPipeMCP server
To set up the ToxPipeMCP server, follow the instructions at [docs/toxpipemcp-readme.md](https://github.com/NIEHS/ToxPipe/blob/Deployment/docs/toxpipemcp-readme.md)

## Maintaining the Application
For more tips on running, maintaining, and updating your docker stack, please refer to the offical [Docker](https://docs.docker.com/guides/) manuals.

# Common Issues and FAQs

## Databases

### Database does not exist
If using the database components of ToxPipe (i.e., ```LITELLM_DB``` and ```LANGFLOW_DB``` in the ```.env``` file), ensure these databases actually exist in their respective Docker containers and that your specified user has access to the corresponding database. The Postgres Docker image should automatically create the specified database(s) upon first startup as long as the volume is empty; however, if they were not created for some reason, you may do it manually in Postgres with the following steps:
1. First, run ```docker exec -it litellm-db psql -U postgres``` to attach to the container running the Postgres instance and run the Postgres command line utility as the ``postgres``` user and connect to the default ```postgres``` database.
2. Run
   ```
   CREATE USER <username> WITH PASSWORD '<password>';
   CREATE DATABASE <database_name> OWNER <username>;
   ```

### Database connection refused
#### Ensure the user has appropriate database permissions
1. First, run ```docker exec -it litellm-db psql -U postgres``` to attach to the container running the Postgres instance and run the Postgres command line utility as the ``postgres``` user and connect to the default ```postgres``` database.
2. Run
   ```
   GRANT ALL PRIVILEGES ON DATABASE <database_name> TO <username>;
   \c <database_name>
   GRANT ALL ON SCHEMA public TO <username>;
   ```

#### Ensure the Postgres server is running on 0.0.0.0 and accepting connections
1. Create a ```pg_hba.conf``` file and ensure it contains the line:
   ```
   host    all             all             0.0.0.0/0               md5
   ```
   For this example, we will save this file at ```litellm-pg-etc/pg_hba.conf``` in the ToxPipe project directory.
2. Add the following to your ```docker-compose.yml``` specifications for the database service:
   ```
   command: >
     -c hba_file=/etc/postgresql/pg_hba.conf
   ```

   For example:
   ```
    litellm-db:
        container_name: litellm-db
        image: postgres:16.4
        restart: always
        environment:
          - POSTGRES_USER=${LITELLM_USER}
          - POSTGRES_PASSWORD=${LITELLM_PASSWORD}
          - POSTGRES_DB=${LITELLM_DB}
        volumes:
          - ./litellm-pg-etc/pg_hba.conf:/etc/postgresql/pg_hba.conf:ro # ensure you allow Docker to see this file
          - litellm-pg:/var/lib/postgresql/data
        networks:
          - autonomous
        healthcheck:
          test: ["CMD-SHELL", "pg_isready -U ${LITELLM_USER} -d ${LITELLM_DB}"]
        command: >
          -c hba_file=/etc/postgresql/pg_hba.conf
   ```
3. Completely shut down and delete the container, then recreate it and start it back up.

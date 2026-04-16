
# Setting up Ollama with GPU support and persistent storage for ToxPipe

ToxPipe supports locally-hosted models through [Ollama](https://ollama.com/). A sufficiently robust machine is required to effectively run Ollama: you must have access to at least one GPU.

## Setting up the Ollama Docker container
First, add the following block to your docker-compose.yml or docker-compose.override.yml configuration file for ToxPipe.
```
ollama:
    container_name: ollama
    image: ollama/ollama:latest # or whatever version you want to use
    deploy:
      resources:
        reservations:
          devices:
            - driver: nvidia # or "rocm" for AMD GPUs
              capabilities: [compute, utility]
    ports:
      - 11434:11434
    volumes:
      - /data/models:/root/models # where downloaded models should be saved on the host
      - ollama:/root/.ollama
    networks:
      - autonomous
    environment:
      OLLAMA_VULKAN: 1 # enable Vulkan support
      OLLAMA_KEEP_ALIVE: -1 # max. time models will stay loaded, -1 means models will never be unloaded
      OLLAMA_NO_CLOUD: 1 # use Ollama in purely offline mode
      OLLAMA_NUM_PARALLEL: 1 # number of parallel runners, probably want to set between 1-4
      OLLAMA_DEBUG: 1 # for logging
      OLLAMA_NEW_ENGINE: 1 
```

Then, run the container with:
```
docker compose pull ollama
docker compose up ollama -d
```

## Downloading models
Run the following code to get the PID of the running Ollama Docker container:
```
docker container ls | grep ollama
```
![Output of the "docker container ls | grep ollama" command, showing the Docker container's PID.](docker-terminal.png)

Next, run the following command to hook the terminal into the running container:
```
docker exec -it <PID> /bin/sh
# i.e., docker exec -it 6f60918c55b2 /bin/sh
```

From inside the container, the Ollama process should already be running. Run the following code to download the specific model you want. A full list of models supported by Ollama may be found [here](https://ollama.com/library).
```
ollama pull <model_name>
# ollama pull llama3.1:8b # downloads the 8B size of the Llama 3.1 model
# ollama pull gemma3:latest # downloads the latest build of the Gemma3 model
```

Once your model(s) is downloaded, you can exit the Docker container with ```Ctrl+D```.

## Configuring LiteLLM to point to Ollama models
Once you have downloaded the necessary models, you must set up LiteLLM to access them. First, navigate to your LiteLLM configuration file (i.e., ```litellm-config.yaml```) and open it for editing. For each Ollama model you want to add, add the following code under the ```model_list:``` header:
```
- model_name: <whatever you want the model to be callable by>
    litellm_params:
      model: ollama/<model>:<version>
      api_base: http://ollama:11434 # or whichever port the Ollama Docker container is running on

# For example:
# - model_name: llama3.1
#     litellm_params:
#       model: ollama/llama3.1:8b
#       api_base: http://ollama:11434
# - model_name: gemma3
#     litellm_params:
#       model: ollama/gemma3:latest
#       api_base: http://ollama:11434
```

After your models are configured, save the configuration file and restart the LiteLLM container with ```docker compose restart litellm```. The Ollama models should now be callable from the LiteLLM API.

## Configuring LibreChat to point to Ollama models
After your models are configured in LiteLLM, you can configure LibreChat to access them in the same way you would for remote-hosted models. Navigate to your LibreChat configuration file (```librechat.yaml```) and open it for editing. Add the following code under the
```
endpoints:
  custom:
    ...
```
headers:
```
endpoints:
  custom:
    - name: "Ollama"
      apiKey: "sk-1234" # Your LiteLLM API key or the LiteLLM API key for LibreChat use
      iconURL: "https://simpleicons.org/icons/ollama.svg"
      baseURL: "http://litellm:8000" # or wherever your LiteLLM instance is hosted
      models:
        default: ["llama3.1", "gemma3"] # comma-delimited list of Ollama model names as they are defined in LiteLLM
        fetch: false
        userIdQuery: True
      titleConvo: true
      titleModel: "llama3.1" # or whatever model you want to generate conversation titles in the lefthand navbar in LibreChat. This doesn't have to be an Ollama model
      titleMethod: "functions"
      titleMessageRole: "user"
      modelDisplayLabel: "Ollama"
      dropParams:
        - "stop"
        - "presence_penalty"
        - "frequency_penalty"
```

After your models are configured, save the configuration file and restart the LibreChat container with ```docker compose restart api```. The Ollama models should now be accessible from the LibreChat interface.
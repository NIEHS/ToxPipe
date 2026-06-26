# Setting Up Open Notebook With ToxPipe

## Introduction
[Open Notebook](https://github.com/lfnovo/open-notebook) is an open-source alternative to Google's Notebook LM that offers more privacy and customization. It is easily set up with Docker and supports models from a variety of providers, including compatibility with ToxPipe's models.

## Installation
### Prerequisites
- Docker (or Docker Desktop) and Docker Compose
- a ToxPipe LiteLLM API key

### Steps
- Follow the instructions at [https://github.com/lfnovo/open-notebook](https://github.com/lfnovo/open-notebook):
    - Create a new directory for Open Notebook
    - Create the file `docker-compose.yml` in this new directory and copy the following into it:
    ```
    services:
        surrealdb:
            image: surrealdb/surrealdb:v2
            command: start --log info --user root --pass root rocksdb:/mydata/mydatabase.db
            user: root
            ports:
            - "8000:8000"
            volumes:
            - ./surreal_data:/mydata
            restart: always

        open_notebook:
            image: lfnovo/open_notebook:v1-latest
            ports:
            - "8502:8502"
            - "5055:5055"
            environment:
            - OPEN_NOTEBOOK_ENCRYPTION_KEY=change-me-to-a-secret-string # CHANGEME
            - SURREAL_URL=ws://surrealdb:8000/rpc
            - SURREAL_USER=root
            - SURREAL_PASSWORD=root
            - SURREAL_NAMESPACE=open_notebook
            - SURREAL_DATABASE=open_notebook
            - SSL_CERT_FILE=/etc/ssl/certs/toxpipe.niehs.nih.gov.pem # Note: not in default config - this gets around the ToxPipe SSL certificate error
            - REQUESTS_CA_BUNDLE=/etc/ssl/certs/toxpipe.niehs.nih.gov.pem # Note: not in default config - this gets around the ToxPipe SSL certificate error
            volumes:
            - ./notebook_data:/app/data
            - ./toxpipe.niehs.nih.gov.pem:/etc/ssl/certs/toxpipe.niehs.nih.gov.pem # Note: not in default config - this gets around the ToxPipe SSL certificate error
            depends_on:
            - surrealdb
            restart: always
    ```
    - Change the `- OPEN_NOTEBOOK_ENCRYPTION_KEY=change-me-to-a-secret-string` to a new secret string of your choosing
    - Run `docker compose up -d` from a terminal in your Open Notebook directory to run the constituent `surrealdb` and `open_notebook` services
    - Wait a few seconds, and Open Notebook should be available at: `http://localhost:8502`
    - Navigate to `http://localhost:8502` and click on the "Models" tab on the lefthand side menu
    - In this new menu, scroll down to the "OpenAI Compatible" section and click the "+ Add Configuration" button
    - In the new modal that opens up, input the following values:
        - Configuration Name: ToxPipe
        - API Key: Your ToxPipe API key (should begin with "sk-")
        - Base URL: The URL of the ToxPipe LiteLLM API you are using (the URL for the main public API is: [https://litellm.toxpipe.niehs.nih.gov/](https://litellm.toxpipe.niehs.nih.gov/))
    - If using the default public ToxPipe LiteLLM instance, you will need to enable the proper SSL certificates:
        - Download the certificate bundle at [https://github.com/NIEHS/ToxPipe-Public-Certs/blob/main/toxpipe.niehs.nih.gov.pem](https://github.com/NIEHS/ToxPipe-Public-Certs/blob/main/toxpipe.niehs.nih.gov.pem) to your Open Notebook directory
        - Open the `docker-compose.yml` file and ensure these lines appear under the proper sections:
        ```
        environment:
        - SSL_CERT_FILE=/etc/ssl/certs/toxpipe.niehs.nih.gov.pem # Note: not in default config - this gets around the ToxPipe SSL certificate error
        - REQUESTS_CA_BUNDLE=/etc/ssl/certs/toxpipe.niehs.nih.gov.pem # Note: not in default config - this gets around the ToxPipe SSL certificate error

        volumes:
        - ./toxpipe.niehs.nih.gov.pem:/etc/ssl/certs/toxpipe.niehs.nih.gov.pem
        ```
    - Click the "Add Configuration" button
    - Back in the "Models" menu, click the "Models" button to the righthand side of your new ToxPipe configuration to open the "Discover Models" menu:
        - Click the "Add Selected" button or check each model in the list you would like to use
        - Click the "Add" button on the bottom right when done
    - Back in the "Models" menu, the "Default Model Assignments" should now be populated with the models you just selected. You can click on the dropdown for each model type to specify which model you want to use for each purpose.

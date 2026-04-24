# Implementing security controls in your ToxPipe deployment
When deploying ToxPipe publicly, it is **crucial** to implement proper security mechanisms to avoid unauthorized access to your AI models, accounts, and sensitive information. This guide will cover multiple methods for enhancing security.

# Limiting open ports
All ToxPipe services run through Docker Compose. If you do not wish to make certain services publicly available (for example, if you want users to be able to access LibreChat but not the underlying LiteLLM instance, thereby preventing users from querying the models programmatically), you can comment out or delete the service's port mapping:
```
litellm:
    container_name: litellm
    image: ghcr.io/berriai/litellm:main-v1.80.11.rc.1
    ports:
    #  - '8000:8000'
    ...
```

and change connections to the service to use Docker's internal network:
```
# ex. in librechat.yaml configuration

- name: "Azure OpenAI"
  apiKey: "sk-my-secret-key"
  iconURL: "https://icons.getbootstrap.com/assets/icons/openai.svg"
  # baseURL: "http://host.docker.internal:8000"
  baseURL: "http://litellm:8000"

```

# Deploying ToxPipe behind a VPN
A simple way to limit ToxPipe access at an organizational level is to require users to be behind a VPN to access the machine that the ToxPipe services are running on.

# Deploying ToxPipe behind a reverse proxy
Deploying ToxPipe behind a reverse proxy is an easy way of implementing basic security to the entire system. The recommended service is [Traefik](https://github.com/traefik/traefik), but any other sufficient proxy can be used, like Nginx. 

## Docker configuration

Setting up Traefik can easily be done by adding its Docker configuration as a service to your ```docker-compose.override.yml``` file:
### ```docker-compose.override.yml```
```
services: 
    traefik:
        image: traefik:v3.6 # CHANGEME to whichever version you want
        ports:
        - "80:80" # for HTTP
        - "443:443" # for HTTPS
        - "8080:8080" # for access to the Traefik API
        restart: always
        volumes:
        - path/to/your/ssl/certs.pem:/etc/traefik/tls/certs.pem # CHANGEME SSL certs for HTTPS
        - /var/run/docker.sock:/var/run/docker.sock # to connect to Docker's network
        - ./traefik/config.yml:/etc/traefik/config.yml # Dynamic configuration
        - ./traefik/traefik.yml:/etc/traefik/traefik.yml # Static configuration
        #- ./traefik/log:/var/log # logging (optional)
        labels:
        - traefik.enable=true
        networks:
        - your-docker-network-name # CHANGEME 
        command:
        - --providers.docker=true
        - --api.dashboard=true # enable Traefik's admin dashboard
        #- --log.level=DEBUG # set logging level
```
Full Docker container for Traefik documentation may be found here [https://doc.traefik.io/traefik/reference/install-configuration/providers/docker/](https://doc.traefik.io/traefik/reference/install-configuration/providers/docker/).

## Traefik configuration
Next, you will want to navigate to the ```traefik``` directory in the ToxPipe project root directory (create it if it does not exist). Create two files here for the Traefik configuration, ```traefik.yml``` and ```config.yml```.

### ```traefik.yml```
```
# Traefik static configuration file (/etc/traefik/traefik.yml)
# See https://doc.traefik.io/traefik/getting-started/configuration-overview/#the-static-configuration
# and https://doc.traefik.io/traefik/reference/static-configuration/cli/

api:
  dashboard: true                             # Enable the dashboard
  insecure: false                             # Enable insecure mode (no auth)

entryPoints:
  http:
    address: ":80"                            # Create the HTTP entrypoint on port 80
    http:
      redirections:                           # HTTPS redirection (80 to 443)
        entryPoint:
          to: "https"                         # The target element
          scheme: "https"                     # The redirection target scheme
          permanent: true
  https:
    address: ":443"                           # Create the HTTPS entrypoint on port 443
    asDefault: true

global:
  checknewversion: false                      # Periodically check if a new version has been released.
  sendanonymoususage: false                   # Periodically send anonymous usage statistics.

providers:
  docker:
    endpoint: "unix:///var/run/docker.sock"   # Listen to the UNIX Docker socket
    exposedByDefault: true                    # Only expose container that are explicitly enabled (using label traefik.enabled)
    network: "autonomous"                     # Default network to use for connections to all containers.
    watch: true                               # Watch Docker events
  file:
    filename: "/etc/traefik/config.yml"       # Link to the dynamic configuration
    watch: true                               # Watch for modifications
  providersThrottleDuration: 2                # Configuration reload frequency
```

### ```config.yml```
```
# Traefik dynamic configuration file
# See https://doc.traefik.io/traefik/getting-started/configuration-overview/#the-dynamic-configuration

http:
  routers:
    traefik:
      entryPoints:
        - "https"
      rule: "Host(`my.toxpipe.host.com`) && PathPrefix(`/dashboard`)"     # CHANGEME - your main hostname, this is also where the Dashy dashboard should live
      service: "api@internal"
      tls: {}
      middlewares:
        - "traefikAuth@file"

    dashy:
      entryPoints:
        - "https"
      service: "dashy@file"
      rule: "Host(`my.toxpipe.host.com`)"                                   # CHANGEME
      tls: {}
      priority: 1

    librechat:
      entryPoints:
        - "https"
      service: "librechat@file"
      rule: "Host(`my.librechat.host.com`)"                                 # CHANGEME
      tls: {}
      priority: 1

    langfuse:
      entryPoints:
        - "https"
      service: "langfuse@file"
      rule: "Host(`my.langfuse.toxpipe.host.com`)"                          # CHANGEME
      tls: {}
      priority: 1

    litellm:
      entryPoints:
        - "https"
      service: "litellm@file"
      rule: "Host(`my.litellm.host.com`)"                                   # CHANGEME
      tls: {}
      priority: 1
      middlewares:
        - default-security-headers

    promptfoo:
      entryPoints:
        - "https"
      service: "promptfoo@file"
      rule: "Host(`my.promptfoo.host.com`)"                                 # CHANGEME
      tls: {}
      priority: 1

    iconify:
      entryPoints:
        - "https"
      service: "iconify@file"
      rule: "Host(`my.iconify.host.com`)"                                   # CHANGEME
      tls: {}
      priority: 1

    langflow:
      entryPoints:
        - "https"
      service: "langflow@file"
      rule: "Host(`my.langflow.host.com`)"                                  # CHANGEME
      tls: {}
      priority: 1

    ragapi:
      entryPoints:
        - "https"
      service: "ragapi@file"
      rule: "Host(`my.ragapi.host.com`)"                                    # CHANGEME
      tls: {}
      priority: 1

    mongoexpress:
      entryPoints:
        - "https"
      service: "mongoexpress@file"
      rule: "Host(`my.mongoexpress.host.com`)"                              # CHANGEME
      tls: {}
      priority: 1

    ollam:
      entryPoints:
        - "https"
      service: "ollama@file"
      rule: "Host(`my.ollama.host.com`)"                                    # CHANGEME
      tls: {}
      priority: 1

    chromadb:
      entryPoints:
        - "https"
      service: "chromadb@file"
      rule: "Host(`my.chromadb.host.com`)"                                  # CHANGEME
      tls: {}
      priority: 1

    dozzle:
      entryPoints:
        - "https"
      service: "dozzle@file"
      rule: "Host(`my.dozzle.host.com`)"                                    # CHANGEME
      tls: {}
      priority: 1


# CHANGEME - NOTE! If you changed any of the ports that ToxPipe services run on in docker-compose.override.yml, you will need to change the corresponding port(s) below to match.
  services:
    traefik:
      loadBalancer:
        servers:
          - url: "http://traefik:8080"
        sticky:
          cookie:
            httpOnly: true
            secure: true

    dashy:
      loadBalancer:
        servers:
          - url: "http://dashy:8080"

    librechat:
      loadBalancer:
        servers:
          - url: "http://librechat:3080"

    langfuse:
      loadBalancer:
        servers:
          - url: "http://langfuse-server:3000"

    litellm:
      loadBalancer:
        servers:
          - url: "http://litellm:8000"

    promptfoo:
      loadBalancer:
        servers:
          - url: "http://promptfoo-ui:3000"

    iconify:
      loadBalancer:
        servers:
          - url: "http://iconify:3000"

    langflow:
      loadBalancer:
        servers:
          - url: "http://langflow:7860"

    ragapi:
      loadBalancer:
        servers:
          - url: "http://rag_api:8000"
    mongoexpress:
      loadBalancer:
        servers:
          - url: "http://mongo-express:8081"
    #ollama:
    #loadBalancer:
    #servers:
    #- url: "http://ollama:11434"
    chromadb:
      loadBalancer:
        servers:
          - url: "http://chromadb:8000"
    dozzle:
      loadBalancer:
        servers:
          - url: "http://dozzle:8080"

    biomni:
      loadBalancer:
        servers:
          - url: "http://172.17.0.1:7861"

  middlewares:

    # A basic authentification middleware, to protect the Traefik dashboard to anyone except myself
    # Use with traefik.http.routers.myRouter.middlewares: "traefikAuth@file"
    # The password here MUST be hashed, which can be done with:
    #   htpasswd -nbB user password     # BCrypt
    #   openssl passwd -apr1 password   # APR1 (MD5)
    traefikAuth:
      basicAuth:
        users:
          - "admin:hashed_password"     # CHANGEME - this is authentication for the Traefik admin dashboard. The format is username:hashed_password. You must supply the HASH here.

    # Recommended default middleware for most of the services
    # Use with traefik.http.routers.myRouter.middlewares: "default@file"
    # Equivalent of traefik.http.routers.myRouter.middlewares: "default-security-headers@file,error-pages@file,gzip@file"
    default:
      chain:
        middlewares:
          - default-security-headers
          - gzip

    # Add automatically some security headers
    # Use with traefik.http.routers.myRouter.middlewares: "default-security-headers@file"
    default-security-headers:
      headers:
        browserXssFilter: true                            # X-XSS-Protection=1; mode=block
        contentTypeNosniff: true                          # X-Content-Type-Options=nosniff
        forceSTSHeader: true                              # Add the Strict-Transport-Security header even when the connection is HTTP
        frameDeny: true                                   # X-Frame-Options=deny
        referrerPolicy: "strict-origin-when-cross-origin"
        sslRedirect: true                                 # Allow only https requests
        stsIncludeSubdomains: true                        # Add includeSubdomains to the Strict-Transport-Security header
        stsPreload: true                                  # Add preload flag appended to the Strict-Transport-Security header
        stsSeconds: 63072000                              # Set the max-age of the Strict-Transport-Security header (63072000 = 2 years)

    # Enables the GZIP compression (https://docs.traefik.io/middlewares/compress/)
    #   if the response body is larger than 1400 bytes
    #   if the Accept-Encoding request header contains gzip
    #   if the response is not already compressed (Content-Encoding is not set)
    # Use with traefik.http.routers.myRouter.middlewares: "gzip@file"
    gzip:
      compress: {}

# SSL certificate configuration
# If ALL your certs are in a single .pem, you can supply the same file for both the certFile and keyFile parameters.
# See https://doc.traefik.io/traefik/https/tls/
tls:
  stores:
    default:
      defaultCertificate:
        certFile: /etc/traefik/tls/certs.pem    # CHANGEME - should match specified volume in docker-compose.override.yml
        keyFile: /etc/traefik/tls/certs.pem     # CHANGEME - should match specified volume in docker-compose.override.yml
```

## SSL/TLS configuration
To set up HTTPS connectivity to your reverse proxy, you need not only your immediate SSL certificate (and private key) but also all intermediate SSL certificates for your organization. It is recommended to combine these all into one .pem file by appending the contents of each certificate file together. 

Update the left-hand side of the ```- path/to/your/ssl/certs.pem:/etc/traefik/tls/certs.pem``` volume in your ```docker-compose.override.yml``` to point to the location where your certificate .pem is stored on the host filesystem.

## Running Traefik
After the above configuration is complete, you may run the Traefik service with ```docker compose up traefik -d```.

# Per-service authentication
Most of ToxPipe's constituent services have application-level authentication that may be enabled. This section will detail these options. **Please note that none of these options are meant to be the singular form of security in a public-facing deployment, nor are they meant to be unbreakable. Deploying ToxPipe behind a reverse proxy with SSL and/or behind a VPN will always provide better security.**

## Dashy
Follow the guide at [https://dashy.to/docs/authentication/](https://dashy.to/docs/authentication/). The ```conf.yml``` discussed in this guide will be your Dashy configuration file in the directory: ```(toxpipe-root)/user-data/conf.yml```. Any environment variables should be configured in ToxPipe's ```.env``` file.

## LibreChat
Follow the guide at [https://www.librechat.ai/docs/configuration/authentication](https://www.librechat.ai/docs/configuration/authentication). You will need to configure these environment variables in ToxPipe's ```.env``` file.

## LiteLLM
LiteLLM's admin panel can be protected with authentication. Follow the guide here: [https://docs.litellm.ai/docs/proxy/ui](https://docs.litellm.ai/docs/proxy/ui). You will need to set the ```UI_USERNAME``` and ```UI_PASSWORD``` environment variables in the ToxPipe ```.env``` file. Similarly, you may also set ```DISABLE_ADMIN_UI="True"``` in the .env to disable the admin panel completely, which may be useful for production environments.

Model access through LiteLLM may be controlled through authentication using API keys: more information may be found here: [https://docs.litellm.ai/docs/proxy/virtual_keys](https://docs.litellm.ai/docs/proxy/virtual_keys).

## Langflow
Follow the guide at [https://docs.langflow.org/api-keys-and-authentication#start-a-langflow-server-with-authentication-enabled](https://docs.langflow.org/api-keys-and-authentication#start-a-langflow-server-with-authentication-enabled) with additional documentation at [https://docs.langflow.org/api-keys-and-authentication](https://docs.langflow.org/api-keys-and-authentication) to add authentication to the Langflow interface. These environment variables will have to be set in ToxPipe's ```.env``` file.

## Langfuse
Follow the guide at [https://langfuse.com/self-hosting/security/authentication-and-sso](https://langfuse.com/self-hosting/security/authentication-and-sso). Environment variables should be set in the ToxPipe ```.env``` file.

## MongoDB and Mongo Express
To add authentication to the Mongo Express UI, you may set the ```ME_CONFIG_BASICAUTH_USERNAME``` and ```ME_CONFIG_BASICAUTH_PASSWORD``` environment variables in ToxPipe's ```.env``` file. Also ensure that the environment variable ```ME_CONFIG_BASICAUTH_ENABLED: true``` is set in the ```.env``` or ```docker-compose.override.yml``` files.

To change the authentication information for MongoDB, you may follow the guidance at [https://hub.docker.com/_/mongo](https://hub.docker.com/_/mongo). Namely, you will need to set the ```MONGO_INITDB_ROOT_USERNAME``` and ```MONGO_INITDB_ROOT_PASSWORD``` environment variables in ToxPipe's ```.env``` or ```docker-compose.override.yml``` files. If you set these variables, make sure you update Mongo Express's connection string accordingly to include these credentials.

## Dozzle
Follow the guidance at [https://dozzle.dev/guide/authentication](https://dozzle.dev/guide/authentication) and [https://dozzle.dev/guide/changing-base](https://dozzle.dev/guide/changing-base) to set up authentication for Dozzle. Namely, you will need to set the ```DOZZLE_AUTH_PROVIDER=simple``` environment variable in ToxPipe's ```.env``` or ```docker-compose.override.yml``` files. To generate the login credentials for dozzle, run the following code:
```
docker run -it --rm amir20/dozzle generate admin --password password --email me@email.net --name "Admin"
```
where ```admin``` is the username and ```password``` is the password you will use to access the Dozzle UI. You should also specify your own email. This code will output some YAML like this:
```
users:
    admin:
        email: me@email.net
        name: Admin
        password: $2a$11$CGcURl4KqtEIPDV1XDwNJOBBMKdmINY3C7QYzpCYWcFvL9kB79lqO
        filter: ""
        roles: ""
```
where the password listed here is actually a hashed version of the plaintext password you supplied. **When you log in to the UI, you will need to supply the original, plaintext password, NOT the hash!** Place this YAML in the ```(toxpipe-root)/dozzle/users.yml``` file, either manually or with 
```
docker run -it --rm amir20/dozzle generate admin --password password --email me@email.net --name "Admin" > dozzle/users.yml
```
and restart the dozzle dcontainer with ```docker compose restart dozzle``` to enable authentication.
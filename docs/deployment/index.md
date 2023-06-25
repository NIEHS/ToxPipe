TODO: Stack will automatically be deployed from the `prod` branch of this repo. This will be done through GitLab CI/CD.
Currently deployed on ehsdttlp30 using Docker Compose for each individual repository. 

### ToxPipe Supabase Deployment
```
cd /toxpipe/toxpipe-supabase/docker
docker compose up -d
```

### Dialoqbase Deployment
```
cd /toxpipe/dialoqbase/docker
docker compose up -d
```

### AGiXT Deployment
```
cd /toxpipe/AGiXT
docker compose up -d
```

### ToxPipe Deployment
```
cd /toxpipe/toxpipe/.build
docker compose up -d
```
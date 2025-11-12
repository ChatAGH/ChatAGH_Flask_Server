1. Build image
```commandline
docker build -t chatagh-api:latest . 
```

1. Run container
```commandline
docker run -p 8000:8000 chatagh-api:latest
```
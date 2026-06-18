# DVA Test Environment

Start core DVA services:
```console
docker compose up -d
```


## Testing

Just run all [karate](https://karatelabs.github.io/karate/) tests:
```console
docker compose --profile karate up --abort-on-container-exit
```

(Will start all necessary services using Docker Compose, run the test scenarios and then stop everything.)

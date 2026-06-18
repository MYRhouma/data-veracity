# DVA API module (Kotlin)

## How to build

Execute from the parent directory (root of the repository)
```console
docker buildx build -t dva-api:latest -f dva-api/Dockerfile ./
```

## How to run unit tests

```console
./gradlew test
```

> [!TIP]
> If your goal is ultimate reproducibility, you can try the following one-liner to run unit tests in a Docker container.
> Run it from the parent directory (the repository root).
> ```console
> docker run --rm -it \
>     -v ./docs/spec/openapi.yaml:/home/gradle/docs/spec/openapi.yaml:ro \
>     -v /run/docker.sock:/run/docker.sock \
>     $(docker buildx build -q --no-cache --target build -f dva-api/Dockerfile ./) \
>     gradle test
> ```

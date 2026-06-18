# DVA processing module (Python)

> [!IMPORTANT]
> This project is built with [`uv`](https://docs.astral.sh/uv/).
> If you are a developer, please [install `uv`](https://docs.astral.sh/uv/getting-started/installation/).


## How to run

```console
$ uv run dva-processing
```


## Run unit tests

```console
$ uv run pytest
```

> [!TIP]
> If your goal is ultimate reproducibility, you can try the following one-liner to run unit tests in a Docker container.
> Run it from the parent directory (the repository root).
> ```console
> $ docker run --rm -it \
>     $(docker buildx build --target build -q --no-cache -f dva-processing/Dockerfile ./) \
>     uv run pytest
> ```

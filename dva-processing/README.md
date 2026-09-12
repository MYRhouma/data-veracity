# DVA processing module (Python)

The processing module is the DVA's veracity-check engine.
It is stateless: it evaluates data-quality requirements — ODCS `DataQuality` entries, the
same form they take inside a VLA — against data handed to it, and reports the outcome.
Deciding *which* requirements apply is the VLA Manager's job, and attesting to the
outcome is the VC Manager's; this service only runs the checks.

> [!IMPORTANT]
> This project is built with [`uv`](https://docs.astral.sh/uv/).
> If you are a developer, please [install `uv`](https://docs.astral.sh/uv/getting-started/installation/).


## Role

| Endpoint | Caller | Purpose |
|---|---|---|
| `POST /evaluate` | VLA Manager UI | Evaluate one requirement against data — for trying a requirement out while building a VLA |
| `POST /evaluate-batch` | DVA API | Evaluate every requirement in a VLA against data — the veracity check of the synchronous attestation flow |
| `POST /evaluate/from-template` | VLA Manager UI | Fetch a VLA template, render it with a model, and evaluate the result against data |

Three engines back `implementation`, selected by the requirement's `engine`:
`JQ` (a jq expression yielding `{ success, details }`), `SCHEMA` (a JSON Schema document),
and `GREAT_EXPECTATIONS` (a YAML expectation definition).
ODCS types `engine` as a free-form string, so a requirement naming anything else is only
rejected when it is evaluated — with a `400`, not at deserialisation.

The hand-written OpenAPI spec lives at [`docs/spec/dva-processing.yaml`](../docs/spec/dva-processing.yaml)
and is served at `/swagger` (Swagger UI) and `/redoc`, with the schema itself at
`/swagger/openapi.json`.


## Configuration

Everything the service reads comes from the environment.

| Variable | Default | Purpose |
|---|---|---|
| `DVA_VLA_MANAGER_URL` | `http://localhost:8000` | VLA Manager API, where `POST /evaluate/from-template` fetches templates |
| `DVA_PROCESSING_OPENAPI_FILE` | `/app/openapi.yaml` | The spec to serve; when it is missing, FastAPI's auto-generated schema is served instead |
| `DVA_LOG_LEVEL` | `warn` | Log verbosity (any level `structlog` accepts) |


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

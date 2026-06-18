# Data veracity assurance BB

The Data Veracity Assurance (DVA) building block allows data exchange participants to agree on and later prove/verify quality requirements or properties of the exchanged data.

## Design Document

See the design document [here](docs/design-document.md).

## Building instructions

At the moment, DVA has several subcomponents:

* **API server** in [`dva-api/`](dva-api/) – gateway / entry point / connector integration
* **Processing** in [`dva-processing/`](dva-processing/) – evaluates veracity requirements
* **RabbitMQ** from [`rabbitmq`](https://hub.docker.com/_/rabbitmq) – message queue facilitating communication between the API server and the processing module
* **ACA-Py Controller** in [`dva-acapy-controller/`](dva-acapy-controller/) – contains SSI/VC-related logic
* **ACA-Py Agent** from [`ghcr.io/hyperledger/aries-cloudagent-python`](https://github.com/orgs/hyperledger/packages/container/package/aries-cloudagent-python) – an SSI cloud agent (~ wallet)
* **PostgreSQL** from [`postgres`](https://hub.docker.com/_/postgres) – stores application state, events, and _logs_
* **Dashboard** in [`dva-dashboard/`](dva-dashboard/) – frontend application that displays database contents on a dashboard interface
* **VLA Manager** in [`vla-manager`](vla-manager/) – frontend application for VLAs management (creation, display, etc)

All of these are either existing Docker images or have been prepared for docker image building.
Note that some of the subcomponents currently require the build context to be the root of the repository.

You can use the following commands to build / pull the images (from the repository root):

```console
docker buildx build -t dva-api:latest -f dva-api/Dockerfile ./
docker buildx build -t dva-processing:latest -f dva-processing/Dockerfile ./
docker pull rabbitmq:4-management-alpine
docker buildx build -t dva-aca-py-controller:latest -f dva-acapy-controller/Dockerfile ./
docker pull ghcr.io/hyperledger/aries-cloudagent-python:py3.9-0.12.6
docker pull postgres:17-alpine
docker buildx build -t dva-dashboard:latest ./dva-dashboard/
docker buildx build -t vla-manager:latest ./vla-manager/
```

> [!NOTE]
> Check the currently used RabbitMQ, PostgreSQL, and ACA-Py versions in [`test-env/common-services.yml`](test-env/common-services.yml).

You normally do not have to do this however as you should be using Docker Compose to set up your DVA instance (see the [_test environment_](test-env/)).

> [!NOTE]
> The resulting `dva-api` image currently needs to receive a command parameter when running.
> Currently, the only used parameter is `api`.


## Running instructions

A test environment has been prepared in the [`test-env/`](test-env/) subdirectory.

A simple `docker compose up` should be sufficient to start the test environment.
You can find more information in the README in [`test-env/`](test-env/).

The following additional Docker Compose profiles are available:

* **`karate`:** in addition to the default services, this profile also includes an ephemeral `karate` container that executes availble Karate tests.  
   Use `docker compose --profile karate up --detach` to start a test environment and run all Karate tests.
   Check the `karate` container’s logs and/or the [`karate-reports/`](test-env/karate-reports/) subdirectory inside [`test-env/`](test-env/) to analyze the results.


## Example usage

> [!TIP]
> More detailed test definitions can be found [here](docs/test-definitions.md).

See the [OpenAPI specification](docs/spec/openapi.yaml) for available endpoints.

> [!NOTE]
> By default, an API is available at **`http://127.0.0.1:9091`** when using the [test environment](test-env/) with the default settings.
> All endpoints in the table below are relative to this URL.

> [!TIP]
> * Example **input** data can be found in [`test-env/test-data/`](test-env/test-data/).
> * Example **output** data can be found in [`test-env/example-outputs/`](test-env/example-outputs/).

Example requests to test functionality manually (non-exhaustive):

| Endpoint                | HTTP Method | Example parameters                                                  | Example input (request body)                                                                                                                                                    | Expected output                                                                                                                                                         |
|-------------------------|-------------|---------------------------------------------------------------------|---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|-------------------------------------------------------------------------------------------------------------------------------------------------------------------------|
| `/template`             | `GET`       | *nothing*                                                           | *empty*                                                                                                                                                                         | `200 OK` and a [list of VLA templates](test-env/example-outputs/template-get.json)                                                                                      |
| `/template`             | `POST`      | *nothing*                                                           | a [VLA template](test-env/test-data/vla-template/template.json)                                                                                                                 | `201 CREATED` and [an ID](test-env/example-outputs/id.json)                                                                                                             |
| `/template/{id}`        | `GET`       | `id`: a VLA template ID (eg `3c58c2fd-6d7a-4953-9f76-7c71fc3ac7e2`) | *empty*                                                                                                                                                                         | `200 OK` and the requested VLA template ([example for `a3be74b8-a7dc-4c42-aa83-59b678004748`](test-env/example-outputs/template-id-get.json))                           |
| `/template/{id}`        | `DELETE`    | `id`: a VLA template ID (eg `3c58c2fd-6d7a-4953-9f76-7c71fc3ac7e2`) | *empty*                                                                                                                                                                         | `204 NO CONTENT`                                                                                                                                                        |
| `/template/{id}/render` | `POST`      | `id`: a VLA template ID (eg `3c58c2fd-6d7a-4953-9f76-7c71fc3ac7e2`) | a VLA template’s model, according to its `variableSchema` ([example for `test-env/test-data/vla-template/template.json`](test-env/test-data/vla-template/template-render.json)) | `200 OK` and a rendered VLA template with the given data ([example for `test-env/test-data/vla-template/template.json`](test-env/example-outputs/template-render.json)) |
| `/vla`                  | `GET`       | *nothing*                                                           | *empty*                                                                                                                                                                         | `200 OK` and a [list of VLAs](test-env/example-outputs/vla-get.json)                                                                                                    |
| `/vla`                  | `POST`      | *nothing*                                                           | a [VLA request](test-env/test-data/vla-request/request.json)                                                                                                                    | `201 CREATED` and [an ID](test-env/example-outputs/id.json)                                                                                                             |
| `/vla/from-templates`   | `POST`      | *nothing*                                                           | a [VLA request using templates](test-env/test-data/vla-request/request-from-templates.json)                                                                                     | `201 CREATED` and [an ID](test-env/example-outputs/id.json)                                                                                                             |
| `/vla/{id}`             | `GET`       | `id`: a VLA ID (eg `570b22e0-2e90-4e02-8c7b-1d6d274629f3`)          | *empty*                                                                                                                                                                         | `200 OK` and the VLA template ([example](test-env/example-outputs/vla-id-get.json))                                                                                     |
| `/attestation`          | `POST`      | *nothing*                                                           | an [AoV request](test-env/test-data/aov/timestamp-in-range/request-good.json)                                                                                                   | `200 OK` and [an ID](test-env/example-outputs/id.json)                                                                                                                  |
| `/attestation/verify`   | `POST`      | *nothing*                                                           | an [AoV verification request](test-env/test-data/aov/verif-req.json)                                                                                                            | `200 OK` and an AoV JSON object from ACA-Py                                                                                                                            |

> [!NOTE]
> AoV requests (`POST /attestation`) are processed asynchronously.


## Unit testing

### DVA API ([`dva-api`](dva-api/))

#### Setup test environment

_No setup needed._

#### Run tests

Set your working directory to `dva-api/` and execute:
```console
./gradlew test
```

#### Expected results

In the test output, you should see all JUnit tests passing.

<details>
  <summary>Example output segment (click to open)</summary>

  ```
  [...]
  ApplicationTest > should respond with not found error on nonexistent path requested() PASSED
  AoVRoutesTest > should create attestation request() PASSED
  DocRoutesTest > should return swagger documentation page when slash swagger is requested() PASSED
  DocRoutesTest > should return HTML page when root route is requested() PASSED
  TemplateRoutesTest > should delete existing template() PASSED
  TemplateRoutesTest > should not allow creation of template with existing ID() PASSED
  TemplateRoutesTest > should respond with not found error when attempting to read nonexistent template() PASSED
  TemplateRoutesTest > should respond with list of templates() PASSED
  TemplateRoutesTest > should create new template() PASSED
  TemplateRoutesTest > should respond with not found error when attempting to delete nonexistent () PASSED
  TemplateRoutesTest > should respond with existing template if exists() PASSED
  [...]
  ```
</details>

### DVA Processing Module ([`dva-processing`](dva-processing/))

> [!NOTE]
> A nice way to run the tests from the repository root using Docker without having to touch your local environment:
> ```console
> docker run --rm -it -v ./dva-processing:/app ghcr.io/astral-sh/uv:debian-slim uv --directory /app/ run pytest
> ```

#### Setup test environment

Find a way to run [uv](https://docs.astral.sh/uv) → [installation instructions](https://docs.astral.sh/uv/getting-started/installation/)

#### Run tests

Set your working directory to `dva-processing/` and execute:
```console
uv run pytest
```

#### Expected results

In the test output, you should see all PyTest tests passing.

<details>
  <summary>Example output segment (click to open)</summary>

  ```
  ============================================================ test session starts ============================================================
  platform linux -- Python 3.12.8, pytest-8.4.1, pluggy-1.6.0
  rootdir: /projects/uni/edge/data-veracity/dva-processing
  configfile: pyproject.toml
  plugins: anyio-4.9.0
  collected 3 items

  tests/test_example.py ..                                                                                                              [ 66%]
  tests/test_qc.py .                                                                                                                    [100%]
  ```
</details>

### DVA ACA-Py Controller Module ([`dva-acapy-controller`](dva-acapy-controller/))

> [!NOTE]
> A nice way to run the tests from the repository root using Docker without having to touch your local environment:
> ```console
> docker run --rm -it -v ./dva-acapy-controller:/app ghcr.io/astral-sh/uv:debian-slim uv --directory /app/ run pytest
> ```

#### Setup test environment

Find a way to run [uv](https://docs.astral.sh/uv) → [installation instructions](https://docs.astral.sh/uv/getting-started/installation/)

#### Run tests

Set your working directory to `dva-acapy-controller/` and execute:
```console
uv run pytest
```

#### Expected results

In the test output, you should see all PyTest tests passing.

<details>
  <summary>Example output segment (click to open)</summary>

  ```
  ============================================================ test session starts ============================================================
  platform linux -- Python 3.12.8, pytest-8.4.1, pluggy-1.6.0
  rootdir: /projects/uni/edge/data-veracity/dva-processing
  configfile: pyproject.toml
  plugins: anyio-4.9.0
  collected 3 items

  tests/test_controller.py ..                                                                                                           [100%]
  ```
</details>


## Component-level testing

### Setup test environment

_No setup needed, but you need to have Docker- and Docker Compose installed._

### Run tests

Change your working directory to `test-env/` and run the following:
```console
docker compose --profile karate up
```

### Expected results

All container should start successfully and the `karate` container should exit with code `0`.
`karate`’s summary table in the log should show the same number next to `scenarios` as `passed` (ie, all scenarios pass).

<details>
  <summary>Click to see any example of <code>karate</code>’s summary table</summary>

  ```
  karate-1  | Karate version: 1.5.0
  karate-1  | ======================================================
  karate-1  | elapsed:   2.84 | threads:    1 | thread time: 1.64
  karate-1  | features:     2 | skipped:    0 | efficiency: 0.58
  karate-1  | scenarios:    4 | passed:     4 | failed: 0
  karate-1  | ======================================================
  karate-1  |
  karate-1  | HTML report: (paste into browser to view) | Karate version: 1.5.0
  karate-1  | file:///app/target/karate-reports/karate-summary.html
  karate-1  | ===================================================================
  ```
</details>

In addition, you can check `karate` test results by checking the files generated in [`test-env/karate-reports/`](test-env/karate-reports/), such as `karate-summary.html` – you can open this in a browser.

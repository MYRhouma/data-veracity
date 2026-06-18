# Test Definitions – Data veracity assurance (DVA)

Component-level tests for DVA are implemented as [Karate](https://karatelabs.github.io/karate/) features and scenarios.

> [!TIP]
> You can find a test environment that is also capable of running all of these tests automatically in [`test-env/`](../test-env/).
> There, you probably want to use at least the `dev` profile or even the `karate` one that also automatically runs all Karate tests.

> [!TIP]
> The documentation below only refers to endpoints, relative to wherever the DVA API is running.
> Using test environment in [`test-env/`](../test-env/), these paths are relative to [`localhost:9090`](http://localhost:9090/).

## [Feature] Veracity Level Agreement (VLA) template management

> [!NOTE]
> **Corresponding Karate feature file:**
> [`templates.feature`](../test-env/karate-features/templates.feature)

### [Scenario] Retrieve all VLA templates

> [!NOTE]
> **Corresponding Karate scenario title:**
> `get all VLA templates`

**Objective:**
Ensure DVA can return all currently stored VLA templates.

**Precondition:**
_nothing_

**Steps:**

1. **Action:**
   Send a `GET` HTTP request to the `/template` endpoint  
   **Expected result:**
   A list of VLA templates is returned in a `200 OK` response.
   By default, DVA is preloaded with two sample VLA templates.
   <details>
     <summary>After a clean start, the response body should match (click to open)</summary>

     ```json
     [
       {
         "id": "template-0001",
         "objective": {
           "evaluationScheme": {
             "evaluationMethod": "syntax_check",
             "criterionType": "VALID_INVALID"
           },
           "targetAspect": "SYNTAX"
         }
       },
       {
         "id": "template-0002",
         "objective": {
           "evaluationScheme": {
             "evaluationMethod": "age_check",
             "criterionType": "WITHIN_RANGE"
           },
           "targetAspect": "TIMELINESS"
         }
       }
     ]
     ```
   </details>
   
### [Scenario] Create a VLA template, retrieve it, then delete it

> [!NOTE]
>  **Corresponding Karate scenario title:**
> `create, get, then delete VLA template`
                  -
**Objectives:**

* Ensure DVA can create VLA templates
* Ensure DVA can retrieve VLA templates by ID
* Ensure DVA can delete VLA templates by ID

**Precondition:**
No VLA template with ID `template-test-0` should exist in the database.

**Steps:**

1. **Action:**
   Send a `POST` HTTP request to the `/template` endpoint with [this](../test-env/test-data/vla-template/template.json) body.  
   **Expected result:**
   The response is a `201 CREATED` message with a JSON in the body that has an `id` property (a UUID) → we’ll refer to this as `${id}`.

2. **Action:**
   Send a `GET` HTTP request to the `/template/${id}` endpoint.  
   **Expected result:**
   The [previously submitted VLA template](../test-env/test-data/vla-template/template.json) is returned in a `200 OK` response.

3. **Action:**
   Send a `DELETE` HTTP request to the `/template/${id}` endpoint.  
   **Expected result:**
   An empty `200 OK` response.

4. **Action:**
   Verify that the template has been deleted by making another `GET` request to the `/template/${id}` endpoint.
   **Expected result:**
   A `404 NOT FOUND` error response.


## [Feature] Attestation of Veracity (AoV) handling

> [!NOTE]
> **Corresponding Karate feature file:**
> [`aov.feature`](../test-env/karate-features/aov.feature)

### [Scenario] Submit an AoV request with passing data

> [!NOTE]
>  **Corresponding Karate scenario title:**
> `create an AoV request with data passing requirements`
                  -
**Objectives:**

* Ensure DVA can successfully generate AoVs
* Ensure that when the data accompanying the AoV request conforms to the VLA, the evaluations in the AoV include this information

**Precondition:**
_nothing_

**Steps:**

1. **Action:**
   Send a `POST` HTTP request to the `/attestation` endpoint with [this](../test-env/test-data/aov/request-good.json) body.  
   **Expected result:**
   A `200 OK` response with a JSON body that has an `id` property (a UUID) → we’ll refer to it as `${id}`.

2. **Action:**
   Wait a few seconds.

3. **Action:**
   Verify that an AoV has been submitted to the callback URL in the [submitted AoV request](../test-env/test-data/aov/request-good.json) (`http://callback-dummy/callback`) by sending a `GET` HTTP request to the `/get/last` endpoint **of the callback dummy component in the test network** (normally mapped to `localhost:9099`).
   **Expected result:**
   A `200 OK` response from the _callback-dummy_ component with an AoV in the `payload` property of the response body.
   The `evaluations` array inside the AoV payload should indicate **passing** checks.
  <details>
    <summary>Click to see an example response from <code>callback-dummy</code></summary>

    ```
    HTTP/1.1 200 OK
    Accept-Ranges: bytes
    Cache-Control: no-cache
    Connection: keep-alive
    Content-Length: 613
    Content-Type: application/json; charset=utf-8
    Date: Sun, 23 Mar 2025 21:06:12 GMT
    Keep-Alive: timeout=5
    
    {
        "headers": {
            "host": "callback-dummy",
            "user-agent": "python-requests/2.32.3",
            "accept-encoding": "gzip, deflate",
            "accept": "*/*",
            "connection": "keep-alive",
            "content-length": "339",
            "content-type": "application/json"
        },
        "method": "post",
        "mime": "application/json",
        "params": {},
        "path": "/callback",
        "payload": {
            "aovID": "07f4e4cc-425c-4416-a8c4-4eab262880be",
            "contractID": "8665acf8-0e70-465a-9a4b-e58bd0aa2559",
            "evaluations": [],
            "vc": {
                "id": "300bdede-c62e-400e-bb9f-8dcbf6d7077e",
                "type": "VerifiableCredential",
                "validFrom": "2025-03-23T21:05:17.856489",
                "subject": {
                    "id": "/catalog/participants/provider-test-id"
                },
                "issuer": "attester-0000"
            }
        }
    }
    ```
  </details>

> [!WARNING]
> Currently, evaluations will always be empty arrays.
> The feature of including evaluations in the AoVs is being tracked in [#31](https://github.com/Prometheus-X-association/data-veracity/issues/31).

### [Scenario] Submit an AoV request with failing data

> [!NOTE]
>  **Corresponding Karate scenario title:**
> `create an AoV request with data failing requirements`
                  -
**Objective:**
Ensure DVA refuses to generate AoVs when the data fails the requirements in the relevant VLA.

**Precondition:**
_nothing_

**Steps:**

1. **Action:**
   Send a `POST` HTTP request to the `/attestation` endpoint with [this](../test-env/test-data/aov/request-bad.json) body.  
   **Expected result:**
   A `200 OK` response with a JSON body that has an `id` property (a UUID) → we’ll refer to it as `${id}`.

2. **Action:**
   Wait a few seconds.

3. **Action:**
   Verify that an AoV has been submitted to the callback URL in the [submitted AoV request](../test-env/test-data/aov/request-good.json) (`http://callback-dummy/callback`) by sending a `GET` HTTP request to the `/get/last` endpoint **of the callback dummy component in the test network** (normally mapped to `localhost:9099`).
   **Expected result:**
   A `200 OK` response from the _callback-dummy_ component with an AoV in the `payload` property of the response body.
   The `evaluations` array inside the AoV payload should indicate **failing** checks.
  <details>
    <summary>Click to see an example response from <code>callback-dummy</code></summary>

    ```
    HTTP/1.1 200 OK
    Accept-Ranges: bytes
    Cache-Control: no-cache
    Connection: keep-alive
    Content-Length: 613
    Content-Type: application/json; charset=utf-8
    Date: Sun, 23 Mar 2025 21:06:12 GMT
    Keep-Alive: timeout=5
    
    {
        "headers": {
            "host": "callback-dummy",
            "user-agent": "python-requests/2.32.3",
            "accept-encoding": "gzip, deflate",
            "accept": "*/*",
            "connection": "keep-alive",
            "content-length": "339",
            "content-type": "application/json"
        },
        "method": "post",
        "mime": "application/json",
        "params": {},
        "path": "/callback",
        "payload": {
            "aovID": "07f4e4cc-425c-4416-a8c4-4eab262880be",
            "contractID": "8665acf8-0e70-465a-9a4b-e58bd0aa2559",
            "evaluations": [],
            "vc": {
                "id": "300bdede-c62e-400e-bb9f-8dcbf6d7077e",
                "type": "VerifiableCredential",
                "validFrom": "2025-03-23T21:05:17.856489",
                "subject": {
                    "id": "/catalog/participants/provider-test-id"
                },
                "issuer": "attester-0000"
            }
        }
    }
    ```
  </details>

> [!WARNING]
> Currently, evaluations will always be empty arrays.
> The feature of including evaluations in the AoVs is being tracked in [#31](https://github.com/Prometheus-X-association/data-veracity/issues/31).

### [Scenario] Verify a valid AoV

> [!NOTE]
> Not yet implemented.
> Feature tracked in [#10](https://github.com/Prometheus-X-association/data-veracity/issues/10).

### [Scenario] Verify an invalid AoV

> [!NOTE]
> Not yet implemented.
> Feature tracked in [#10](https://github.com/Prometheus-X-association/data-veracity/issues/10).


## [Feature] Proof of Veracity (PoV) handling

> [!NOTE]
> Not yet implemented.
> Feature tracked in [#10](https://github.com/Prometheus-X-association/data-veracity/issues/16).

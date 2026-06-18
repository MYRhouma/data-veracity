# Requirement specifications

A requirement always looks like this:
```json
{
  "engine": __QUALITY_ENGINE__,
  "implementation": __IMPLEMENTATION_STRING__
}
```
where the value of `engine` is one of the following (supported engines):
* `GREAT_EXPECTATIONS` ([GreatExpectations](https://greatexpectations.io/))
* `JQ` ([jq](https://jqlang.org/) evaluation)
* `SCHEMA` ([JSON schema](https://json-schema.org/) validator)

`implementation` is always a string passed to the evaluation engine and its format and content depends on the engine.

## Great Expectations

For Great Exectations requirements, the `implementation` string must be a ‘flattened’ YAML document of the following form:
```yaml
---
type: __EXPECTATION_TYPE__
kwargs: {}
meta: __METADATA__
...
```
The value of `type` should match a known expectation function, such as `ExpectColumnValuesToBeBetween`.
`kwargs` contain the parameters (as name-value pairs) passed to that specific expectation function.
`meta` is currently used to guide the JSON-to-DataFrame mapping done in the processing component (GreatExpectations works on tabular data).

### JSON to DataFrame mapping details

GreatExpectations (at least in most cases) requires data to be in tabular format.
Behind the scenes, the proessing module uses Pandas DataFrames as these tables.
So, JSON-structured input data must be converted to DataFrames as a preprocessing step.

How the columns in the (typically single row) DataFrame should be obtained must be encoded in the `meta` of the `GreatExpectations` requirement implementation string.
The format for `meta` is the following:
```yaml
meta:
  schema:
    root_path: OPTIONAL, "$" BY DEFAULT
    columns:
      column_1_name:
        jsonpath: OPTIONAL, "$.column_1_name" BY DEFAULT
        dtype: OPTIONAL "string" BY DEFAULT
      column_2_name:
        jsonpath: OPTIONAL, "$.column_2_name" BY DEFAULT
        dtype: OPTIONAL "string" BY DEFAULT
```
In many cases, neither `jsonpath` nor `dtype` must be overridden from their defaults; the sample below is a valid equivalent:
```yaml
meta:
  schema:
    columns:
      column_1_name:
      column_2_name:
```

For each column name key in `columns`, the associated `jsonpath` defines how to obtain the values for that column.
The default is to look for the same column name at the root of the JSON structure as a top-level property.
The associated `dtype` specifies what data type to assign to the column in the DataFrame.
Most often, the default `string` is sufficient, but specific types may need to be specified for numbers or timestamps.

‘flattening’ the implementation `YAML` to a string means that this sample:
```yaml
---
type: ExpectColumnValuesToBeBetween
kwargs:
  column: description
  min_value: 10
  max_value: 100
meta:
  schema:
    columns:
      description:
...
```
becomes
```
"---\ntype: ExpectColumnValuesToBeBetween\nkwargs:\n  column: description\n  min_value: 10\n  max_value: 100\nmeta:\n  schema:\n    columns:\n      description:\n...\n"
```

> [!NOTE]
> In a future version, data may be passed directly in the requirement JSON but for now, pure _string_ implementations must be used.


## jq

The `implementation` string for `JQ` requirements is much simpler: the string just has to be a jq expression, as one would pass to the `jq` binary.
The only caveat is that since `jq` does not return anything by default (unlike other engines), a JSON with the following structure must be returned as the result of the expression (and it is the responsibility of the requirement designer to ensure this):
```json
{
  "success": __BOOLEAN__,
  "details": __OPTIONAL_STRING__
}
```

An example:
```jq
if .description != ''
then {
  success: true,
  details: 'Description is a valid non-empty string'
}
else {
  success: false,
  details: 'Description must not be an empty string'
}
end
```
or, _stringified:_
```
"if .description != '' then { success: true, details: 'Description is a valid non-empty string' } else { success: false, details: 'Description must not be an empty string' } end"
```


## Schema

Schema requirements test JSON schema conformance.

The value of the `implementation` string can take two values:
* a ‘direct’ inclusion of an entire JSON schema
* a URL to a JSON schema


## Evaluation input/output format

The following structure is used to describe an evaluation request:
```
{
  "requirement": __REQUIREMENT_AS_SEEN_AT_THE_START_OF_THE_DOCUMENT__,
  "data": __INPUT_DATA__
}
```
`data` is an arbitrary JSON element that will be passed to the quality engine.

All quality engines (either directly or after a transformation done by the processing component) respond with an evaluation result of the following form:
```json
{
  "engine": __QUALITY_EGINE__,
  "timestamp": __WHEN_THE_EVALUATION_WAS_DONE__,
  "success": __BOOLEAN__,
  "details": __OPTIONAL_STRING__,
  "error": __OPTIONAL_STRING__
}
```

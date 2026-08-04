# Customer Preference API

A small FastAPI service that stores each customer's communication
preferences (marketing opt-in, channel, zip code, display name) with
add / update / delete / search endpoints. Built as a real test target for
[ComplianceAgent](../cmp-dashboard-develop/README.md)'s dashboard
**Repositories** tab and its Engine A contract/mutation probing.

## Endpoints

| Method | Path                | Purpose                                      |
|--------|---------------------|-----------------------------------------------|
| POST   | `/preferences`      | Add a preference record (`409` if it exists)  |
| PUT    | `/preferences/{id}` | Update a record, partial fields (`404` if missing) |
| DELETE | `/preferences/{id}` | Delete a record (`404` if missing)            |
| GET    | `/preferences`      | Search, filterable by `customer_id`, `comm_channel`, `marketing_opt_in`, `zip_code`, `display_name_contains` |

Field contract (`models.py`) mirrors ComplianceAgent's reference consumer in
`guardrails/engine_a_contract.py`: `comm_channel` is one of
`email|sms|push|mail`, `zip_code` accepts int or string and normalizes to a
5-digit string, `display_name` is capped at 128 chars. Invalid input returns
a controlled `422` — FastAPI/Pydantic validation never lets a bad payload
reach an unhandled exception.

## Run it

```bash
pip install -r requirements.txt
uvicorn main:app --reload --port 8000
```

Interactive docs: `http://localhost:8000/docs`
OpenAPI spec (for the orchestrator's `--openapi` flag): `http://localhost:8000/openapi.json`

## Test it

```bash
pytest tests -v
```

## Example requests

```bash
curl -X POST localhost:8000/preferences \
  -H "Content-Type: application/json" \
  -d '{"customer_id":"cust-1","marketing_opt_in":true,"comm_channel":"sms","zip_code":2118,"display_name":"Alex"}'

curl -X PUT localhost:8000/preferences/cust-1 \
  -H "Content-Type: application/json" -d '{"display_name":"Alexandra"}'

curl "localhost:8000/preferences?comm_channel=sms"

curl -X DELETE localhost:8000/preferences/cust-1
```

## Registering with ComplianceAgent

In `guardrails.config.json` (see the parent project's README §6), register
this as a producer with a live consumer probe:

```json
{
  "api_repos": [
    {
      "name": "preference-api",
      "local_path": "../preference-api",
      "openapi": "http://localhost:8000/openapi.json"
    }
  ],
  "consumer_repos": [
    {
      "name": "preference-api",
      "depends_on": ["preference-api"],
      "base_url": "http://localhost:8000/preferences",
      "probe": true
    }
  ]
}
```

With the server running, the orchestrator's `--target-url` / `probe:true`
mode will POST the Engine A mutation battery at `/preferences` and flag any
`5xx` as a violation.

# Local research inference service

The optional inference extra enables a local, research-only service. It is separate from the static showcase. It uses a label-free synthetic fixture by default and creates deterministic **synthetic weights** for demonstrations; those outputs are not predictions from recovered checkpoints.

```sh
python -m pip install '.[inference,dev]'
export GATE7_LAB_TOKEN="$(python -c 'import secrets; print(secrets.token_urlsafe(32))')"
python -m cmj_recovery_dynamics.research_lab
```

The service binds to `127.0.0.1:8765` only. Every request requires the token in `X-Lab-Token`. Browser requests are accepted only from `http://127.0.0.1:3000`; Host and Origin are checked independently. Give the token only to the local interface. A caller may inspect `/v1/health` and `/v1/capabilities`, then POST `/v1/predict` with exactly `version`, `candidate`, `repeat`, `observation_id` and `mode`. Version is `gate7-lab-v1`; mode is `synthetic_demo` or `original`. Example:

```sh
curl -H "X-Lab-Token: $GATE7_LAB_TOKEN" -H 'Content-Type: application/json' \
  --data '{"version":"gate7-lab-v1","candidate":"M0","repeat":0,"observation_id":"training-0","mode":"synthetic_demo"}' \
  http://127.0.0.1:8765/v1/predict
```

Responses identify synthetic weights or original checkpoints, observation alias, origin, horizon, target order and units, a response identity, and CPU-source and CPU-to-saved-CUDA states. The saved-CUDA comparison is not an authentic GPU replay. Refusals contain stable codes; request bodies and paths are not logged. Synthetic example M6–M8 requests refuse until the operator has independently supplied a valid basis-row authority.

To use original checkpoints or authorized observations, a trusted operator writes and executes a private Python startup script. The script constructs `ResearchLab` with immutable `ObservationGrant` and `ModelGrant` tuples and calls `serve`. An `ObservationGrant` selects an origin and horizon in an independently authorized `Gate7ObservationBuilderV1`, whose constructor pins observation bytes and routine authority and enforces pre-origin availability. Give it public-safe aliases only. Model grants require independently authenticated source and candidate/repeat/config/checkpoint associations, plus both SHA-256 pins; their paths are supplied only by the operator at startup. The loader rechecks the pins, contracts and weights-only deserialization. The service cannot independently establish an attestation just because a string or digest was supplied: the operator must verify it against the private evidence first. Never expose the operator script, pins, data or checkpoints through the static site or public Git.

M6–M8 additionally require a `BasisGrant` for the selected observation. Its five unscaled values and independently verified `row_sha256` bind the observation-source digest, origin, exact projected raw/history tensors, horizon and basis values using `row_digest`. The matching authority must be independently established from source evidence; computing a digest from untrusted submitted values is not authorization. Missing or mismatched basis is refused. The first two standardized values alone are consumed by M6; M7/M8 use all five.

The service processes one request at a time, admits one row per request, rejects bodies over 8 KiB, limits operator checkpoint/config files to 8 MB/1 MB, and terminates an inference worker after 20 seconds. A connection has a 25-second overall deadline and a five-second inactivity limit. These limits do not establish production readiness; local operating-system scheduling, process startup and filesystem behavior can still delay shutdown or resource release. Only trusted local operators may provision grants; access to the machine and token remains a security boundary.

Run focused service tests with `python -m pytest tests/test_research_lab.py`. No result here establishes predictive accuracy, generalization, clinical validity or suitability for production.

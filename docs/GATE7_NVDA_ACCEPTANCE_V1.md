# Gate7 Windows NVDA manual acceptance, version 1

Status: **SCREEN_READER_ACCEPTANCE_PENDING**. Automated accessibility tests and browser accessibility-tree checks do not establish screen-reader acceptance. A real qualified tester must complete and sign this record.

Use a supported Windows browser with the tester's installed NVDA. Record Windows, browser, NVDA and speech settings, keyboard layout, application commit, date and tester. Use synthetic observations and weights only. Start the loopback service and the local Research Lab under the documented local-token procedure. Never include the token, observations, original-checkpoint outputs or private locators in the acceptance record.

1. With NVDA running and the pointer unused, open the local Research Lab. Navigate headings and landmarks. Confirm the research-only purpose and synthetic-weight distinction are spoken in a sensible reading order.
2. Tab from the top. Confirm the token field has a useful name, password masking and keyboard focus. Enter the token, activate Connect, and confirm connection status is announced without exposing the token. Confirm successful connection clears the field.
3. Navigate model, repeat, execution mode and observation selectors. Confirm each name, current value and disabled state is announced. Choose a synthetic H72 observation and run. Confirm the busy state and completion announcement occur once without trapping focus.
4. Read both outputs in browse and focus modes. Confirm mean concentric force is associated with N/kg and concentric net impulse with m/s. Confirm a negative sign, a small nonzero scientific-notation value and nine-significant-digit formatting are intelligible. Record pronunciation concerns; do not call a value rounded to zero acceptable.
5. Read candidate/repeat, origin/horizon, response identity and synthetic provenance. Confirm CPU/CUDA fields describe synthetic execution as not applicable and do not imply original-model or GPU qualification. Repeat with D7 and verify its identity is spoken correctly.
6. Select M6, M7 or M8 with an observation lacking a basis grant. Run and confirm the refusal is announced as an alert, no stale result is presented as current, and the controls permit recovery. Select a qualified synthetic observation and repeat successfully.
7. Select original mode without a registered checkpoint. Confirm the unavailable state and disabled run control are understandable. This script grants no original-checkpoint use permission.
8. Stop the local service and attempt a run. Confirm the outage and reconnect guidance are announced. Restart and reconnect using keyboard only. While a deliberately stalled synthetic request is active, activate Disconnect; confirm the request is cancelled and a new connection/run works. Verify the timeout announcement using a qualified local test setup without exposing credentials.
9. At 200% browser zoom, repeat key navigation and result reading. Confirm focus remains visible, reading order is usable and essential content is reachable. Do not equate a desktop zoom test with a mobile screen-reader session.
10. Disconnect and close/reopen the page. Confirm no token is retained in the URL, local/session storage or visible form state.

Record each step as PASS, FAIL or NOT TESTED, with reproducible observations and assistive-technology output where useful. Record separate desktop/browser combinations rather than generalizing. Record issue IDs and retest results. The release gate remains pending until a real session has no unresolved blocking findings and a named acceptance owner signs it.

Tester / versions / date: PENDING

Step results / issue references / retest evidence: PENDING

Acceptance owner / decision / signature: PENDING

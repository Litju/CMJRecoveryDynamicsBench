Local Research Lab
==================

This interface runs separately from the static research showcase. It connects
only to the local research service at ``127.0.0.1:8765``; start the service
using its documented local setup and choose an operator-held access token.
No checkpoints or observations are included here.

From the repository root, serve the interface on its allowed loopback origin::

    python3 -m http.server 3000 --bind 127.0.0.1 --directory website/research-lab

Open ``http://127.0.0.1:3000`` and enter the token in the connection field.
The token is held only in the active page memory, never in a URL or browser
storage. Disconnect or close the page to clear it. The default execution mode
uses synthetic demonstration weights; those outputs are explicitly marked and
are not recovered model predictions. Original inference requires an
operator-configured checkpoint, observation authority and, where required,
authenticated basis input.

Browser checks use the Playwright and axe dependencies already declared by the
showcase. After installing them with ``npm ci --prefix website`` and installing
Playwright Chromium, run from the repository root::

    website/node_modules/.bin/playwright test --config website/research-lab/playwright.config.cjs

The live service tests are skipped unless the local service is already running
and ``LAB_LIVE_TOKEN`` contains its operator-held token. To exercise the complete
synthetic-fixture request path, export that variable privately and run the same
command. Set ``LAB_SCREENSHOT_DIR`` to a writable directory if screenshots are
needed; the token field is cleared immediately after connection.

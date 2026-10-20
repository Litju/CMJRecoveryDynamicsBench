# Build and deployment

## Build locally

Use Node.js 22. Install exactly from the committed lockfile and build the static export:

```sh
npm ci
npm run build
```

The build first verifies the pinned scientific snapshots and generated fixtures, then runs Next.js 16.4.2 with `output: "export"`. The deployable artifact is `out/`. No runtime environment variables, secrets, database, API, Next.js server process or external asset fetch is required.

For a local production preview:

```sh
python3 -m http.server 4173 --directory out
```

This Python server is for review only. It is not a production web server. The complete Playwright suite starts its own static server on port 4174 after the build so an existing development server cannot be reused as production output.

## Hosting configuration

[`vercel.json`](../vercel.json) currently declares the Next.js framework, `npm ci`, `npm run build` and `out/` as the output directory. These values match the local static export. A compatible static host must serve the files under `out/` and return the exported HTML for the root page. No API routes or dynamic routes need server rewrites.

The public launch configuration is not complete: this checkout has no .vercel/project.json, no approved production hostname and no canonical URL. In the canonical monorepo, configure the Vercel project root directory as website/. The root layout keeps robots.index and robots.follow disabled while the site is unpublished. No sitemap or robots file advertises an unapproved URL. Open Graph and Twitter text metadata are present; an absolute canonical URL, public indexing and social preview image require an owner-approved hostname and final brand decision.

## Access and release steps

No Vercel project was linked or deployment attempted for this task. The handoff records a previous Vercel 403. In this environment, the read-only `vercel whoami` command also fails because the installed global CLI shim points to a missing `dist/vc.js`, and there is no linked project file. Do not work around account permissions.

After the owner approves the final name/hostname and a deployment:

1. Install or repair the Vercel CLI through the owner's approved package manager and authenticate with the authorized Vercel account.
2. Ask a project owner to grant access or create/link the approved Vercel project.
3. Confirm `npm ci`, `npm run build`, `npm run test:ui` and the static output before connecting production.
4. Use `vercel.json`'s existing build settings. Confirm the output and public URLs, update approved canonical/robots/social metadata, and run a fresh desktop/mobile smoke check on the preview deployment before production promotion.
5. If a production deployment later needs rollback, use the Vercel dashboard to restore the previously approved production deployment. No production deployment exists from this task, so there is currently nothing to roll back.

## GitHub repository

The website is part of the canonical repository at website/. The owner authorized public branch publication; the review PR and hosted CI results will be recorded in the reconciliation manifest. No Vercel project or deployment is linked or authorized. See the release checklist for the remaining launch gates.

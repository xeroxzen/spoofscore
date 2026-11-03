# Host the web page

The web page in `web/` is three static files with no build step. This guide shows you how to publish it on Cloudflare Pages or GitHub Pages, and how to change the footer to your own contact details.

## Before you begin

- A fork or copy of this repository.
- Edit the `<footer>` in `web/index.html`. It names the original author; replace it with your own name and contact link, or remove it.

## Cloudflare Pages

1. In the Cloudflare dashboard, go to **Workers & Pages** and create a Pages project connected to your repository.
2. Set **Build command** to empty and **Build output directory** to `web`.
3. Deploy. The page is served at `<project>.pages.dev`, and you can add a custom domain from the project settings.

## GitHub Pages

GitHub Pages can only serve the repository root or `/docs` from a branch. To serve `web/`, deploy it with a workflow:

1. In the repository settings, go to **Pages** and set **Source** to **GitHub Actions**.

2. Add this workflow:

   ```yaml
   # .github/workflows/pages.yml
   name: Deploy web page
   on:
     push:
       branches: [main]
       paths: ["web/**"]
     workflow_dispatch:
   permissions:
     contents: read
     pages: write
     id-token: write
   jobs:
     deploy:
       runs-on: ubuntu-latest
       environment:
         name: github-pages
         url: ${{ steps.deployment.outputs.page_url }}
       steps:
         - uses: actions/checkout@v4
         - uses: actions/upload-pages-artifact@v3
           with:
             path: web
         - id: deployment
           uses: actions/deploy-pages@v4
   ```

3. Push to `main`. The page is served at `https://<user>.github.io/spoofscore/`.

## Any other static host

Upload the contents of `web/`. The page needs:

- `app.js` and `spoofscore.js` served as `text/javascript`, because they're ES modules.
- Outbound requests from the browser to `https://cloudflare-dns.com`. If you add a Content Security Policy, include `connect-src https://cloudflare-dns.com`.

## Privacy

The page sends each domain the visitor checks to Cloudflare's DNS-over-HTTPS resolver. Nothing is sent to your server, and nothing is stored. If you add analytics, say so on the page.

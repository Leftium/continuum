# Maintain the site

The public entry point is configured for
[https://leftium.github.io/continuum/](https://leftium.github.io/continuum/).
It becomes available after GitHub Pages setup and an authorized merge deploy
successfully. The site uses MkDocs with its built-in theme, Markdown pages in
`docs/site/`, and navigation in `mkdocs.yml`. Generated HTML is ignored.

Protocol and client instructions stay in their existing repository files. The
site links their immutable release sources instead of maintaining another copy.
When supporting a new stable release, verify its published status and exact
commit, then update the release and source links together. Existing PR contracts
keep their accepted pins.

## Build and preview locally

From the repository root, create an isolated documentation environment:

```sh
python3 -m venv .venv-docs
.venv-docs/bin/python -m pip install -r requirements-docs.txt
.venv-docs/bin/python -m mkdocs build --strict
.venv-docs/bin/python -m mkdocs serve
```

CI uses the same requirements and `python -m mkdocs build --strict`. Warnings
fail the build, including missing page links and anchors. This validates local
documentation links; review external release and commit links when they change.
Run `bash scripts/check-continuum.sh` for the protocol and reference client checks.

## GitHub Pages setup

Before the first production deploy, a repository administrator selects
**GitHub Actions** in **Settings > Pages > Build and deployment > Source**.
Use the default project URL; this setup needs no custom domain, DNS changes or
additional secrets. Keep the `github-pages` environment restricted to `main`.

The documentation workflow builds all PRs with read-only repository permissions.
PR runs do not configure Pages, upload its production artifact or deploy. On a
push to `main`, the workflow builds the same site and uses GitHub's official
`configure-pages`, `upload-pages-artifact` and `deploy-pages` actions. Only the
deployment job receives `pages: write` and `id-token: write`, and it depends on
both the docs build and repository checks.

A merge to `main` starts production deployment. Obtain separate merge/deployment
authority first. After the authorized merge, check the Actions deployment and
open the project URL, follow the bootstrap navigation and pinned source links,
then close issue #16 only after the deployed site is verified.

See [GitHub's custom Pages workflow instructions](https://docs.github.com/en/pages/getting-started-with-github-pages/using-custom-workflows-with-github-pages)
for the hosting requirements and [MkDocs configuration](https://www.mkdocs.org/user-guide/configuration/)
for site options.

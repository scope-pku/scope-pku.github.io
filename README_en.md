# SCOPE Group Web

[简体中文](README.md) | **English**

Bilingual Hugo website for the SCOPE Group at Peking University. Production
publishing runs through GitHub Pages by default; a small Python client for
Boda V12 is retained for fallback and emergency static-site releases.

## Highlights

- Bilingual Hugo site: English at `/`, Chinese at `/zh/`.
- Editorial research pages for research, publications, people, news, photos,
  teaching, and contact information.
- Shared content and data conventions for maintaining equivalent English and
  Chinese pages.
- Reproducible Python tooling managed with `uv` and `uv.lock`.
- GitHub Pages is the default production publisher; Boda remains available as a
  fallback and emergency release path.

## Quick start

### Prerequisites

Install:

- [Hugo Extended](https://gohugo.io/installation/)
- [uv](https://docs.astral.sh/uv/getting-started/installation/) if you need the
  Boda CLI or Python tests

On macOS, the shortest setup is:

```sh
brew install hugo
curl -LsSf https://astral.sh/uv/install.sh | sh
```

Verify the tools:

```sh
hugo version
uv --version
```

Hugo Extended is recommended because the site uses Hugo Pipes for CSS and
JavaScript assets. The Python package requires Python 3.13 or newer; uv can
install and manage it when needed.

### Preview the website

Run from the repository root:

```sh
hugo server --source site
```

Open the URL printed by Hugo, normally <http://localhost:1313/>. The English
site is at `/`; the Chinese site is at `/zh/`. Hugo watches the source files
and refreshes the browser after changes.

To include drafts and future-dated pages while developing:

```sh
hugo server --source site --buildDrafts --buildFuture
```

Stop the server with `Ctrl-C`.

### Build the website

Create a production build from the repository root:

```sh
hugo --source site --minify
```

The generated static site is written to `site/public/`. Do not deploy output
from `hugo server`; GitHub Pages performs the production build and deployment
when changes reach `main`. Use the checked Boda release builder only for a
fallback or emergency release.

## Common commands

```sh
# Preview the Hugo site.
hugo server --source site

# Build minified production output.
hugo --source site --minify

# Install locked runtime dependencies for the Boda CLI.
uv sync --locked --no-dev

# Install locked development dependencies and run all Python tests.
uv sync --locked --dev
uv run pytest tests

# (Fallback/emergency) Build and inspect a checked Boda release artifact.
tools/build_boda_release.sh
tools/bodacli plan dist/boda-site
tools/bodacli probe
```

The Boda commands require credentials only for operations that contact Boda.
Never commit credentials, OTP seeds, session cookies, or unfinished private
material. Uploads can become publicly reachable immediately; read the operator
guide before any write operation.

## Project structure

```text
.
├── site/                    # Hugo source and generated public/ output
│   ├── content/en/          # English content, served at /
│   ├── content/zh/          # Chinese content, served at /zh/
│   ├── layouts/             # Hugo templates and shortcodes
│   ├── assets/              # Hugo Pipes source assets
│   ├── static/              # Public files copied as-is
│   ├── data/                # Shared people, photo, and contact data
│   ├── i18n/                # Interface translations
│   └── hugo.yaml            # Hugo and language configuration
├── bodacli/                 # Boda V12 Python client
├── tools/                   # Release and CLI entry points
├── tests/                   # Python CLI and deployment tests
├── docs/                    # Developer, operator, and content guides
├── pyproject.toml           # Python project and dependency groups
└── uv.lock                  # Locked Python dependency resolution
```

The optional `source/xulm.pku.edu.cn/` directory is an immutable local snapshot
of the previous public site. It is read-only and excluded from Git.

## Contributing and content development

Before opening an issue or pull request, read [`CONTRIBUTING.md`](CONTRIBUTING.md) for submission requirements, Issue and PR checklists, and validation expectations.

Before changing public content, templates, styles, or components, read:

- [`AGENTS.md`](AGENTS.md) for repository rules and deployment boundaries.
- [`CONTRIBUTING.md`](CONTRIBUTING.md) for the Issue, PR, validation, and collaboration workflow.
- [`DESIGN.md`](DESIGN.md) for visual, editorial, bilingual, and accessibility
  requirements.
- [`docs/developer-guide.md`](docs/developer-guide.md) for the Hugo data model,
  templates, build checks, and validation workflow.
- [`docs/content-update-examples.md`](docs/content-update-examples.md) for
  copyable examples of common content changes.

For a bilingual page, keep the same relative path and `translationKey` in
`site/content/en/` and `site/content/zh/`. Keep facts, claims, caveats, links,
people, and dates equivalent; the wording does not need to be literal.

## Documentation map

- [`site/README.md`](site/README.md): short Hugo content and preview notes.
- [`docs/developer-guide.md`](docs/developer-guide.md): development workflow,
  architecture, and verification.
- [`docs/content-update-examples.md`](docs/content-update-examples.md):
  page-by-page content recipes.
- [`docs/operator-guide.md`](docs/operator-guide.md): GitHub Pages production
  publishing, plus Boda fallback operation, authentication, probing, deployment,
  and rollback.
- [`BODA_DEPLOYMENT.md`](BODA_DEPLOYMENT.md): deployment safety rules and
  release protocol.

## GitHub Pages

Pushes to `main` deploy the Hugo site to
<https://scope-pku.github.io/> through GitHub Actions. The workflow builds
`site/` and deploys the generated artifact; `site/public/` does not need to be
committed. See the repository settings and workflow files for CI details.

## Deployment boundary

Normal production publishing runs through GitHub Actions: after changes reach
`main`, `.github/workflows/pages.yml` builds and deploys GitHub Pages. Do not
manually upload `site/public/` or deploy production for an ordinary PR.

Boda is a fallback and emergency path, not the default publisher. Boda
deployment is a production write even when the target directory is unlinked or
named as a probe. If Boda is needed, read the operator guide, build the artifact,
run the read-only plan and probe, and obtain explicit authorization before any
deployment.

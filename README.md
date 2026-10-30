# version-agent

[![CI](https://github.com/nikhil2sharma/version-agent/actions/workflows/ci.yml/badge.svg)](https://github.com/nikhil2sharma/version-agent/actions/workflows/ci.yml)

Give it a CSV of tools and the versions you run, and it tells you which ones
are out of date. Claude looks up each tool's latest stable release with web
search, and the result is written to a CSV report.

Useful for keeping a team's toolchain or a server's install list current
without checking release pages by hand.

## Example

`examples/software.csv`:

```csv
sno,name,version,url
1,fastapi,0.110.0,https://pypi.org/project/fastapi/
4,terraform,1.5.0,https://github.com/hashicorp/terraform
6,python,3.11.4,https://www.python.org/downloads/
```

```bash
uv run version-agent examples/software.csv
```

The report adds two columns, `latest_version` and `status`:

| status | meaning |
| --- | --- |
| `UP_TO_DATE` | current version is the latest or newer |
| `OUTDATED` | a newer stable release exists |
| `NO_CURRENT_VERSION` | no version given in the input |
| `UNKNOWN` | latest version could not be found |
| `CHECK_MANUALLY` | version string isn't a standard version |

## How it works

- Each row becomes one question to Claude with the server-side web search tool
  enabled. If a `url` is given, Claude is told to check it first.
- Long searches can return `pause_turn`; the request is sent back so the model
  can finish.
- The reply is parsed for a version number and compared with
  [`packaging.version`](https://packaging.pypa.io/) (so `1.10.0` > `1.9.0`).
- A failed lookup marks that row `UNKNOWN` and the run continues.

## Setup

Requires Python 3.10+ and [uv](https://docs.astral.sh/uv/).

```bash
git clone https://github.com/nikhil2sharma/version-agent.git
cd version-agent
uv sync
cp .env.example .env    # add your ANTHROPIC_API_KEY
```

## Usage

```bash
uv run version-agent INPUT.csv [-o report.csv] [--model MODEL] [-v]
```

Input needs a `name` column. `version` and `url` are optional; any other
columns are kept in the report.

## Development

```bash
uv run pytest          # no API calls; the client is faked
uv run ruff check .
```

## Project layout

```
src/version_agent/
    checker.py   lookup, version parsing and comparison
    cli.py       CSV in/out and the command-line interface
tests/
examples/software.csv
```

## License

MIT

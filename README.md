# P18 - Verifiable Credentials

![The login page of our demo wallet app.](/demo/login.png)
![The home page of our  demo wallet app.](/demo/wallet.png)

## Installation

### TLS Certificates

In this repository, located at `vclib/(holder|issuer|verifier)/examples`, there are various `.crt` and `.key` files. **THESE ARE ILLUSTRATIVE EXAMPLES ONLY AND SHOULD NOT BE USED IN ANY PRODUCTION CONTEXT, These examples are _NOT_ treated as secret.** They exist to indicate how the repo should be set up. You *can* use these files to run this project locally, but you **SHOULD** provide your own beyond that purpose.

We have provided a script, `generate_certs.sh`, that will generate new certificates for you. This script requires `openssl` to be installed on your machine. It will generate new files at the appropriate locations for you.

### Steps to Install

1. Make a copy of `example.env` and name it `.env`, and either provide values for ports, or use the defaults. If you are only running the code through docker, and NOT locally developing, you do NOT need to set `CS3900_HOLDER_WALLET_PATH`. This will be set in the docker container independently.
2. From the root of the repository, run `docker-compose up --build`. This will build and start the containers.
3. Open the wallet application at `https://localhost:{CS3900_OWNER_UI_PORT}` in a Chromium-based browser (e.g. Google Chrome) Since the certificates are self-signed, unless you add them to your browser yourself, you will need to click past the invalid certificate warning.

NOTE: Restarting the docker containers will "wipe" any previous wallet data.

### Using the Examples

The Docker containers run a series of "example" apps/backends all built off our library. Demonstrating the interaction between these examples requires QR codes. We have provided some pre-generated examples in the [`docs`](docs/) directory at the root of this repository, but they have the default ports encoded within. If you wish to specify alternative ports, you will need to generate your own QR codes using a free tool online. The formats of these QR codes and further instructions on how to generate them can be found at [`docs/FORMAT.md`](demo/FORMAT.md).

Note that when 'adding' a new credential, you may be prevented from redirecting from the 'example' issuer form. If this happens, open the console to grab the redirect link.

## Local development

If you are planning to run unit tests on the code, you also need to make a copy of `example.env` and call it `.env` (`docker-compose` will work without doing this). The `.env` file contains environment variables that are passed to all tests and Docker containers, and because it is ignored by `.gitignore`, you can modify it as you like.

### Running tests

#### Testing the Python agents

To perform tests, run `pipenv shell` then `tox` from the root directory of this repo. You will need to have run `pipenv sync` at least once to set up the virtual environment. Any options you provide to `tox` using `--` (e.g. `tox -- --capture=no`) will be passed to pytest (e.g. `pytest --capture=no`).
In order to ensure that tox runs with the correct dependencies, run `pipenv requirements > requirements.txt` at the root to generate an up-to-date requirements.txt.

The `tox` tests will also run a linter (called `ruff`) to validate that all your code follows a certain style. If it fails your code, you will need to run `ruff` yourself. This involves running `ruff check --fix`.

Running these tests also generates an HTML coverage report in the `htmlcov/` folder.

#### Testing the React frontend

From the `owner-ui` directory, run `pnpm test` or `pnpm coverage`. You may need to run `pnpm install` first to install the frontend's dependencies if you haven't already.

### Serving agents

To start all the agents and network them together, run `docker compose up --build`.

While `docker-compose` is running, it is setup to automatically reload the server with any changes you make to the source code, so you don't have to restart `docker-compose` while you're developing code.

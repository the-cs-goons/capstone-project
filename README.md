[![Open in Visual Studio Code](https://classroom.github.com/assets/open-in-vscode-718a45dd9cf7e7f842a935f5ebbe5719a5e09af4491e668f4dbf3b35d5cca122.svg)](https://classroom.github.com/online_ide?assignment_repo_id=15170743&assignment_repo_type=AssignmentRepo)

## Local development

If you are planning to run unit tests on the code, you also need to make a copy of `example.env` and call it `.env` (`docker-compose` will work without doing this). The `.env` file contains environment variables that are passed to all tests and Docker containers, and because it is ignored by `.gitignore`, you can modify it as you like.

### Running tests

#### Testing the Python agents

To perform tests, run `pipenv shell` then `tox` from the root directory of this repo. You will need to have run `pipenv sync` at least once to set up the virtual environment. Any options you provide to `tox` using `--` (e.g. `tox -- --capture=no`) will be passed to pytest (e.g. `pytest --capture=no`).
In order to ensure that tox runs with the correct dependencies, run `pipenv requirements > requirements.txt` at the root to generate an up-to-date requirements.txt.

The `tox` tests will also run a linter (called `ruff`) to validate that all your code follows a certain style. If it fails your code, you will need to run `ruff` yourself. This involves running `ruff check --fix`.

Running these tests also generates an HTML coverage report in the `htmlcov/` folder.

#### Testing the React frontend

From the `owner-ui` directory, run `pnpm test`. You may need to run `pnpm install` first to install the frontend's dependencies if you haven't already.

### Serving agents

To start all the agents and network them together, run `docker compose up --build`.

While `docker-compose` is running, it is setup to automatically reload the server with any changes you make to the source code, so you don't have to restart `docker-compose` while you're developing code.

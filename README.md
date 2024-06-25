[![Open in Visual Studio Code](https://classroom.github.com/assets/open-in-vscode-718a45dd9cf7e7f842a935f5ebbe5719a5e09af4491e668f4dbf3b35d5cca122.svg)](https://classroom.github.com/online_ide?assignment_repo_id=15170743&assignment_repo_type=AssignmentRepo)

## Local development

This project requires you have **Python 3.12** and **Node.js 20** installed.

If you are planning to run unit tests on the code, you also need to make a copy of `example.env` and call it `.env`  (`docker-compose` will work without doing this). The `.env` file contains environment variables that are passed to all tests and Docker containers, and because it is ignored by `.gitignore`, you can modify it as you like.

### Running tests

#### Testing the Python agents

To install the Python testing framework, run `pip install tox`.

To perform tests, run `tox` from the root directory of this repo. Any options you provide to `tox` using `--` (e.g. `tox -- --capture=no`) will be passed to pytest (e.g. `pytest --capture=no`).

The `tox` tests will also run a linter (called `ruff`) to validate that all your code follows a certain style. If it fails your code, you will need to run `ruff` yourself. This involves running `pip install ruff` followed by `ruff check --fix`.

Running these tests also generates an HTML coverage report in the `htmlcov/` folder.

#### Testing the React frontend

From the `owner-ui` directory, run `yarn test`. You may need to run `yarn install` first to install the frontend's dependencies if you haven't already.

### Serving agents

To start all the agents and network them together, run `docker compose up --build`.

While `docker-compose` is running, it is setup to automatically reload the server with any changes you make to the source code, so you don't have to restart `docker-compose` while you're developing code.

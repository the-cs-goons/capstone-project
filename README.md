[![Open in Visual Studio Code](https://classroom.github.com/assets/open-in-vscode-718a45dd9cf7e7f842a935f5ebbe5719a5e09af4491e668f4dbf3b35d5cca122.svg)](https://classroom.github.com/online_ide?assignment_repo_id=15170743&assignment_repo_type=AssignmentRepo)

## Local development

This project requires you have **Python 3.12** and **Node.js 20** installed.

You also need to make a copy of `example.env` and call it `.env`. This file contains environment variables that are passed to all tests and Docker containers. You can then modify `.env` as you like (it is ignored by `.gitignore`).

### Running tests

#### Testing the Python agents

To install the Python testing framework, run `pip install tox`.

To perform tests, run `tox` from the root directory of this repo. Any options you provide to `tox` using `--` (e.g. `tox -- --capture=no`) will be passed to pytest (e.g. `pytest --capture=no`).

Running these tests also generates an HTML coverage report in the `htmlcov/` folder.

#### Testing the React frontend

From the `owner-ui` directory, run `npm test`. You may need to run `npm install` first to install the frontend's dependencies if you haven't already.

### Serving agents

To start all the agents and network them together, run `docker-compose up --build`.

While `docker-compose` is running, it is setup to automatically reload the server with any changes you make to the source code, so you don't have to restart `docker-compose` while you're developing code.

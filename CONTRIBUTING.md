# Contributing to FEAS 2.0

First off, thank you for considering contributing to the Forensic Evidence Acquisition System (FEAS)! 

As an enterprise-grade open-source forensic platform, we rely on community contributions to expand our capabilities, fix bugs, and ensure the system meets the rigorous standards required by digital forensic investigators and red teamers.

## Code of Conduct

By participating in this project, you agree to abide by our [Code of Conduct](CODE_OF_CONDUCT.md). We expect all contributors to maintain a professional and welcoming environment.

## How Can I Contribute?

### Reporting Bugs

Before submitting a bug report, please check the existing issues to ensure it hasn't already been reported. When opening a new issue, please include:

* A clear and descriptive title.
* The exact steps to reproduce the issue.
* Expected vs. actual behavior.
* System information (OS, Python version, Node.js version, Docker version if applicable).
* Logs from the backend (`backend/logs/`) or frontend console if available.

### Suggesting Enhancements

If you have an idea for a new feature or an improvement to an existing one:

* Open a "Feature Request" issue.
* Clearly describe the use case and how it benefits forensic investigators or red teamers.
* For significant architectural changes, please submit an issue for discussion *before* writing code.

### Pull Requests

1. **Fork the repository** and create your branch from `main`.
2. **Setup your development environment** (see `README.md` Quick Start).
3. **Write clean, documented code.** Follow PEP 8 for Python and standard ESLint rules for React.
4. **Add or update tests** where applicable (especially for new services in the backend).
5. **Update documentation** if your changes affect the API, architecture, or setup processes.
6. **Ensure the test suite passes** before submitting.
7. **Submit the PR** with a comprehensive description of the changes.

## Development Guidelines

### Backend (Python/FastAPI)

* **Type Hinting**: All new Python code must use type hints.
* **Docstrings**: Use Google-style docstrings for all new functions, methods, and classes.
* **Dependencies**: If adding a new dependency, ensure it is strictly necessary and add it to `requirements.txt`.
* **Database Changes**: If you modify `sql_models.py`, you must generate an Alembic migration script.

### Frontend (React)

* **Components**: Use functional components and React Hooks.
* **Styling**: Use `styled-components`. Do not use inline styles unless absolutely necessary for dynamic values.
* **State Management**: Use `Zustand` for global state and `React Query` for server state/API fetching.

## Security Contributions

If you find a security vulnerability, **DO NOT open a public issue**. Please refer to our [Security Policy](SECURITY.md) for instructions on how to responsibly disclose the vulnerability.

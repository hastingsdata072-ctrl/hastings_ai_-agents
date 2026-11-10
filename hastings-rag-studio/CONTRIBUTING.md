# Contributing to Hastings RAG Studio

Thank you for your interest in contributing!

## Development Setup

1. Fork the repository
2. Clone your fork
3. Follow the [Quick Start](README.md#-quick-start) setup
4. Create a feature branch: `git checkout -b feature/your-feature-name`

## Code Standards

- Python type hints throughout
- Module-level docstrings on all files
- Follow existing patterns — read the relevant module before adding to it
- No hardcoded secrets, API keys, or connection strings

## Submitting Changes

1. Test your changes locally
2. Run `python tests/test_db_connection.py` — all checks must pass
3. Open a pull request with a clear description of what changed and why

## Reporting Issues

Open a GitHub Issue with:
- What you expected to happen
- What actually happened
- Steps to reproduce
- Your OS and Python version

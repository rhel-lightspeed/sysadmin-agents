# Contributing to Sysadmin Agents

Thank you for your interest in contributing to Sysadmin Agents! This document provides guidelines and instructions for contributing.

## Code of Conduct

Please be respectful and constructive in all interactions. We welcome contributors of all backgrounds and experience levels.

## Getting Started

### Prerequisites

- Python 3.10 or later
- Git
- A Gemini API key (for testing agents)
- SSH access to a test Linux/RHEL system (optional, for integration testing)

### Development Setup

1. **Fork and clone the repository**

   ```bash
   git clone https://github.com/your-username/sysadmin-agents.git
   cd sysadmin-agents
   ```

2. **Create a virtual environment**

   ```bash
   python -m venv .venv
   source .venv/bin/activate
   ```

3. **Install dependencies**

   ```bash
   pip install -e ".[dev]"
   ```

4. **Set up environment variables**

   ```bash
   # Copy the example config
   cp deploy/config.env.example .env
   # Edit .env with your settings (at minimum, set GOOGLE_API_KEY and LINUX_MCP_USER)
   ```

## Development Workflow

### Branch Naming

Use descriptive branch names:

- `feature/agent-<name>` - For new agents
- `feature/<description>` - For new features
- `fix/<description>` - For bug fixes
- `docs/<description>` - For documentation updates

### Making Changes

1. **Create a feature branch**

   ```bash
   git checkout -b feature/agent-my-new-agent
   ```

2. **Make your changes**

   - Follow the code style (enforced by ruff)
   - Add tests for new functionality
   - Update documentation as needed

3. **Run tests and linting**

   ```bash
   # Run linting
   ruff check .
   ruff format .

   # Run tests
   pytest
   ```

4. **Commit your changes**

   ```bash
   git add .
   git commit -m "feat: add my-new-agent for X functionality"
   ```

   Follow [Conventional Commits](https://www.conventionalcommits.org/):
   - `feat:` - New features
   - `fix:` - Bug fixes
   - `docs:` - Documentation changes
   - `test:` - Adding tests
   - `refactor:` - Code refactoring

5. **Push and create a Pull Request**

   ```bash
   git push origin feature/agent-my-new-agent
   ```

   Then create a PR on GitHub.

## Code Style

### Python

- Follow PEP 8 (enforced by ruff)
- Use type hints where practical
- Write docstrings for public functions and classes
- Maximum line length: 100 characters

### YAML Configuration

- Use 2-space indentation
- Include comments explaining non-obvious settings
- Keep prompts readable with proper line breaks

## Testing

### Running Tests

```bash
# Run all tests
pytest

# Run specific test file
pytest tests/test_rca_agent.py

# Run with coverage
pytest --cov=agents
```

### Writing Tests

- Place tests in `tests/` directory
- Name test files `test_<module>.py`
- Use descriptive test names: `test_agent_loads_config_correctly`
- Mock external dependencies (MCP server, SSH connections)

## Adding New Agents

See [ADDING_AGENTS.md](ADDING_AGENTS.md) for detailed instructions on creating new agents.

Quick overview:

1. Create directory: `agents/<agent_name>/`
2. Add files: `__init__.py`, `agent.py`, `root_agent.yaml`
3. Define agent in `root_agent.yaml` with YAML-driven configuration
4. Add tests in `tests/test_<agent_name>.py`

## Pull Request Guidelines

### Before Submitting

- [ ] Tests pass locally
- [ ] Linting passes (`ruff check .`)
- [ ] Code is formatted (`ruff format .`)
- [ ] Documentation is updated
- [ ] Commit messages follow conventions

### PR Description

Include:
- What the change does
- Why the change is needed
- How to test the change
- Any breaking changes

### Review Process

1. Automated checks run (linting, tests)
2. Maintainer reviews code
3. Address feedback if needed
4. Maintainer merges when approved

## Reporting Issues

### Bug Reports

Include:
- Steps to reproduce
- Expected vs actual behavior
- Python version, OS
- Relevant logs or error messages

### Feature Requests

Include:
- Use case description
- Proposed solution
- Alternatives considered

## Getting Help

- Open an issue for questions
- Tag issues with appropriate labels
- Be patient - maintainers are volunteers

## License

By contributing, you agree that your contributions will be licensed under the Apache-2.0 License.

## Thank You!

Your contributions help make Linux system administration easier for everyone.


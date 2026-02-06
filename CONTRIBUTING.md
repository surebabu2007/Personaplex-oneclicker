# Contributing to PersonaPlex

Thank you for your interest in contributing to PersonaPlex! This document provides guidelines for contributing to the project.

## Table of Contents

- [Code of Conduct](#code-of-conduct)
- [Getting Started](#getting-started)
- [How to Contribute](#how-to-contribute)
- [Development Setup](#development-setup)
- [Pull Request Process](#pull-request-process)
- [Reporting Issues](#reporting-issues)

## Code of Conduct

By participating in this project, you agree to maintain a respectful and inclusive environment. Please:

- Be respectful and constructive in discussions
- Welcome newcomers and help them get started
- Focus on what is best for the community
- Show empathy towards other community members

## Getting Started

1. **Fork the repository** on GitHub
2. **Clone your fork** locally:
   ```bash
   git clone https://github.com/YOUR_USERNAME/personaplex.git
   cd personaplex
   ```
3. **Add the upstream remote**:
   ```bash
   git remote add upstream https://github.com/NVIDIA/personaplex.git
   ```

## How to Contribute

### Types of Contributions

We welcome several types of contributions:

- **Bug fixes**: Fix issues reported in the issue tracker
- **Documentation**: Improve or add documentation
- **Features**: Add new features (please discuss first)
- **Tests**: Add or improve test coverage
- **Performance**: Optimize existing code

### Before You Start

1. Check the [issue tracker](https://github.com/NVIDIA/personaplex/issues) for existing issues
2. For new features, open an issue first to discuss the proposal
3. Make sure your contribution aligns with the project's goals

## Development Setup

### Prerequisites

- Python 3.10+
- NVIDIA GPU with CUDA support (for full functionality)
- Git

### Setting Up Your Development Environment

```bash
# Create a virtual environment
python -m venv venv

# Activate it (Windows)
.\venv\Scripts\activate

# Activate it (Linux/macOS)
source venv/bin/activate

# Install in development mode
pip install -e moshi/.

# Install development dependencies
pip install accelerate pytest black isort
```

### Running Tests

```bash
# Run the verification script
python verify_project.py

# Test that imports work
python -c "import moshi; print('OK')"
```

### Code Style

- Follow PEP 8 guidelines
- Use meaningful variable and function names
- Add docstrings to functions and classes
- Keep functions focused and concise

## Pull Request Process

1. **Create a feature branch**:
   ```bash
   git checkout -b feature/your-feature-name
   ```

2. **Make your changes**:
   - Write clear, concise commit messages
   - Keep commits focused on a single change
   - Add tests if applicable

3. **Keep your branch updated**:
   ```bash
   git fetch upstream
   git rebase upstream/main
   ```

4. **Push and create a PR**:
   ```bash
   git push origin feature/your-feature-name
   ```
   Then create a Pull Request on GitHub.

5. **PR Requirements**:
   - Clear description of changes
   - Reference any related issues
   - All tests passing
   - Documentation updated if needed

## Reporting Issues

When reporting issues, please include:

### For Bug Reports

- **Environment**: OS, Python version, GPU model, CUDA version
- **Steps to reproduce**: Detailed steps to trigger the issue
- **Expected behavior**: What you expected to happen
- **Actual behavior**: What actually happened
- **Error messages**: Full error logs/tracebacks
- **Screenshots**: If applicable

### For Feature Requests

- **Use case**: Why is this feature needed?
- **Proposed solution**: How should it work?
- **Alternatives considered**: Other approaches you've thought about

## Questions?

- Open a [Discussion](https://github.com/NVIDIA/personaplex/discussions) for general questions
- Join our [Discord](https://discord.gg/5jAXrrbwRb) for real-time chat
- Check existing issues before creating new ones

## License

By contributing, you agree that your contributions will be licensed under the same license as the project (MIT License for code, NVIDIA Open Model License for weights).

---

Thank you for contributing to PersonaPlex!

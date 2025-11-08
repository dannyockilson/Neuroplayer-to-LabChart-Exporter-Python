# Contributing to NDF LabChart Exporter

Thank you for your interest in contributing to the NDF LabChart Exporter! This project helps researchers convert EEG data from Neuroplayer NDF format to LabChart-compatible files.

## Table of Contents

- [Code of Conduct](#code-of-conduct)
- [Getting Started](#getting-started)
- [How to Contribute](#how-to-contribute)
- [Development Setup](#development-setup)
- [Coding Standards](#coding-standards)
- [Testing](#testing)
- [Submitting Changes](#submitting-changes)
- [Issue Guidelines](#issue-guidelines)
- [Documentation](#documentation)

## Code of Conduct

This project follows a standard code of conduct to ensure a welcoming environment for all contributors. Please be respectful, constructive, and inclusive in all interactions.

## Getting Started

### Prerequisites

- Python 3.6 or higher
- Git
- A text editor or IDE of your choice

### First Steps

1. Fork the repository on GitHub
2. Clone your fork locally:
   ```bash
   git clone https://github.com/yourusername/ndf-labchart.git
   cd ndf-labchart
   ```
3. Create a branch for your changes:
   ```bash
   git checkout -b feature/your-feature-name
   ```

## How to Contribute

### Types of Contributions

We welcome several types of contributions:

- **Bug fixes** - Fix issues with existing functionality
- **Features** - Add new capabilities (please discuss in an issue first)
- **Documentation** - Improve docs, examples, or code comments
- **Testing** - Add test cases or improve test coverage
- **Performance** - Optimize existing code
- **Compatibility** - Support new file formats or transmitter types

### Areas Where Help is Needed

- Support for additional transmitter types and voltage ranges
- Performance optimization for large NDF files
- Additional output formats (CSV, MATLAB, etc.)
- Cross-platform testing (Windows, macOS, Linux)
- Documentation improvements for non-technical users
- Test data validation and edge case handling

## Development Setup

### Setting Up Your Environment

1. Create a virtual environment (recommended):
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

2. Install development dependencies:
   ```bash
   pip install -r requirements.txt  # If this file exists
   ```

3. Install the package in development mode:
   ```bash
   pip install -e .
   ```

### Testing Your Setup

1. Run the basic functionality test:
   ```bash
   python ndf_to_text_converter.py --help
   python bulk_converter.py --help
   ```

2. Test with mock data:
   ```bash
   python bulk_converter.py mock-inputs
   ```

## Coding Standards

### Python Style Guide

- Follow [PEP 8](https://pep8.org/) for Python code style
- Use meaningful variable and function names
- Maximum line length: 88 characters (Black formatter standard)
- Use type hints where possible

### Code Formatting

We use automated formatting tools:

```bash
# Install formatting tools
pip install black isort

# Format your code
black .
isort .
```

### Type Checking

Use type hints and mypy for type checking:

```bash
pip install mypy
mypy *.py
```

### Documentation Style

- Use docstrings for all functions and classes
- Follow [Google docstring style](https://google.github.io/styleguide/pyguide.html#38-comments-and-docstrings)
- Update README.md for user-facing changes

Example:
```python
def convert_signal(data: List[int], sample_rate: float) -> List[Tuple[float, List[int]]]:
    """Convert raw signal data to time intervals.

    Args:
        data: List of 16-bit sample values
        sample_rate: Sampling rate in Hz

    Returns:
        List of (timestamp, samples) tuples for each interval

    Raises:
        ValueError: If sample_rate is not positive
    """
```

## Testing

### Running Tests

```bash
# Run all tests
python -m pytest

# Run specific test file
python -m pytest test_ndf_reader.py

# Run with coverage
python -m pytest --cov=.
```

### Writing Tests

- Add tests for new functionality
- Use descriptive test names
- Test both success and failure cases
- Include tests with real data when possible

Example test structure:
```python
def test_ndf_reader_with_valid_file():
    """Test NDF reader with a valid input file."""
    reader = NDFReader('test_data.ndf')
    channels = reader.get_available_channels()
    assert len(channels) > 0
    assert all(isinstance(ch, int) for ch in channels)
```

## Submitting Changes

### Commit Guidelines

- Use clear, descriptive commit messages
- Start with a verb in present tense ("Add", "Fix", "Update")
- Keep the first line under 50 characters
- Add details in the body if needed

Good examples:
```
Add support for A3028C transmitters

Fix timestamp calculation in NDF reader

Update documentation for new output formats
```

### Pull Request Process

1. **Before submitting:**
   - Run tests and ensure they pass
   - Update documentation if needed
   - Add tests for new features
   - Check code formatting

2. **Pull request description:**
   - Clearly describe what changes were made
   - Reference any related issues
   - Include testing instructions
   - Note any breaking changes

3. **Review process:**
   - Address reviewer feedback promptly
   - Make requested changes in new commits
   - Keep discussions focused and constructive

### Pull Request Template

```markdown
## Description
Brief description of changes made.

## Type of Change
- [ ] Bug fix
- [ ] New feature
- [ ] Documentation update
- [ ] Performance improvement
- [ ] Other (please describe):

## Testing
- [ ] Tests pass locally
- [ ] Added tests for new functionality
- [ ] Tested with real NDF files

## Checklist
- [ ] Code follows project style guidelines
- [ ] Self-review completed
- [ ] Documentation updated
- [ ] No breaking changes (or clearly documented)
```

## Issue Guidelines

### Reporting Bugs

Include the following information:

- **Description:** Clear description of the issue
- **Steps to reproduce:** Detailed steps to recreate the problem
- **Expected behavior:** What you expected to happen
- **Actual behavior:** What actually happened
- **Environment:** Python version, OS, file types being processed
- **Error messages:** Full error text if applicable

### Feature Requests

For new features:

- **Use case:** Describe why this feature would be useful
- **Proposed solution:** How you envision it working
- **Alternatives:** Other approaches you've considered
- **Implementation:** Are you willing to implement it yourself?

### Questions and Support

- Check the README.md and existing issues first
- Use clear, descriptive titles
- Provide context about what you're trying to accomplish
- Include relevant code snippets or error messages

## Documentation

### User Documentation

- Keep README.md and QUICK_START.md up to date
- Add examples for new features
- Use clear, non-technical language where appropriate
- Test documentation with real use cases

### Code Documentation

- Document all public functions and classes
- Explain complex algorithms or data processing
- Include usage examples in docstrings
- Comment non-obvious code sections

## Research Data Considerations

### Data Privacy

- Never commit real research data to the repository
- Use only publicly available demo data for testing
- Be mindful of data privacy in examples and tests

### Scientific Accuracy

- Ensure signal processing maintains data integrity
- Validate against known good outputs when possible
- Consider the impact of changes on research reproducibility
- Document any assumptions about data formats or ranges

## Getting Help

- **Issues:** Open a GitHub issue for bugs or feature requests
- **Questions:** Use GitHub Discussions for general questions
- **Email:** Contact the maintainers for sensitive issues

## Recognition

Contributors will be acknowledged in:
- CONTRIBUTORS.md file
- Release notes for significant contributions
- README.md for major features or fixes

Thank you for helping make this tool better for the research community!
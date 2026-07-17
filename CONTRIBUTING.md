# Contributing to OpsDeck

Thank you for considering contributing to OpsDeck! 🎉

## Code of Conduct

Be respectful, inclusive, and constructive. We're here to build something awesome together.

## How Can I Contribute?

### Reporting Bugs

**Before submitting:**
- Check if the bug is already reported in [Issues](https://github.com/rasinmuhammed/opsdeck/issues)
- Try the latest version to see if it's already fixed

**When reporting:**
```markdown
**Environment:**
- OS: (e.g., macOS 14.1, Ubuntu 22.04)
- Python version: (e.g., 3.11.5)
- FastAPI Shadow Admin version: (e.g., 0.1.0)

**Steps to Reproduce:**
1. Install with `pip install opsdeck`
2. Create this model: ...
3. Register with: ...
4. Error occurs when: ...

**Expected behavior:**
What you expected to happen

**Actual behavior:**
What actually happened (include error messages/stack traces)

**Additional context:**
Any other relevant information
```

### Suggesting Features

We love new ideas! Open an issue with:
- **Problem**: What problem does this solve?
- **Solution**: Your proposed solution
- **Alternatives**: Other solutions you considered
- **Examples**: Code examples of usage

### Pull Requests

#### Quick Checklist
- [ ] Tests pass (`pytest`)
- [ ] Code formatted (`black . && ruff check --fix .`)
- [ ] Type hints added (where applicable)
- [ ] Documentation updated (if needed)
- [ ] Commit messages are clear

#### Step-by-Step

**1. Fork & Clone**
```bash
git clone https://github.com/rasinmuhammed/opsdeck.git
cd opsdeck
```

**2. Set Up Environment**
```bash
# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -e ".[dev]"
```

**3. Create Branch**
```bash
git checkout -b feature/your-amazing-feature
# or
git checkout -b fix/issue-123
```

**4. Make Changes**
- Write clear, readable code
- Add type hints
- Include docstrings
- Follow existing code style

**5. Run Tests**
```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=fastapi_shadcn_admin --cov-report=html

# Run specific test
pytest tests/test_security.py::TestURLSigner

# Format code
black .
ruff check --fix .
```

**6. Commit**
```bash
git add .
git commit -m "feat: add amazing feature"
# or
git commit -m "fix: resolve issue #123"
```

**Commit Message Format:**
- `feat:` New feature
- `fix:` Bug fix
- `docs:` Documentation only
- `style:` Code style (formatting, no logic change)
- `refactor:` Code restructuring
- `test:` Adding or updating tests
- `chore:` Maintenance tasks

**7. Push & PR**
```bash
git push origin feature/your-amazing-feature
```

Then open a Pull Request on GitHub with:
- Clear title
- Description of changes
- Related issues (if any)
- Screenshots (if UI changes)

## Development Guide

### Project Structure
```
fastapi_shadcn_admin/
├── core/          # Core functionality
│   ├── admin.py   # Main ShadcnAdmin class
│   ├── router.py  # Route handlers
│   ├── crud.py    # Database operations
│   └── ...
├── auth/          # Authentication & authorization
├── audit/         # Audit logging
├── templates/     # Jinja2 templates
└── tests/         # Test suite
```

### Code Style

**We use:**
- **black** for formatting (line length 88)
- **ruff** for linting
- **mypy** for type checking (aspirational)

**Example:**
```python
from __future__ import annotations

from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from sqlalchemy.ext.asyncio import AsyncSession


async def example_function(
    session: "AsyncSession",
    data: dict[str, Any],
) -> list[str]:
    """
    Clear, concise docstring.
    
    Args:
        session: Database session
        data: Input data
        
    Returns:
        List of processed items
        
    Note:
        Explain any non-obvious behavior
    """
    # Implementation
    pass
```

### Testing Guidelines

**Test Structure:**
```python
import pytest
from fastapi.testclient import TestClient


class TestYourFeature:
    """Group related tests."""
    
    @pytest.fixture
    def client(self):
        """Setup test client."""
        app = FastAPI()
        # ... setup
        return TestClient(app)
    
    def test_happy_path(self, client):
        """Test expected behavior."""
        response = client.get("/endpoint")
        assert response.status_code == 200
    
    def test_edge_case(self, client):
        """Test edge cases."""
        response = client.get("/endpoint?empty=true")
        assert response.status_code == 200
        assert response.json() == []
    
    def test_error_handling(self, client):
        """Test error scenarios."""
        response = client.get("/endpoint/invalid")
        assert response.status_code == 404
```

**What to Test:**
- ✅ Happy path
- ✅ Edge cases (empty, None, max values)
- ✅ Error handling
- ✅ Security scenarios
- ✅ Integration between components

### Documentation

**Code Documentation:**
- All public functions/classes need docstrings
- Use Google style docstrings
- Include examples for complex functionality

**README Updates:**
- Update README.md for new features
- Add examples to demonstrate usage
- Update comparison table if applicable

**Example Documentation:**
```python
def my_feature(param: str, option: bool = False) -> dict:
    """
    Short, clear description.
    
    Longer explanation if needed. What does this do and why?
    
    Args:
        param: What this parameter does
        option: What this option controls (default: False)
        
    Returns:
        Dictionary containing:
        - 'result': The processed result
        - 'status': Success status
        
    Raises:
        ValueError: When param is empty
        
    Example:
        >>> result = my_feature("test", option=True)
        >>> print(result['status'])
        'success'
        
    Note:
        Any important caveats or gotchas
    """
```

## Areas We Need Help

### High Priority
- 🧪 **Test Coverage**: Get to 100% from current 90%
- 📖 **Documentation**: API reference, tutorials, guides
- 🐛 **Bug Fixes**: Check [Issues](https://github.com/rasinmuhammed/opsdeck/issues)

### Features
- ✨ **Inline Editing**: Edit fields directly in list view
- 🔍 **Advanced Filters**: Complex filtering UI
- 📊 **Export**: Excel, PDF export functionality
- 🌍 **i18n**: Internationalization support
- 🎨 **Themes**: Additional color schemes

### Nice to Have
- 📱 **Mobile Optimization**: Better mobile experience
- ⚡ **Performance**: Optimization opportunities
- 🔌 **Plugins**: Plugin system architecture
- 📹 **Tutorials**: Video walkthroughs

## Questions?

Don't hesitate to ask! Open an issue labeled `question` or start a discussion.

## Recognition

Contributors will be:
- Listed in README
- Mentioned in release notes
- Given proper credit in commit history

Thank you for contributing! 🙏

---

**Happy coding!** 🚀

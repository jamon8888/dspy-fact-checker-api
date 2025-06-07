# Contributing to DSPy-Enhanced Fact-Checker API Platform

Thank you for your interest in contributing to the DSPy-Enhanced Fact-Checker API Platform! We welcome contributions from the community and are grateful for your support.

## 🌟 **Ways to Contribute**

### **Code Contributions**
- **Bug fixes** - Help us fix issues and improve stability
- **Feature development** - Add new features and capabilities
- **Performance improvements** - Optimize existing functionality
- **Documentation** - Improve and expand documentation
- **Testing** - Add tests and improve test coverage

### **Non-Code Contributions**
- **Bug reports** - Report issues and problems
- **Feature requests** - Suggest new features and improvements
- **Documentation improvements** - Fix typos, clarify instructions
- **Community support** - Help other users in discussions
- **Feedback** - Provide feedback on usability and design

## 🚀 **Getting Started**

### **Development Setup**

1. **Fork the repository**
   ```bash
   # Fork on GitHub, then clone your fork
   git clone https://github.com/YOUR_USERNAME/fact-checker.git
   cd fact-checker
   ```

2. **Set up development environment**
   ```bash
   # Create virtual environment
   python -m venv venv
   source venv/bin/activate  # Linux/Mac
   # or
   venv\Scripts\activate     # Windows
   
   # Install dependencies
   pip install -r requirements.txt
   pip install -r requirements-testing.txt
   ```

3. **Configure environment**
   ```bash
   # Copy environment template
   cp .env.production .env
   
   # Edit with your development settings
   nano .env
   ```

4. **Initialize database**
   ```bash
   python scripts/init_database.py
   ```

5. **Run tests**
   ```bash
   pytest
   ```

6. **Start development server**
   ```bash
   uvicorn app.main:app --reload
   ```

### **Development Workflow**

1. **Create a feature branch**
   ```bash
   git checkout -b feature/your-feature-name
   ```

2. **Make your changes**
   - Write code following our style guidelines
   - Add tests for new functionality
   - Update documentation as needed

3. **Test your changes**
   ```bash
   # Run all tests
   pytest
   
   # Run specific test categories
   pytest tests/test_your_feature.py
   
   # Check code coverage
   pytest --cov=app tests/
   
   # Run production readiness test
   python scripts/production_readiness_test.py
   ```

4. **Commit your changes**
   ```bash
   git add .
   git commit -m "feat: add your feature description"
   ```

5. **Push to your fork**
   ```bash
   git push origin feature/your-feature-name
   ```

6. **Create a Pull Request**
   - Go to GitHub and create a PR from your fork
   - Fill out the PR template
   - Wait for review and address feedback

## 📝 **Code Style Guidelines**

### **Python Code Style**
- **PEP 8** - Follow Python style guidelines
- **Type hints** - Use type annotations for all functions
- **Docstrings** - Document all classes and functions
- **Black** - Use Black for code formatting
- **isort** - Use isort for import sorting

### **Code Formatting**
```bash
# Format code
black app/
isort app/

# Check formatting
black --check app/
isort --check-only app/

# Lint code
flake8 app/
mypy app/
```

### **Naming Conventions**
- **Variables**: `snake_case`
- **Functions**: `snake_case`
- **Classes**: `PascalCase`
- **Constants**: `UPPER_SNAKE_CASE`
- **Files**: `snake_case.py`

### **Documentation Style**
- **Docstrings**: Use Google-style docstrings
- **Comments**: Clear, concise explanations
- **README**: Update relevant sections
- **API docs**: Update OpenAPI documentation

## 🧪 **Testing Guidelines**

### **Test Requirements**
- **Unit tests** for all new functions
- **Integration tests** for API endpoints
- **Test coverage** should not decrease
- **All tests** must pass before merging

### **Test Structure**
```python
def test_function_name():
    """Test description."""
    # Arrange
    input_data = "test input"
    expected_result = "expected output"
    
    # Act
    result = function_to_test(input_data)
    
    # Assert
    assert result == expected_result
```

### **Test Categories**
- **Unit tests**: `tests/unit/`
- **Integration tests**: `tests/integration/`
- **API tests**: `tests/api/`
- **OCR tests**: `tests/ocr/`
- **Performance tests**: `tests/performance/`

## 📋 **Pull Request Guidelines**

### **PR Requirements**
- **Clear description** of changes
- **Tests** for new functionality
- **Documentation** updates
- **No breaking changes** without discussion
- **Passing CI** checks

### **PR Template**
```markdown
## Description
Brief description of changes

## Type of Change
- [ ] Bug fix
- [ ] New feature
- [ ] Breaking change
- [ ] Documentation update

## Testing
- [ ] Unit tests added/updated
- [ ] Integration tests added/updated
- [ ] All tests pass
- [ ] Manual testing completed

## Documentation
- [ ] Code comments updated
- [ ] README updated
- [ ] API documentation updated
- [ ] Changelog updated

## Checklist
- [ ] Code follows style guidelines
- [ ] Self-review completed
- [ ] No breaking changes
- [ ] Tests added for new functionality
```

### **Review Process**
1. **Automated checks** - CI/CD pipeline runs
2. **Code review** - Maintainer reviews code
3. **Testing** - Manual testing if needed
4. **Approval** - PR approved by maintainer
5. **Merge** - Changes merged to main branch

## 🐛 **Bug Reports**

### **Before Reporting**
- **Search existing issues** to avoid duplicates
- **Test with latest version** to ensure bug still exists
- **Gather information** about your environment

### **Bug Report Template**
```markdown
## Bug Description
Clear description of the bug

## Steps to Reproduce
1. Step one
2. Step two
3. Step three

## Expected Behavior
What should happen

## Actual Behavior
What actually happens

## Environment
- OS: [e.g., Ubuntu 20.04]
- Python: [e.g., 3.11.2]
- Version: [e.g., 1.0.0]

## Additional Context
Any other relevant information
```

## 💡 **Feature Requests**

### **Feature Request Template**
```markdown
## Feature Description
Clear description of the proposed feature

## Problem Statement
What problem does this solve?

## Proposed Solution
How should this feature work?

## Alternatives Considered
Other solutions you've considered

## Additional Context
Any other relevant information
```

## 🔒 **Security**

### **Security Issues**
- **Do not** open public issues for security vulnerabilities
- **Email** security@fact-checker.com for security issues
- **Include** detailed information about the vulnerability
- **Wait** for response before public disclosure

### **Security Guidelines**
- **No hardcoded secrets** in code
- **Validate all inputs** thoroughly
- **Use secure defaults** for configurations
- **Follow security best practices**

## 📞 **Community**

### **Communication Channels**
- **GitHub Issues** - Bug reports and feature requests
- **GitHub Discussions** - General discussions and questions
- **Email** - Direct communication with maintainers

### **Code of Conduct**
- **Be respectful** and inclusive
- **Be constructive** in feedback
- **Be patient** with new contributors
- **Follow** our community guidelines

## 🏆 **Recognition**

### **Contributors**
All contributors will be recognized in:
- **README** contributors section
- **CHANGELOG** for significant contributions
- **Release notes** for major features

### **Maintainers**
Current maintainers:
- **Core Team** - Overall project maintenance
- **OCR Team** - OCR integration and optimization
- **API Team** - API development and documentation
- **DevOps Team** - Infrastructure and deployment

## 📚 **Resources**

### **Documentation**
- [**Installation Guide**](INSTALLATION_NEW.md)
- [**API Documentation**](docs/API_DOCUMENTATION.md)
- [**Deployment Guide**](docs/DEPLOYMENT_GUIDE.md)
- [**Configuration Guide**](docs/CONFIGURATION_GUIDE.md)

### **Development Tools**
- **IDE**: VS Code, PyCharm, or your preferred editor
- **Testing**: pytest for testing framework
- **Formatting**: Black and isort for code formatting
- **Linting**: flake8 and mypy for code quality
- **Documentation**: Sphinx for documentation generation

### **Learning Resources**
- **FastAPI**: https://fastapi.tiangolo.com/
- **PostgreSQL**: https://www.postgresql.org/docs/
- **Redis**: https://redis.io/documentation
- **Docker**: https://docs.docker.com/
- **Kubernetes**: https://kubernetes.io/docs/

## 🙏 **Thank You**

Thank you for contributing to the DSPy-Enhanced Fact-Checker API Platform! Your contributions help make this project better for everyone.

---

**Questions?** Feel free to reach out through GitHub Issues or Discussions!

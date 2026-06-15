# Contributing to turo-onboard

Thank you for your interest in contributing to **turo-onboard**! This guide will help you get started.

---

## How to contribute

### 1. Fork the repository

Click the **Fork** button on the [turo-onboard repository](https://github.com/whozahm3d/turo-onboard) to create your own copy.

```bash
git clone https://github.com/YOUR-USERNAME/turo-onboard.git
cd turo-onboard
```

### 2. Create a feature branch

Always work on a new branch for your changes:

```bash
git checkout -b feature/your-feature-name
```

Use descriptive branch names:
- `feature/improve-scraper` for new features
- `fix/scraper-cloudflare-bug` for bug fixes
- `docs/update-readme` for documentation

### 3. Set up your environment

Install dependencies and configure your environment:

```bash
pip install -r requirements.txt
playwright install chromium
cp .env.example .env
# Add your Cohere API key to .env
```

### 4. Make your changes

- Keep commits focused and atomic
- Write clear commit messages (e.g., "Add retry logic to scraper for Cloudflare challenges")
- Test your changes locally before pushing

```bash
# Test the scraper
python scraper.py https://turo.com/us/en/car-rental/...

# Test the pipeline
python pipeline.py

# Run the UI
streamlit run app.py
```

### 5. Push to your fork

```bash
git push origin feature/your-feature-name
```

### 6. Open a Pull Request

Go to the [original repository](https://github.com/whozahm3d/turo-onboard) and click **New Pull Request**. 

**Please include:**
- A clear title and description of your changes
- Why the change is needed
- Any testing you've done
- Links to related issues (if applicable)

---

## What we're looking for

### High-impact contributions
- **Scraper improvements** — better data extraction, handling edge cases, bypassing Cloudflare more reliably
- **AI pipeline enhancements** — smarter prompt engineering, structured output validation, error handling
- **UI/UX** — Streamlit refinements, better error messages, output formatting
- **Documentation** — clearer setup instructions, API examples, troubleshooting guides
- **Bug fixes** — reproducible issues with clear steps to fix

### Guidelines
- Keep PRs focused (one feature or fix per PR)
- Follow the existing code style
- Add comments for complex logic
- Test edge cases (e.g., missing fields, malformed URLs, API rate limits)
- Update `README.md` if you change user-facing behavior

---

## Code style

This project uses:
- **Python 3.9+** with standard library conventions
- **No strict linter** — keep it readable and consistent with the existing codebase
- **Comments** — explain *why*, not *what*; the code should speak for itself

---

## Reporting bugs

If you find a bug, [open an issue](https://github.com/whozahm3d/turo-onboard/issues) with:
1. A clear title and description
2. Steps to reproduce
3. Expected vs. actual behavior
4. Your environment (Python version, OS, dependencies)
5. Screenshots or error logs (if applicable)

---

## Feature requests

Have an idea? [Start a discussion](https://github.com/whozahm3d/turo-onboard/discussions) or [open an issue](https://github.com/whozahm3d/turo-onboard/issues) labeled as a feature request.

---

## Questions?

- Check existing [issues](https://github.com/whozahm3d/turo-onboard/issues) and [discussions](https://github.com/whozahm3d/turo-onboard/discussions)
- Reach out directly or comment on relevant issues

---

## Contributor recognition

All contributors are recognized in the [README.md](README.md) and the GitHub contributors graph. Thank you for helping improve turo-onboard! 🙌

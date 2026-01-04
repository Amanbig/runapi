# Contributing to runapi

Thank you for your interest in contributing to **runapi** 🚀
Every contribution matters — whether it’s code, documentation, tests, or ideas.

This guide explains **how to contribute**, **what to work on**, and **what is expected**.

---

## 🧠 About runapi

**runapi** is an opinionated framework built on top of **FastAPI**, focused on:

* File-based routing
* Improved developer experience
* Production-ready defaults

The project is still evolving, and contributions are welcome at all levels.

---

## 📋 Ways to Contribute

You can contribute by:

* Fixing bugs
* Improving documentation
* Adding examples
* Writing tests
* Improving developer experience
* Suggesting features

If you’re new to open source, look for issues labeled **`good first issue`**.

---

## 🟢 Getting Started

### 1️⃣ Fork the Repository

Click **Fork** on GitHub and clone your fork:

```bash
git clone https://github.com/Amanbig/runapi.git
cd runapi
```

---

### 2️⃣ Create a Virtual Environment

```bash
python -m venv venv
source venv/bin/activate      # Linux / macOS
venv\Scripts\activate         # Windows
```

---

### 3️⃣ Install Dependencies

```bash
pip install -r requirements.txt
```

> **Python 3.9+ is required**

---

## ▶️ Running the Project Locally

If the project includes examples:

```bash
cd examples
python main.py
```

If not, refer to the README for current usage instructions.

---

## 🧩 Choosing an Issue

1. Browse open issues
2. Look for labels:

   * `good first issue`
   * `help wanted`
3. Comment on the issue to let others know you’re working on it

Please wait for maintainer confirmation before starting work.

---

## 🌱 Branching Strategy

Create a new branch for your work:

```bash
git checkout -b feature/short-description
```

Examples:

* `fix/missing-route-error`
* `docs/file-based-routing`
* `test/router-discovery`

---

## 🛠️ Making Changes

* Keep changes **small and focused**
* Follow existing project structure
* Add tests when fixing bugs or adding features
* Update documentation when behavior changes

---

## 🧪 Running Tests

If tests are present:

```bash
pytest
```

Make sure all tests pass before opening a PR.

---

## ✍️ Commit Message Guidelines

Use clear and descriptive commit messages:

```
type: short description
```

Examples:

* `fix: improve error message for missing routes`
* `docs: add file-based routing explanation`
* `test: add router discovery tests`

---

## 🔁 Submitting a Pull Request

1. Push your branch to your fork
2. Open a Pull Request to the **main** branch
3. Reference the related issue:

   ```
   Closes #12
   ```
4. Clearly explain:

   * What was changed
   * Why it was changed

Small, focused PRs are preferred over large ones.

---

## 🔍 Pull Request Checklist

Before submitting, make sure:

* [ ] Code follows project style
* [ ] Tests pass
* [ ] Documentation updated (if needed)
* [ ] PR references an issue

---

## 📐 Code Style Guidelines

* Prefer readability over cleverness
* Use meaningful variable names
* Keep functions small and focused
* Avoid unnecessary complexity

---

## 📄 Documentation Guidelines

* Keep explanations concise
* Use examples where possible
* Assume the reader is new to the project

---

## 🤝 Code of Conduct

Please be respectful and inclusive.
Harassment, discrimination, or abusive behavior will not be tolerated.

---

## ❓ Need Help?

If you’re stuck or unsure:

* Ask questions in the related issue
* Provide logs, errors, or screenshots if relevant

Maintainers are happy to help 🙂

---

## ❤️ Thank You

Your time and effort make **runapi** better for everyone.
Thanks for contributing!

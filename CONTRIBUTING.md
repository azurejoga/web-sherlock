# ?? Contributing

We welcome contributions! Here's how to get started:

---

## ??? Project Architecture

```
web-sherlock/
+-- app.py                 # Main Flask application
+-- sherlock_runner.py     # Sherlock CLI integration
+-- auth_manager.py        # Authentication system
+-- history_manager.py     # Search history management
+-- export_utils.py        # Export functionality
+-- translations/          # Multi-language support
¦   +-- pt.json           # Portuguese
¦   +-- en.json           # English
¦   +-- es.json           # Spanish
¦   +-- zh.json           # Chinese
+-- templates/             # HTML templates
+-- static/               # CSS, JS, assets
+-- sherlock/             # Integrated Sherlock project
+-- results/              # Search results storage
```

---

## Quick Contribution Options

- **?? Add Translations**: Follow our [Translation Guide](TRANSLATION.md)
- **?? Report Bugs**: Use our [Issue Template](https://github.com/azurejoga/web-sherlock/issues)
- **?? Suggest Features**: Share your ideas in [Discussions](https://github.com/azurejoga/web-sherlock/discussions)
- **?? Improve Documentation**: Help us make docs better

---

### How to Contribute

1. **Fork the Repository**  
   Click "Fork" at the top right of this page, then clone your fork.

2. **Create a Branch**  
   Create a feature or fix branch:  
   `git checkout -b my-feature-branch`

3. **Make Changes**  
   Make your changes and commit with clear messages.

4. **Push to Your Fork**  
   `git push origin my-feature-branch`

5. **Open a Pull Request**  
   Go to the original repo, click "New Pull Request", and select your branch.

---

### Need Help?

Open an [issue](https://github.com/azurejoga/web-sherlock/issues) or start a [discussion](https://github.com/azurejoga/web-sherlock/discussions) if you have questions.

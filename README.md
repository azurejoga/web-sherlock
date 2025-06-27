# 🔍 Web Sherlock

[![Python Version](https://img.shields.io/badge/python-3.11%2B-blue.svg)](https://www.python.org/downloads/)
[![Flask](https://img.shields.io/badge/flask-3.1%2B-green.svg)](https://flask.palletsprojects.com/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Security](https://img.shields.io/badge/security-OWASP%20compliant-brightgreen.svg)](SECURITY.md)
[![Multilingual](https://img.shields.io/badge/languages-4-orange.svg)](#supported-languages)
[![Stars](https://img.shields.io/github/stars/azurejoga/web-sherlock.svg?style=social)](https://github.com/azurejoga/web-sherlock/stargazers)
[![Forks](https://img.shields.io/github/forks/azurejoga/web-sherlock.svg?style=social)](https://github.com/azurejoga/web-sherlock/network/members)
[![Issues](https://img.shields.io/github/issues/azurejoga/web-sherlock.svg)](https://github.com/azurejoga/web-sherlock/issues)
[![Pull Requests](https://img.shields.io/github/issues-pr/azurejoga/web-sherlock.svg)](https://github.com/azurejoga/web-sherlock/pulls)
[![Last Commit](https://img.shields.io/github/last-commit/azurejoga/web-sherlock.svg)](https://github.com/azurejoga/web-sherlock/commits/main)
[![Repo Size](https://img.shields.io/github/repo-size/azurejoga/web-sherlock)](https://github.com/azurejoga/web-sherlock)

> **A powerful multilingual web interface for cross-platform social media username searches using the Sherlock Project tool.**

Web Sherlock provides an intuitive, secure web interface for conducting comprehensive username investigations across 400+ social media platforms. Built with Flask and featuring multi-user support, real-time search capabilities, and professional export options using the Sherlock Project

## ✨ Key Features
* Advanced Search: Look up usernames on 400+ social networks
* Multiple Users: Search for multiple usernames (separated by lines, spaces or commas)
* Authentication System: Registration, login, and session control
* Search History: View, delete, and manage past searches
* Multiple Export Formats: JSON, CSV, PDF, TXT, and ZIP
* Rate Limiting: 60-second cooldown between searches
* Responsive Interface: Modern UI with Bootstrap 5
* Asynchronous Processing: Background search with live updates

### 🌐 **Multilingual Support**
- **4 Complete Languages**: Portuguese, English, Spanish, Chinese
- **Automatic Detection**: New languages auto-appear in the interface
- **Easy Translation**: Step-by-step guides for contributors

### 🚀 **High Performance**
- **Unlimited Parallel Searches**: Up to 20 concurrent threads
- **Fast Results**: 2-3 second timeout per site
- **Background Processing**: Non-blocking search execution
- **Real-time Updates**: Live search progress tracking

### 📊 **Professional Export Options**
- **Multiple Formats**: JSON, CSV, PDF, TXT, ZIP
- **Detailed Reports**: Comprehensive search statistics
- **Bulk Operations**: Export multiple searches at once
- **Professional Layout**: ReportLab-powered PDF generation

### 👥 **Multi-User Platform**
- **User Authentication**: Secure registration and login
- **Personal History**: Individual search management
- **Session Management**: Persistent user sessions

## 🚀 Quick Start

### Option 1: Automatic Setup (Recommended)

**Linux/macOS:**
```bash
# Clone the repository
git clone https://github.com/azurejoga/web-sherlock.git
cd web-sherlock

# Run setup script
chmod +x setup_venv.sh
./setup_venv.sh

# Start the application
./run_local.sh
```

**Windows:**
```batch
# Clone the repository
git clone https://github.com/azurejoga/web-sherlock.git
cd web-sherlock

# Run setup script
setup_venv.bat

# Start the application
run_local.bat
```

### Option 2: Manual Installation

1. **Clone and Setup**
```bash
git clone https://github.com/azurejoga/web-sherlock.git
cd web-sherlock
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

2. **Install Dependencies**
```bash
pip install -r requirements.txt
```

3. **Set Environment Variables**
```bash
export SESSION_SECRET="your-secret-key-here"
export FLASK_ENV=development  # Optional for development
```

4. **Run the Application**
```bash
python3 main.py # for Windows, python main.py
```

5. **Access the Interface**
   - Open your browser to `http://localhost:5000`
   - Create an account and start searching!

## issue with Windows version
We are still investigating the issue where the system returns 0 users in the search, even though the path is explicitly defined. The problem initially seemed to be in sherlock_runner.py, but early investigation suggests it is not. For now, usage is restricted to Linux environments. You can help by contributing to the investigation [here](https://github.com/azurejoga/web-sherlock/issues/10)

## 🌍 Supported Languages

| Language | Code | Status | Contributors |
|----------|------|--------|-------------|
| 🇧🇷 Português | `pt` | ✅ Complete (145 strings) | [azurejoga](https://github.com/azurejoga) |
| 🇺🇸 English | `en` | ✅ Complete (145 strings) | [azurejoga](https://github.com/azurejoga) |
| 🇪🇸 Español | `es` | ✅ Complete (145 strings) | [azurejoga](https://github.com/azurejoga) |
| 🇨🇳 中文 | `zh` | ✅ Complete (145 strings) | [azurejoga](https://github.com/azurejoga) |

**Want to add your language?** See our [Translation Guide](TRANSLATION.md) for step-by-step instructions.

## 📚 Documentation

- **[Security Guide](SECURITY.md)**: Comprehensive security documentation
- **[Translation Guide](TRANSLATION.md)**: How to add new languages
- **[Contributing Guide](CONTRIBUTING.md)**: Development and contribution guidelines
- **[Code of Conduct](CODE_OF_CONDUCT.md)**: Community standards
- **[Contributors](CONTRIBUTORS.md)**: Project contributors and acknowledgments

## 🔧 System Requirements

- **Python**: 3.11 or higher
- **Memory**: 512MB RAM minimum (2GB recommended)
- **Storage**: 1GB free space
- **Network**: Internet connection for searches
- **Browser**: Modern web browser (Chrome, Firefox, Safari, Edge)

## 🔍 How It Works

1. **User Registration**: Create account with secure authentication
2. **Username Input**: Enter usernames manually or upload JSON files
3. **Search Configuration**: Set timeout, filters, and export options
4. **Parallel Execution**: Sherlock searches across 400+ platforms
5. **Real-time Results**: Live updates during search process
6. **Professional Export**: Download results in multiple formats
7. **History Management**: Access and manage past searches


## 🤝 Contributing

We welcome contributions! see to [CONTRIBUTING]((CONTRIBUTING.md)

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🙏 Acknowledgments

- **[Sherlock Project](https://github.com/sherlock-project/sherlock)**: The amazing CLI tool that powers our searches
- **Flask Community**: For the excellent web framework
- **Bootstrap Team**: For the responsive UI components
- **All Contributors**: See [CONTRIBUTORS.md](CONTRIBUTORS.md) for the full list

## Support

- **GitHub Issues**: [Report bugs or request features](https://github.com/azurejoga/web-sherlock/issues)
- **Discussions**: [Community discussions](https://github.com/azurejoga/web-sherlock/discussions)
- **Security Issues**: [Report security vulnerabilities](SECURITY.md#reporting-security-vulnerabilities)

---

<div align="center">

**⭐ Star this project if you find it useful!**

Made with ❤️ by [azurejoga](https://github.com/azurejoga)

</div>
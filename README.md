# Web Sherlock

A bilingual web interface built with Flask to search usernames across multiple social networks using the Sherlock Project, with authentication system, search history, and multiple export formats.

## 🌟 Features

* 🔍 **Advanced Search**: Look up usernames on 400+ social networks
* 👥 **Multiple Users**: Search for multiple usernames (separated by lines or commas)
* 🌍 **Bilingual Interface**: Portuguese and English with JSON-based translation system
* 🔐 **Authentication System**: Registration, login, and session control
* 📊 **Real-Time Monitoring**: Animated progress bar (without percentage)
* 📈 **Search History**: View, delete, and manage past searches
* 📄 **Multiple Export Formats**: JSON, CSV, PDF, TXT, and ZIP
* ⏱️ **Rate Limiting**: 60-second cooldown between searches
* 🎨 **Responsive Interface**: Modern UI with Bootstrap 5
* ⚡ **Asynchronous Processing**: Background search with live updates

## 🛠️ Technologies Used

* **Backend**: Python 3.11+, Flask 3.0, Gunicorn
* **Frontend**: Bootstrap 5, JavaScript, Font Awesome
* **Integration**: Embedded Sherlock CLI
* **Export Tools**: ReportLab (PDF), Pandas (CSV), built-in JSON
* **Authentication**: JSON file-based system
* **Internationalization**: JSON translation system

## 🚀 Installation & Execution

### Method 1: Local Installation

#### Linux/macOS:
```bash
git clone https://github.com/azurejoga/web-sherlock.git
cd web-sherlock
python3 -m venv websherlock
source websherlock/bin/activate
pip install poetry
poetry install --no-root
python3 main.py
```

#### Windows:

```bash
git clone https://github.com/azurejoga/web-sherlock.git
cd web-sherlock
python -m venv websherlock
websherlock\Scripts\activate
pip install poetry
poetry install --no-root
python main.py
```

The application will be available at `http://localhost:5000`

## 📋 How to Use

### 1. Register and Log In

* Open the application and create an account
* Log in to access full features

### 2. Perform Searches

* **Method 1**: Type one username per line
* **Method 2**: Enter usernames separated by commas: `azurejoga, zargonbr, user3`
* **Method 3**: Upload a JSON file with a list of usernames
* Click "Start Search" to begin and track progress live

### 3. Manage Search History

* Go to "Search History" in the menu
* View previous results by clicking "View Results"
* Delete individual items or clear all history

### 4. Export Results

* **JSON**: Structured data for integration
* **CSV**: Excel-compatible spreadsheet
* **PDF**: Print-friendly report
* **TXT**: Plain text
* **ZIP**: All formats in a compressed file

### 🗂️ Project Structure

```
web-sherlock/
├── app.py                 # Main Flask app
├── main.py                # Entry point
├── auth_manager.py        # Authentication system
├── sherlock_runner.py     # Sherlock integration
├── export_utils.py        # Export logic
├── translations.py        # Language system
├── templates/             # HTML templates
├── static/                # CSS and JavaScript
├── translations/          # JSON translation files
├── sherlock/              # Embedded Sherlock project
├── uploads/               # Uploaded files
├── results/               # Exported results
└── pyproject.toml         # Poetry dependencies
```

## 🌐 Internationalization

Supports multiple languages via JSON files:

* `translations/pt.json` - Portuguese (Brazil)
* `translations/en.json` - English

To add a new language, create a JSON file in the `translations/` directory with corresponding keys and translations.

## 🔒 Authentication System

* **File-Based**: No database required
* **Encrypted Passwords**: SHA-256 with salt
* **Secure Sessions**: Managed by Flask
* **User-Specific History**: Each user has private search history

## 📊 Monitoring

The system includes:

* **Visual Progress**: Spinner-style progress bar
* **Real-Time Status**: Updates every second
* **Detailed Feedback**: Current site being checked
* **Counters**: Number of sites scanned

## 👨‍💻 Author

**Juan Mathews Rebello Santos**

* GitHub: [@azurejoga](https://github.com/azurejoga)
* LinkedIn: [Juan Mathews Rebello Santos](https://linkedin.com/in/juan-mathews-rebello-santos-/)
* Project: [Web Sherlock](https://github.com/azurejoga/web-sherlock/)

## 🤝 Contributing

1. Fork this repository
2. Create a branch (`git checkout -b feature/AmazingFeature`)
3. Commit your changes (`git commit -m 'Add some AmazingFeature'`)
4. Push the branch (`git push origin feature/AmazingFeature`)
5. Open a Pull Request

## 📝 License

This project is licensed under the MIT License. See the `LICENSE` file for more details.

## 🔗 Useful Links

* [GitHub Repository](https://github.com/azurejoga/web-sherlock/)
* [Original Sherlock Project](https://github.com/sherlock-project/sherlock)
* [Flask Documentation](https://flask.palletsprojects.com/)
* [Bootstrap 5](https://getbootstrap.com/)

## 📞 Support

To report bugs or request features, open an [issue on GitHub](https://github.com/azurejoga/web-sherlock/issues).

# Web Sherlock - Web Interface to Search for Usernames with Sherlock

A **Bilingual Web Interface (Portuguese/English)** built with Flask to search for usernames across social networks using the [Sherlock project](https://github.com/sherlock-project/sherlock).

## 🌟 Features

- **Bilingual Interface**: Full support for Portuguese and English  
- **Multi-Username Search**: Search for multiple usernames at once  
- **JSON Upload**: Upload username lists via JSON files  
- **Integrated Sherlock**: Sherlock is already included in the project  
- **Asynchronous Execution**: Real-time progress bar  
- **Export Options**: Export results in JSON (more formats coming soon)  
- **Responsive UI**: Modern design with Bootstrap 5  
- **Accessibility**: Full support for visually impaired users  

## 📋 Requirements

- Python 3.8 or higher  
- Git  
- [Poetry](https://python-poetry.org/) for dependency management  

## 🚀 Installation and Usage

### 1. Clone the Repository

```bash
git clone https://github.com/azurejoga/web-sherlock.git
cd web-sherlock
````

### 2. Install Dependencies with Poetry

Make sure you have Poetry installed. Then run:

```bash
poetry install --no-root
```

### 3. Activate the Virtual Environment

```bash
poetry shell
```

### 4. Run the Application

```bash
python3 main.py or python main.py
```

The application will be available at: [http://localhost:5000](http://localhost:5000)

## 📖 How to Use

### Username Search

1. Enter one or more usernames (one per line) in the input field
2. Select the desired options:

   * **Show All Sites**: Display sites where the user was not found
   * **Only Show Found**: Show only found profiles
   * **Include NSFW Sites**: Include adult websites in the search
   * **Use Local Data**: Force usage of Sherlock's local data
   * **Timeout**: Set a timeout for each request (default: 60s)
3. Click "Start Search"

### JSON File Upload

You can upload a JSON file containing a list of usernames:

```json
["user1", "user2", "user3"]
```

or

```json
{
  "usernames": ["user1", "user2", "user3"]
}
```

**Note**: When a JSON file is uploaded, the "Use Local Data" option is automatically selected for compatibility.

### Exporting Results

Once the search is completed, results can be exported:

* **JSON**: Structured data in JSON format (more formats coming soon)

## 🌐 Language Switch

Use the language menu at the top of the page to switch between Portuguese (🇧🇷) and English (🇺🇸).

## 🔧 Advanced Options

### Custom Timeout

Set a custom timeout for each request (1–300 seconds).

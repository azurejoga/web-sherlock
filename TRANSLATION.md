# Translation Guide - Web Sherlock

This guide explains how to add new translations to Web Sherlock easily and efficiently.

## Translation System Overview

Web Sherlock uses a modular translation system based on JSON files located in the `translations/` folder. Each language has its own `.json` file with all interface strings.

### Current Languages Available
- `translations/pt.json` - Portuguese (Brazil) - **Complete base file - 145 strings**
- `translations/en.json` - English (United States) - **Complete - 145 strings**
- `translations/es.json` - Spanish - **Complete - 145 strings**
- `translations/zh.json` - Chinese (Simplified) - **Complete - 145 strings**

## How to Add a New Language

### Method 1: Automatic (Recommended)

1. **Run the translation addition script:**
   ```bash
   python add_translation.py
   ```

2. **Follow the interactive menu:**
   - Choose option "1" (Add new language)
   - Enter the language code (e.g., `fr` for French, `de` for German)
   - Confirm to create the file based on Portuguese

3. **The system will:**
   - Automatically create the `translations/[code].json` file
   - Copy all 145 strings from the Portuguese base file
   - Display success message

### Method 2: Manual

1. **Create the translation file:**
   - Copy the `translations/pt.json` file
   - Rename to `translations/[language_code].json`
   - Example: `translations/fr.json` for French

2. **Translate the strings:**
   - Keep the keys (left side) unchanged
   - Translate only the values (right side)
   - Example:
   ```json
   {
     "welcome": "Welcome",  // ← Translate only this part
     "search": "Search",
     "username": "Username"
   }
   ```

## Automatic Language Detection

Web Sherlock features **automatic language detection**. As soon as you create a new translation file in the `translations/` folder, it will automatically appear in the language menu.

**No code modifications needed!**

## Adding Language Flag to Interface

If you want to add a flag icon for your new language, follow these steps:

1. **Edit the base template file:**
   Open `templates/base.html`

2. **Find the language menu section** (around line 45-65):
   ```html
   {% for lang_code in supported_languages %}
   <li>
       <a class="dropdown-item" href="{{ url_for('set_language', language=lang_code) }}">
           {% if lang_code == 'pt' %}🇧🇷 Português{% endif %}
           {% if lang_code == 'en' %}🇺🇸 English{% endif %}
           {% if lang_code == 'es' %}🇪🇸 Español{% endif %}
           {% if lang_code == 'zh' %}🇨🇳 中文{% endif %}
       </a>
   </li>
   {% endfor %}
   ```

3. **Add your language flag:**
   ```html
   {% if lang_code == 'fr' %}🇫🇷 Français{% endif %}
   {% if lang_code == 'de' %}🇩🇪 Deutsch{% endif %}
   {% if lang_code == 'ja' %}🇯🇵 日本語{% endif %}
   ```

4. **Save the file** - Your language will now show with its flag icon!

## Complete String Categories (145 total)

### Main Interface (15 strings)
- `welcome`, `search`, `username`, `results`, `home`
- `login`, `register`, `logout`, `history`, `export`
- `options`, `settings`, `language`, `about`, `help`

### Authentication Forms (12 strings)
- `email`, `password`, `confirm_password`, `old_password`
- `register_button`, `login_button`, `submit`, `cancel`
- `remember_me`, `forgot_password`, `create_account`, `welcome_back`

### Search Interface (18 strings)
- `search_usernames`, `enter_username`, `multiple_usernames`
- `upload_json`, `search_options`, `timeout`, `print_all`
- `print_found`, `nsfw`, `local`, `start_search`
- `loading`, `wait`, `searching_users`, `search_completed`
- `search_in_progress`, `clear_history`

### Results Display (20 strings)
- `found_profiles`, `not_found_profiles`, `total_sites`
- `show_all`, `show_only_found`, `filter_results`
- `site_name`, `profile_url`, `status`, `response_time`
- `no_results`, `search_summary`, `usernames_searched`
- Various result status messages

### Export Functionality (15 strings)
- `export_json`, `export_csv`, `export_pdf`, `export_txt`, `export_zip`
- `download`, `formats_available`, `file_size`, `download_ready`
- Export-related success and error messages

### Error and Success Messages (25 strings)
- `success_*` messages for various operations
- `error_*` messages for different failure scenarios
- `warning_*` messages for user notifications
- Form validation messages

### History Management (10 strings)
- `search_history`, `no_history`, `delete_search`
- `clear_all_history`, `view_results`, `search_date`
- History-related interface elements

### System Messages (15 strings)  
- `page_not_found`, `internal_error`, `unauthorized`
- Loading states, connection issues, timeout messages
- General system status indicators

### Navigation and UI (15 strings)
- Menu items, buttons, labels, tooltips
- Modal dialog content, confirmation messages
- Accessibility and user guidance text

## Development Tools

### Check Missing Keys
```bash
python add_translation.py
# Choose option "4" to list missing keys
```

### Add New Translation Key
```bash
python add_translation.py
# Choose option "2" to add key to all languages
```

### Update Existing Key
```bash
python add_translation.py
# Choose option "3" to update a specific key
```

## Quality Standards

### Consistency
- Use consistent terms for similar concepts
- Maintain consistent formal/informal tone
- Preserve functionality (buttons, links, etc.)

### Formatting
- Maintain appropriate punctuation (!, ?, :)
- Preserve HTML formatting if present
- Use proper capitalization for your language

### Contextualization
- Consider the usage context of each string
- Test translations in the actual interface
- Ensure it makes sense to native speakers

## Testing Your Translations

1. **Start the server:**
   ```bash
   python main.py
   ```

2. **Access the web interface:**
   - Open http://localhost:5000
   - Look for your language in the top-right menu
   - Navigate through the interface to verify translations

3. **Test key functionality:**
   - Search form
   - Login/registration system
   - Results page
   - Data export
   - Error/success messages

## Priority Languages

Contributions are especially welcome for:
- **French (fr)** - High community interest
- **German (de)** - European market
- **Italian (it)** - Active community
- **Russian (ru)** - Large user base
- **Japanese (ja)** - OSINT interest
- **Arabic (ar)** - Regional growth
- **Korean (ko)** - Tech community
- **Hindi (hi)** - Growing market

## Contributing Your Translations

### Via GitHub
1. Fork the repository
2. Create a branch: `git checkout -b translation-[language]`
3. Add your translation file
4. Commit: `git commit -m "Add [language] translation"`
5. Open a Pull Request

### Via Issue
1. Create an issue on GitHub
2. Attach your `.json` translation file
3. Mention the language code in the title
4. Wait for review and approval

## File Structure Example

```json
{
  "welcome": "Welcome to Web Sherlock",
  "search": "Search",
  "username": "Username",
  "results": "Results",
  "login": "Login",
  "register": "Register",
  "export_json": "Export JSON",
  "error_no_usernames": "Please enter at least one username.",
  "success_search_completed": "Search completed successfully!",
  "loading": "Loading...",
  "found_profiles": "Found Profiles",
  "not_found_profiles": "Not Found Profiles"
}
```

## Support

For translation questions:
- Open a GitHub issue
- Use the `translation` tag
- Describe your specific question or problem

## Recognition

All translation contributors are credited in the CONTRIBUTORS.md file and in the application interface.

Thank you for helping make Web Sherlock accessible to more people around the world! 🌐
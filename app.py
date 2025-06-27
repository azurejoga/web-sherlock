import os
import json
import threading
import time
from datetime import datetime
from functools import wraps
from flask import Flask, render_template, request, jsonify, send_file, session, redirect, url_for, flash
from werkzeug.utils import secure_filename
import logging

from sherlock_runner import SherlockRunner
from export_utils import ExportUtils
from translations import get_translations, get_supported_languages
from auth_manager import AuthManager
from history_manager import HistoryManager

# Configure secure logging to prevent injection
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler()
    ]
)

# Create sanitized logger
logger = logging.getLogger(__name__)

def safe_log(level, message, *args, **kwargs):
    """Secure logging function that prevents log injection"""
    try:
        # Sanitize message and arguments
        if isinstance(message, str):
            message = message.replace('\n', ' ').replace('\r', ' ')[:500]
        sanitized_args = []
        for arg in args:
            if isinstance(arg, str):
                sanitized_args.append(str(arg).replace('\n', ' ').replace('\r', ' ')[:100])
            else:
                sanitized_args.append(str(arg)[:100])
        
        logger.log(level, message, *sanitized_args, **kwargs)
    except Exception:
        logger.error("Logging error occurred")

def _sanitize_username(username):
    """Sanitize username input for security"""
    import re
    if not username:
        return ""
    
    # Remove potentially dangerous characters
    username = re.sub(r'[<>"\'/\\;=&$%]', '', str(username))
    # Limit length to prevent buffer overflows
    username = username[:50]
    # Remove leading/trailing whitespace
    username = username.strip()
    
    return username

app = Flask(__name__)
app.secret_key = os.environ.get("SESSION_SECRET", "dev-secret-key-change-in-production")

# Security headers middleware
@app.after_request
def apply_security_headers(response):
    """Apply security headers to all responses"""
    response.headers['X-Content-Type-Options'] = 'nosniff'
    response.headers['X-Frame-Options'] = 'DENY'
    response.headers['X-XSS-Protection'] = '1; mode=block'
    response.headers['Strict-Transport-Security'] = 'max-age=31536000; includeSubDomains'
    response.headers['Content-Security-Policy'] = "default-src 'self'; script-src 'self' 'unsafe-inline' https://cdn.jsdelivr.net; style-src 'self' 'unsafe-inline' https://cdn.jsdelivr.net; font-src 'self' https://cdn.jsdelivr.net; img-src 'self' data:; connect-src 'self'"
    return response

# Configuration
UPLOAD_FOLDER = 'uploads'
RESULTS_FOLDER = 'results'
ALLOWED_EXTENSIONS = {'json'}

# Ensure directories exist
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
os.makedirs(RESULTS_FOLDER, exist_ok=True)

app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['RESULTS_FOLDER'] = RESULTS_FOLDER

# Initialize authentication and history managers
auth_manager = AuthManager()
history_manager = HistoryManager()

# Add context processor for global template variables
@app.context_processor
def inject_global_vars():
    """Inject global variables into all templates"""
    return {
        'supported_languages': get_supported_languages(),
        'current_language': session.get('language', 'en')
    }

# Global variables for tracking search progress and preventing duplicates
search_progress = {}
search_results = {}
active_searches = {}  # Track active searches by user to prevent duplicates

# Authentication decorator
def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        token = session.get('auth_token')
        if not token:
            language = session.get('language', 'en')
            translations = get_translations(language)
            flash(translations.get('error_login_required', 'Login required'), 'error')
            return redirect(url_for('login'))
        
        user = auth_manager.verify_token(token)
        if not user:
            session.pop('auth_token', None)
            session.pop('current_user', None)
            language = session.get('language', 'en')
            translations = get_translations(language)
            flash(translations.get('error_login_required', 'Login required'), 'error')
            return redirect(url_for('login'))
        
        session['current_user'] = user
        return f(*args, **kwargs)
    return decorated_function

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

@app.route('/')
@login_required
def index():
    language = session.get('language', 'en')
    translations = get_translations(language)
    user = session.get('current_user')
    return render_template('index.html', 
                         translations=translations, 
                         language=language,
                         languages=get_supported_languages(),
                         user=user)

# Authentication routes
@app.route('/login', methods=['GET', 'POST'])
def login():
    language = session.get('language', 'en')
    translations = get_translations(language)
    
    if request.method == 'POST':
        username = request.form.get('username', '').strip()
        password = request.form.get('password', '')
        
        result = auth_manager.login_user(username, password)
        
        if result['success']:
            session['auth_token'] = result['token']
            session['current_user'] = result['user']
            flash(translations.get('success_login', 'Login successful!'), 'success')
            
            # Redirect to the page user was trying to access or home
            next_page = request.args.get('next')
            return redirect(next_page or url_for('index'))
        else:
            error_key = result.get('error', 'error_invalid_credentials')
            flash(translations.get(error_key, 'Login failed'), 'error')
    
    return render_template('login.html', 
                         translations=translations, 
                         language=language,
                         languages=get_supported_languages())

@app.route('/register', methods=['GET', 'POST'])
def register():
    language = session.get('language', 'en')
    translations = get_translations(language)
    
    if request.method == 'POST':
        username = request.form.get('username', '').strip()
        email = request.form.get('email', '').strip()
        password = request.form.get('password', '')
        confirm_password = request.form.get('confirm_password', '')
        
        # Validate passwords match
        if password != confirm_password:
            flash(translations.get('error_passwords_dont_match', 'Passwords do not match'), 'error')
        else:
            result = auth_manager.register_user(username, email, password)
            
            if result['success']:
                session['auth_token'] = result['token']
                session['current_user'] = result['user']
                flash(translations.get('success_register', 'Account created successfully!'), 'success')
                return redirect(url_for('index'))
            else:
                error_key = result.get('error', 'error_registration_failed')
                flash(translations.get(error_key, 'Registration failed'), 'error')
    
    return render_template('register.html', 
                         translations=translations, 
                         language=language,
                         languages=get_supported_languages())

@app.route('/logout')
def logout():
    language = session.get('language', 'en')
    translations = get_translations(language)
    
    token = session.get('auth_token')
    if token:
        auth_manager.logout_user(token)
    
    session.pop('auth_token', None)
    session.pop('current_user', None)
    flash(translations.get('success_logout', 'Logout successful!'), 'success')
    return redirect(url_for('login'))

@app.route('/history')
@login_required
def history():
    language = session.get('language', 'en')
    translations = get_translations(language)
    user = session.get('current_user')
    
    # Get user history
    if not user or 'username' not in user:
        return redirect(url_for('login'))
    
    user_history = history_manager.get_history(user['username'])
    stats = history_manager.get_history_stats(user['username'])
    
    return render_template('history.html', 
                         translations=translations, 
                         language=language,
                         languages=get_supported_languages(),
                         user=user,
                         history=user_history,
                         stats=stats)

@app.route('/history/delete/<search_id>', methods=['POST'])
@login_required
def delete_search(search_id):
    language = session.get('language', 'en')
    translations = get_translations(language)
    user = session.get('current_user')
    
    if not user or 'username' not in user:
        return redirect(url_for('login'))
    
    success = history_manager.delete_search(user['username'], search_id)
    
    if success:
        flash(translations.get('success_search_deleted', 'Search deleted successfully!'), 'success')
    else:
        flash(translations.get('error_export_failed', 'Delete failed'), 'error')
    
    return redirect(url_for('history'))

@app.route('/history/clear', methods=['POST'])
@login_required
def clear_history():
    language = session.get('language', 'en')
    translations = get_translations(language)
    user = session.get('current_user')
    
    if not user or 'username' not in user:
        return redirect(url_for('login'))
    
    success = history_manager.clear_history(user['username'])
    
    if success:
        flash(translations.get('success_history_cleared', 'History cleared successfully!'), 'success')
    else:
        flash(translations.get('error_export_failed', 'Clear failed'), 'error')
    
    return redirect(url_for('history'))

@app.route('/history/view/<search_id>')
@login_required
def view_search_results(search_id):
    language = session.get('language', 'en')
    translations = get_translations(language)
    user = session.get('current_user')
    
    if not user or 'username' not in user:
        return redirect(url_for('login'))
    
    # Get search data from history
    search_data = history_manager.get_search(user['username'], search_id)
    if not search_data:
        flash(translations.get('error_404', 'Search not found'), 'error')
        return redirect(url_for('history'))
    
    # Get results data
    results_data = history_manager.get_search_results(user['username'], search_id)
    if not results_data:
        flash(translations.get('error_export_failed', 'Results not found'), 'error')
        return redirect(url_for('history'))
    
    return render_template('results.html', 
                         translations=translations, 
                         language=language,
                         languages=get_supported_languages(),
                         user=user,
                         search_data=search_data,
                         results=results_data,
                         search_id=search_id,
                         from_history=True)

@app.route('/set_language/<language>')
def set_language(language):
    if language in get_supported_languages():
        session['language'] = language
    return redirect(url_for('index'))

@app.route('/search', methods=['POST'])
@login_required
def search():
    try:
        language = session.get('language', 'en')
        translations = get_translations(language)
        
        # Get form data
        usernames = request.form.get('usernames', '').strip()
        uploaded_file = request.files.get('json_file')
        
        # Get usernames from various sources with input validation
        username_list = []
        
        # From text input - support multiple formats: lines, commas, spaces
        if usernames:
            # Split by lines first
            for line in usernames.split('\n'):
                line = line.strip()
                if not line:
                    continue
                
                # Check if line contains commas
                if ',' in line:
                    # Split by comma and clean each username
                    for username in line.split(','):
                        username = _sanitize_username(username.strip())
                        if username and username not in username_list:
                            username_list.append(username)
                # Check if line contains spaces (multiple usernames in one line)
                elif ' ' in line and len(line.split()) > 1:
                    # Split by spaces and clean each username
                    for username in line.split():
                        username = _sanitize_username(username.strip())
                        if username and username not in username_list:
                            username_list.append(username)
                else:
                    # Single username per line
                    username = _sanitize_username(line)
                    if username and username not in username_list:
                        username_list.append(username)
        
        logging.info(f"Parsed {len(username_list)} unique usernames from text input")
        
        # From uploaded JSON file with proper validation
        if uploaded_file and uploaded_file.filename and allowed_file(uploaded_file.filename):
            filepath = None
            try:
                filename = secure_filename(uploaded_file.filename)
                filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
                uploaded_file.save(filepath)
                
                # Check if file is empty
                if os.path.getsize(filepath) == 0:
                    flash(translations.get('json_empty_file', 'Empty JSON file'), 'error')
                    os.remove(filepath)
                    return redirect(url_for('index'))
                
                with open(filepath, 'r', encoding='utf-8') as f:
                    file_content = f.read().strip()
                    
                    # Check if file has content
                    if not file_content:
                        flash(translations.get('json_empty_file', 'Empty JSON file'), 'error')
                        os.remove(filepath)
                        return redirect(url_for('index'))
                    
                    try:
                        json_data = json.loads(file_content)
                    except json.JSONDecodeError as json_error:
                        error_msg = f"""{translations.get('json_format_error', 'JSON format error')}: {str(json_error)}. 
                        
{translations.get('json_accepted_formats', 'Invalid format')}

{translations.get('json_verify_format', 'Verify format')}"""
                        flash(error_msg, 'error')
                        os.remove(filepath)
                        return redirect(url_for('index'))
                    
                    if isinstance(json_data, list):
                        # Validate that all items are strings
                        valid_usernames = [str(username).strip() for username in json_data if str(username).strip()]
                        username_list.extend(valid_usernames)
                        logging.info(f"JSON upload: loaded {len(valid_usernames)} usernames from array")
                        success_msg = translations.get('json_loaded_success', 'JSON loaded successfully: {count} usernames found').format(count=len(valid_usernames))
                        flash(success_msg, 'success')
                    elif isinstance(json_data, dict) and 'usernames' in json_data:
                        if isinstance(json_data['usernames'], list):
                            valid_usernames = [str(username).strip() for username in json_data['usernames'] if str(username).strip()]
                            username_list.extend(valid_usernames)
                            logging.info(f"JSON upload: loaded {len(valid_usernames)} usernames from object")
                            success_msg = translations.get('json_loaded_success', 'JSON loaded successfully: {count} usernames found').format(count=len(valid_usernames))
                            flash(success_msg, 'success')
                        else:
                            flash(translations.get('json_usernames_must_be_array', 'usernames field must be array'), 'error')
                            os.remove(filepath)
                            return redirect(url_for('index'))
                    else:
                        flash(translations.get('json_invalid_format', 'Invalid JSON format'), 'error')
                        os.remove(filepath)
                        return redirect(url_for('index'))
                
                os.remove(filepath)  # Clean up uploaded file
            except Exception as e:
                error_msg = f"{translations.get('json_processing_error', 'Error processing JSON file')}: {str(e)}"
                flash(error_msg, 'error')
                if filepath:
                    try:
                        if os.path.exists(filepath):
                            os.remove(filepath)
                    except:
                        pass  # Ignore cleanup errors
                return redirect(url_for('index'))
        elif uploaded_file and uploaded_file.filename and not allowed_file(uploaded_file.filename):
            flash("Invalid file type. Please upload a JSON file.", 'error')
            return redirect(url_for('index'))
        
        if not username_list:
            flash(translations['error_no_usernames'], 'error')
            return redirect(url_for('index'))
        
        # Get options with proper checkbox validation
        timeout_val = request.form.get('timeout', '').strip()
        if not timeout_val:
            timeout_val = '300'  # Default 5 minutes, no upper limit
        
        # Properly validate checkboxes - only True if explicitly checked
        print_all_checked = request.form.get('print_all') == 'on'
        print_found_checked = request.form.get('print_found') == 'on'
        nsfw_checked = request.form.get('nsfw') == 'on'
        local_checked = request.form.get('local') == 'on'
            
        options = {
            'print_all': print_all_checked,
            'print_found': print_found_checked,
            'nsfw': nsfw_checked,
            'local': local_checked,
            'timeout': timeout_val,
        }
        
        logging.info(f"Checkbox validation - print_all: {print_all_checked}, print_found: {print_found_checked}, nsfw: {nsfw_checked}, local: {local_checked}")
        
        logging.info(f"Search options: {options}")
        
        # Get current user
        user = session.get('current_user')
        if not user or 'username' not in user:
            return redirect(url_for('login'))
        
        username_owner = user['username']
        
        # Check if user already has an active search
        if username_owner in active_searches:
            active_search_id = active_searches[username_owner]
            flash(translations.get('search_in_progress', 'You already have a search in progress'), 'warning')
            return redirect(url_for('get_results', search_id=active_search_id))
        
        # Generate UNIQUE search ID
        import time as time_module
        import random
        search_id = f"search_{int(time_module.time())}_{random.randint(1000,9999)}"
        
        # Mark user as having an active search
        active_searches[username_owner] = search_id
        
        # Create search data ONCE
        search_data = {
            'search_id': search_id,
            'usernames': username_list,
            'options': options,
            'status': 'running',
            'timestamp': datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        }
        
        # Add to history manager ONCE - no duplicates allowed
        history_manager.add_search(username_owner, search_data)
        logging.info(f"Created SINGLE search entry {search_id} for user {username_owner}")
        
        # Start search in background thread and redirect to loading page immediately
        def run_search_background():
            try:
                logging.info(f"Background search: Starting for {len(username_list)} usernames")
                
                runner = SherlockRunner()
                results = runner.run_search(
                    username_list, 
                    options, 
                    search_id, 
                    history_manager,
                    username_owner
                )
                
                # Save results to JSON file
                results_file = os.path.join('results', f'{search_id}_results.json')
                os.makedirs('results', exist_ok=True)
                
                with open(results_file, 'w', encoding='utf-8') as f:
                    json.dump(results, f, ensure_ascii=False, indent=2)
                
                logging.info(f"Search {search_id} completed and saved to {results_file}")
                
                # Update search status in history
                history_manager.update_search_status(
                    username_owner, 
                    search_id, 
                    'completed',
                    len(results.get('found_profiles', [])) + len(results.get('not_found_profiles', [])),
                    len(results.get('found_profiles', [])),
                    results_file,
                    []
                )
                
            except Exception as e:
                logging.error(f"Search {search_id} failed: {str(e)}")
                # Update status to failed
                history_manager.update_search_status(
                    username_owner, 
                    search_id, 
                    'failed', 
                    0, 
                    0,
                    None,
                    []
                )
            finally:
                # Clear active search when done
                if username_owner in active_searches:
                    del active_searches[username_owner]
                    logging.info(f"Cleared active search for user {username_owner}")
        
        # Start background thread
        import threading
        thread = threading.Thread(target=run_search_background, daemon=True)
        thread.start()
        
        # Redirect to results page immediately (loading state)
        return redirect(url_for('get_results', search_id=search_id))
            
    except Exception as e:
        logging.error(f"Search route error: {str(e)}")
        flash(f"Error: {str(e)}", 'error')
        return redirect(url_for('index'))

@app.route('/results/<search_id>')
@login_required
def get_results(search_id):
    language = session.get('language', 'en')
    translations = get_translations(language)
    user = session.get('current_user')
    
    if not user or 'username' not in user:
        return redirect(url_for('login'))
    
    # Get search data from history
    search_data = history_manager.get_search(user['username'], search_id)
    if not search_data:
        flash(translations.get('error_404', 'Search not found'), 'error')
        return redirect(url_for('history'))
    
    # Try to read results from JSON file
    results_file = os.path.join('results', f'{search_id}_results.json')
    results_data = None
    
    if os.path.exists(results_file):
        try:
            with open(results_file, 'r', encoding='utf-8') as f:
                results_data = json.load(f)
            logging.info(f"Loaded results from {results_file}")
        except Exception as e:
            logging.error(f"Error reading results file {results_file}: {str(e)}")
    
    # If no results file exists and search is completed, show error
    if not results_data and search_data.get('status') == 'completed':
        flash(translations.get('error_export_failed', 'Results not found'), 'error')
        return redirect(url_for('history'))
    
    # If search is failed, show error
    if search_data.get('status') == 'failed':
        flash(translations.get('search_error', 'Search failed'), 'error')
        return redirect(url_for('history'))
    
    # If search is still running, show loading page with auto-refresh
    if search_data.get('status') == 'running' and not results_data:
        return render_template('results.html', 
                             search_id=search_id,
                             results=None,
                             translations=translations,
                             language=language,
                             user=user,
                             search_data=search_data,
                             loading=True)
    
    return render_template('results.html', 
                         search_id=search_id,
                         results=results_data,
                         translations=translations,
                         language=language,
                         user=user,
                         search_data=search_data)

@app.route('/download/<search_id>/json')
@login_required
def download_json(search_id):
    """Download search results as JSON"""
    try:
        user = session.get('current_user')
        if not user or 'username' not in user:
            flash('Unauthorized', 'error')
            return redirect(url_for('login'))
        
        # Get results data
        if search_id not in search_results:
            results_data = history_manager.get_search_results(user['username'], search_id)
            if not results_data:
                flash('Results not found', 'error')
                return redirect(url_for('history'))
        else:
            results_data = search_results[search_id]
        
        # Create temporary file
        import tempfile
        import json
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            json.dump(results_data, f, indent=2, ensure_ascii=False)
            temp_path = f.name
        
        return send_file(temp_path, 
                        as_attachment=True, 
                        download_name=f'sherlock_results_{search_id}.json',
                        mimetype='application/json')
        
    except Exception as e:
        logging.error(f"JSON download error: {str(e)}")
        flash('Download failed', 'error')
        return redirect(url_for('history'))

# Additional export routes
@app.route('/export/<search_id>/csv')
@login_required
def export_csv(search_id):
    try:
        user = session.get('current_user')
        if not user or 'username' not in user:
            return redirect(url_for('login'))
        
        # Get results data
        if search_id not in search_results:
            results_data = history_manager.get_search_results(user['username'], search_id)
            if not results_data:
                flash('Results not found', 'error')
                return redirect(url_for('history'))
        else:
            results_data = search_results[search_id]
        
        language = session.get('language', 'en')
        export_utils = ExportUtils(language)
        return export_utils.export_csv(results_data, search_id)
        
    except Exception as e:
        logging.error(f"CSV export error: {str(e)}")
        flash('Export failed', 'error')
        return redirect(url_for('history'))

@app.route('/export/<search_id>/pdf')
@login_required
def export_pdf(search_id):
    try:
        user = session.get('current_user')
        if not user or 'username' not in user:
            return redirect(url_for('login'))
        
        # Get results data
        if search_id not in search_results:
            results_data = history_manager.get_search_results(user['username'], search_id)
            if not results_data:
                flash('Results not found', 'error')
                return redirect(url_for('history'))
        else:
            results_data = search_results[search_id]
        
        language = session.get('language', 'en')
        export_utils = ExportUtils(language)
        return export_utils.export_pdf(results_data, search_id)
        
    except Exception as e:
        logging.error(f"PDF export error: {str(e)}")
        flash('Export failed', 'error')
        return redirect(url_for('history'))

@app.route('/export/<search_id>/txt')
@login_required
def export_txt(search_id):
    try:
        user = session.get('current_user')
        if not user or 'username' not in user:
            return redirect(url_for('login'))
        
        # Get results data
        if search_id not in search_results:
            results_data = history_manager.get_search_results(user['username'], search_id)
            if not results_data:
                flash('Results not found', 'error')
                return redirect(url_for('history'))
        else:
            results_data = search_results[search_id]
        
        language = session.get('language', 'en')
        export_utils = ExportUtils(language)
        return export_utils.export_txt(results_data, search_id)
        
    except Exception as e:
        logging.error(f"TXT export error: {str(e)}")
        flash('Export failed', 'error')
        return redirect(url_for('history'))

@app.route('/export/<search_id>/zip')
@login_required
def export_zip(search_id):
    try:
        user = session.get('current_user')
        if not user or 'username' not in user:
            return redirect(url_for('login'))
        
        # Get results data
        if search_id not in search_results:
            results_data = history_manager.get_search_results(user['username'], search_id)
            if not results_data:
                flash('Results not found', 'error')
                return redirect(url_for('history'))
        else:
            results_data = search_results[search_id]
        
        language = session.get('language', 'en')
        export_utils = ExportUtils(language)
        return export_utils.export_zip_simple(results_data, search_id)
        
    except Exception as e:
        logging.error(f"ZIP export error: {str(e)}")
        flash('Export failed', 'error')
        return redirect(url_for('history'))

# Simple API for checking search completion
@app.route('/api/search/status/<search_id>')
@login_required
def api_search_status(search_id):
    """Check if search results are available"""
    try:
        user = session.get('current_user')
        if not user or 'username' not in user:
            return jsonify({'error': 'Unauthorized'}), 401
        
        # Check if results are in memory
        if search_id in search_results:
            return jsonify({
                'status': 'completed',
                'found_count': len(search_results[search_id].get('found_profiles', [])),
                'total_count': search_results[search_id].get('total_sites_checked', 0)
            })
        
        # Check in history
        search_data = history_manager.get_search(user['username'], search_id)
        if search_data and search_data.get('status') == 'completed':
            return jsonify({
                'status': 'completed',
                'found_count': search_data.get('found_count', 0),
                'total_count': search_data.get('total_count', 0)
            })
        
        return jsonify({'status': 'running'})
        
    except Exception as e:
        logging.error(f"API status error: {str(e)}")
        return jsonify({'error': str(e)}), 500

@app.errorhandler(404)
def not_found_error(error):
    language = session.get('language', 'en')
    translations = get_translations(language)
    return render_template('base.html', 
                         error_message=translations['error_404'],
                         translations=translations,
                         language=language), 404

@app.errorhandler(500)
def internal_error(error):
    language = session.get('language', 'en')
    translations = get_translations(language)
    return render_template('base.html',
                         error_message=translations['error_500'],
                         translations=translations,
                         language=language), 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)

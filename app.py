import os
import json
import threading
import time
from datetime import datetime, timedelta
from flask import Flask, render_template, request, jsonify, send_file, session, redirect, url_for, flash
from werkzeug.utils import secure_filename
import logging
from functools import wraps

from sherlock_runner import SherlockRunner
from export_utils import ExportUtils
from translations import get_translations, get_supported_languages, get_language_display_names
from auth_manager import AuthManager

# Configure logging
logging.basicConfig(level=logging.DEBUG)

app = Flask(__name__)
app.secret_key = os.environ.get("SESSION_SECRET", "dev-secret-key-change-in-production")

# Configuration
UPLOAD_FOLDER = 'uploads'
RESULTS_FOLDER = 'results'
ALLOWED_EXTENSIONS = {'json'}

# Ensure directories exist
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
os.makedirs(RESULTS_FOLDER, exist_ok=True)

app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['RESULTS_FOLDER'] = RESULTS_FOLDER

# Global variables for tracking search progress and rate limiting
search_progress = {}
search_results = {}
search_cooldowns = {}  # Track search cooldowns per user

# Initialize authentication manager
auth_manager = AuthManager()

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def login_required(f):
    """Decorator to require user login"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            language = session.get('language', 'en')
            translations = get_translations(language)
            flash(translations['login_required'], 'error')
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated_function

def check_search_cooldown(user_id):
    """Check if user is in search cooldown period"""
    if user_id in search_cooldowns:
        cooldown_end = search_cooldowns[user_id]
        if datetime.now() < cooldown_end:
            remaining = (cooldown_end - datetime.now()).total_seconds()
            return False, int(remaining)
    return True, 0

def set_search_cooldown(user_id):
    """Set search cooldown for user (60 seconds)"""
    search_cooldowns[user_id] = datetime.now() + timedelta(seconds=60)

@app.route('/')
def index():
    language = session.get('language', 'en')
    translations = get_translations(language)
    
    # Check search cooldown for logged in users
    cooldown_remaining = 0
    if 'user_id' in session:
        can_search, cooldown_remaining = check_search_cooldown(session['user_id'])
    
    return render_template('index.html', 
                         translations=translations, 
                         language=language,
                         languages=get_supported_languages(),
                         cooldown_remaining=cooldown_remaining)

@app.route('/login', methods=['GET', 'POST'])
def login():
    language = session.get('language', 'en')
    translations = get_translations(language)
    
    if request.method == 'POST':
        username = request.form.get('username', '').strip()
        password = request.form.get('password', '')
        
        if not username or not password:
            flash(translations['invalid_credentials'], 'error')
            return redirect(url_for('login'))
        
        result = auth_manager.authenticate_user(username, password)
        
        if result['success']:
            session['user_id'] = result['username']
            session['user_email'] = result['email']
            flash(f"Bem-vindo, {username}!" if language == 'pt' else f"Welcome, {username}!", 'success')
            return redirect(url_for('index'))
        else:
            flash(translations['invalid_credentials'], 'error')
    
    return render_template('login.html', translations=translations, language=language)

@app.route('/register', methods=['GET', 'POST'])
def register():
    language = session.get('language', 'en')
    translations = get_translations(language)
    
    if request.method == 'POST':
        username = request.form.get('username', '').strip()
        email = request.form.get('email', '').strip()
        password = request.form.get('password', '')
        confirm_password = request.form.get('confirm_password', '')
        
        # Validation
        if not username or not email or not password:
            flash("Todos os campos são obrigatórios" if language == 'pt' else "All fields are required", 'error')
            return redirect(url_for('register'))
        
        if password != confirm_password:
            flash("As senhas não coincidem" if language == 'pt' else "Passwords don't match", 'error')
            return redirect(url_for('register'))
        
        if len(password) < 6:
            flash("A senha deve ter pelo menos 6 caracteres" if language == 'pt' else "Password must be at least 6 characters", 'error')
            return redirect(url_for('register'))
        
        result = auth_manager.register_user(username, email, password)
        
        if result['success']:
            flash(translations['registration_successful'], 'success')
            return redirect(url_for('login'))
        else:
            if result['error'] == 'user_already_exists':
                flash(translations['user_already_exists'], 'error')
            else:
                flash("Erro no cadastro" if language == 'pt' else "Registration error", 'error')
    
    return render_template('register.html', translations=translations, language=language)

@app.route('/logout')
def logout():
    session.clear()
    language = session.get('language', 'en')
    flash("Logout realizado com sucesso" if language == 'pt' else "Logged out successfully", 'success')
    return redirect(url_for('index'))

@app.route('/history')
@login_required
def search_history():
    language = session.get('language', 'en')
    translations = get_translations(language)
    
    history = auth_manager.get_user_search_history(session['user_id'])
    
    return render_template('history.html', 
                         translations=translations, 
                         language=language,
                         history=history)

@app.route('/history/delete/<search_id>', methods=['POST'])
@login_required
def delete_history_item(search_id):
    language = session.get('language', 'en')
    translations = get_translations(language)
    
    success = auth_manager.delete_search_history_item(session['user_id'], search_id)
    
    if success:
        flash(translations['item_removed'], 'success')
    else:
        flash(translations['error_removing_item'], 'error')
    
    return redirect(url_for('search_history'))

@app.route('/history/clear', methods=['POST'])
@login_required
def clear_history():
    language = session.get('language', 'en')
    translations = get_translations(language)
    
    success = auth_manager.clear_user_search_history(session['user_id'])
    
    if success:
        flash(translations['history_cleared'], 'success')
    else:
        flash(translations['error_clearing_history'], 'error')
    
    return redirect(url_for('search_history'))

@app.route('/history/view/<search_id>')
@login_required
def view_history_item(search_id):
    language = session.get('language', 'en')
    translations = get_translations(language)
    
    # Get search details from history
    search_item = auth_manager.get_search_by_id(session['user_id'], search_id)
    
    if not search_item:
        flash(translations['search_not_found'], 'error')
        return redirect(url_for('search_history'))
    
    # Create a properly structured result for display
    results = {
        'usernames': search_item.get('usernames', []),
        'found_profiles': search_item.get('found_profiles', []),
        'not_found_profiles': search_item.get('not_found_profiles', []),
        'search_timestamp': search_item.get('search_timestamp', search_item.get('timestamp')),
        'total_sites_checked': search_item.get('total_sites_checked', 0)
    }
    
    # Store in session for viewing with proper structure
    session_search_id = f"history_{search_id}"
    search_results[session_search_id] = results
    
    # Mark as completed for history view
    search_progress[session_search_id] = {
        'status': 'completed',
        'progress': 100,
        'message': translations['search_completed'],
        'completed': True
    }
    
    return render_template('results.html',
                         search_id=session_search_id,
                         translations=translations,
                         language=language,
                         is_history_view=True)

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
        user_id = session['user_id']
        
        # Check search cooldown
        can_search, cooldown_remaining = check_search_cooldown(user_id)
        if not can_search:
            flash(f"{translations['search_cooldown']} {cooldown_remaining} {translations['seconds']}", 'error')
            return redirect(url_for('index'))
        
        # Get form data
        usernames = request.form.get('usernames', '').strip()
        uploaded_file = request.files.get('json_file')
        
        # Get usernames from various sources
        username_list = []
        
        # From text input - support both newlines and commas
        if usernames:
            for line in usernames.split('\n'):
                if ',' in line:
                    # Split by comma and add each username
                    username_list.extend([u.strip() for u in line.split(',') if u.strip()])
                else:
                    # Single username per line
                    if line.strip():
                        username_list.append(line.strip())
        
        # From uploaded JSON file
        if uploaded_file and uploaded_file.filename and allowed_file(uploaded_file.filename):
            try:
                filename = secure_filename(uploaded_file.filename)
                filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
                uploaded_file.save(filepath)
                
                with open(filepath, 'r', encoding='utf-8') as f:
                    json_data = json.load(f)
                    if isinstance(json_data, list):
                        username_list.extend(json_data)
                    elif isinstance(json_data, dict) and 'usernames' in json_data:
                        username_list.extend(json_data['usernames'])
                
                os.remove(filepath)  # Clean up uploaded file
            except Exception as e:
                flash(f"Error processing JSON file: {str(e)}", 'error')
                return redirect(url_for('index'))
        
        if not username_list:
            flash(translations['error_no_usernames'], 'error')
            return redirect(url_for('index'))
        
        # Set search cooldown
        set_search_cooldown(user_id)
        
        # Get options
        options = {
            'print_all': 'print_all' in request.form,
            'print_found': 'print_found' in request.form,
            'nsfw': 'nsfw' in request.form,
            'local': 'local' in request.form,
            'timeout': request.form.get('timeout', '').strip(),
        }
        
        # Generate search ID
        search_id = f"search_{int(time.time())}"
        
        # Initialize progress tracking with proper progress system
        search_progress[search_id] = {
            'status': 'starting',
            'progress': 0,
            'message': translations['search_starting'],
            'completed': False,
            'current_site': '',
            'total_sites': 0,
            'sites_checked': 0
        }
        
        # For testing, create progressive mock results
        if username_list[0].lower() in ['test', 'demo', 'example']:
            logging.info(f"Creating test results with progressive updates for search_id: {search_id}")
            
            # Start background thread for progressive test updates
            def simulate_test_progress():
                import time
                
                # Simulate progressive search
                progress_steps = [
                    (10, 'Iniciando verificação...', 'GitHub'),
                    (25, 'Verificando redes sociais principais...', 'Twitter'),
                    (50, 'Expandindo busca...', 'LinkedIn'),
                    (75, 'Finalizando verificações...', 'Instagram'),
                    (90, 'Processando resultados...', ''),
                    (100, translations['search_completed'], '')
                ]
                
                for progress, message, current_site in progress_steps:
                    search_progress[search_id].update({
                        'progress': progress,
                        'message': message,
                        'current_site': current_site,
                        'sites_checked': int(progress / 25) if progress < 100 else 3
                    })
                    time.sleep(1)  # 1 second delay between updates
                
                # Create final test results
                test_results = {
                    'usernames': username_list,
                    'found_profiles': [
                        {
                            'username': username_list[0],
                            'site': 'GitHub',
                            'url': f'https://github.com/{username_list[0]}',
                            'status': 'found',
                            'response_time': 150
                        },
                        {
                            'username': username_list[0],
                            'site': 'Twitter',
                            'url': f'https://twitter.com/{username_list[0]}',
                            'status': 'found',
                            'response_time': 200
                        }
                    ],
                    'not_found_profiles': [
                        {
                            'username': username_list[0],
                            'site': 'LinkedIn',
                            'url': '',
                            'status': 'not_found',
                            'response_time': 100
                        }
                    ],
                    'search_timestamp': datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                    'total_sites_checked': 3,
                    'options_used': options
                }
                
                search_results[search_id] = test_results
                search_progress[search_id].update({
                    'status': 'completed',
                    'progress': 100,
                    'message': translations['search_completed'],
                    'completed': True,
                    'total_sites': 3,
                    'sites_checked': 3
                })
                
                # Save to user history
                auth_manager.save_user_search_history(user_id, {
                    'search_id': search_id,
                    'usernames': username_list,
                    'search_timestamp': test_results['search_timestamp'],
                    'total_sites_checked': test_results['total_sites_checked'],
                    'found_profiles': test_results['found_profiles'],
                    'not_found_profiles': test_results['not_found_profiles']
                })
            
            # Start simulation thread
            thread = threading.Thread(target=simulate_test_progress)
            thread.daemon = True
            thread.start()
        else:
            # Start real search in background thread
            def run_search():
                try:
                    runner = SherlockRunner()
                    results = runner.run_search(username_list, options, search_id, search_progress, translations)
                    search_results[search_id] = results
                    search_progress[search_id]['status'] = 'completed'
                    search_progress[search_id]['progress'] = 100
                    search_progress[search_id]['message'] = translations['search_completed']
                    search_progress[search_id]['completed'] = True
                    
                    # Save to user history
                    auth_manager.save_user_search_history(user_id, {
                        'search_id': search_id,
                        'usernames': username_list,
                        'search_timestamp': results.get('search_timestamp'),
                        'total_sites_checked': results.get('total_sites_checked', 0),
                        'found_profiles': results.get('found_profiles', []),
                        'not_found_profiles': results.get('not_found_profiles', [])
                    })
                    
                except Exception as e:
                    logging.error(f"Search error: {str(e)}")
                    search_progress[search_id]['status'] = 'error'
                    search_progress[search_id]['message'] = f"Error: {str(e)}"
                    search_progress[search_id]['completed'] = True
            
            thread = threading.Thread(target=run_search)
            thread.daemon = True
            thread.start()
        
        return render_template('results.html', 
                             search_id=search_id,
                             translations=translations,
                             language=language)
        
    except Exception as e:
        logging.error(f"Search route error: {str(e)}")
        flash(f"Error: {str(e)}", 'error')
        return redirect(url_for('index'))

@app.route('/progress/<search_id>')
def get_progress(search_id):
    if search_id in search_progress:
        return jsonify(search_progress[search_id])
    return jsonify({'status': 'not_found', 'message': 'Search not found'}), 404

@app.route('/results/<search_id>')
def get_results(search_id):
    if search_id in search_results:
        return jsonify(search_results[search_id])
    return jsonify({'error': 'Results not found'}), 404

@app.route('/download/<search_id>/json')
def download_json(search_id):
    try:
        if search_id not in search_results:
            return "Resultados não encontrados", 404
        
        results = search_results[search_id]
        language = session.get('language', 'en')
        
        export_utils = ExportUtils(language)
        filename = export_utils.export_json(results, search_id)
        
        return send_file(filename, as_attachment=True, download_name=f'sherlock_results_{search_id}.json')
        
    except Exception as e:
        logging.error(f"JSON download error: {str(e)}")
        return f"Erro ao fazer download: {str(e)}", 500

@app.route('/download/<search_id>/csv')
def download_csv(search_id):
    try:
        if search_id not in search_results:
            return "Resultados não encontrados", 404
        
        results = search_results[search_id]
        language = session.get('language', 'en')
        
        export_utils = ExportUtils(language)
        filename = export_utils.export_csv(results, search_id)
        
        return send_file(filename, as_attachment=True, download_name=f'sherlock_results_{search_id}.csv')
        
    except Exception as e:
        logging.error(f"CSV download error: {str(e)}")
        return f"Erro ao fazer download: {str(e)}", 500

@app.route('/download/<search_id>/pdf')
def download_pdf(search_id):
    try:
        if search_id not in search_results:
            return "Resultados não encontrados", 404
        
        results = search_results[search_id]
        language = session.get('language', 'en')
        
        export_utils = ExportUtils(language)
        filename = export_utils.export_pdf(results, search_id)
        
        return send_file(filename, as_attachment=True, download_name=f'sherlock_results_{search_id}.pdf')
        
    except Exception as e:
        logging.error(f"PDF download error: {str(e)}")
        return f"Erro ao fazer download: {str(e)}", 500

@app.route('/download/<search_id>/txt')
def download_txt(search_id):
    try:
        if search_id not in search_results:
            return "Resultados não encontrados", 404
        
        results = search_results[search_id]
        language = session.get('language', 'en')
        
        export_utils = ExportUtils(language)
        filename = export_utils.export_txt(results, search_id)
        
        return send_file(filename, as_attachment=True, download_name=f'sherlock_results_{search_id}.txt')
        
    except Exception as e:
        logging.error(f"TXT download error: {str(e)}")
        return f"Erro ao fazer download: {str(e)}", 500

@app.route('/download/<search_id>/zip')
def download_zip(search_id):
    try:
        if search_id not in search_results:
            return "Resultados não encontrados", 404
        
        results = search_results[search_id]
        language = session.get('language', 'en')
        
        export_utils = ExportUtils(language)
        filename = export_utils.export_zip_simple(results, search_id)
        
        return send_file(filename, as_attachment=True, download_name=f'sherlock_results_{search_id}.zip')
        
    except Exception as e:
        logging.error(f"ZIP download error: {str(e)}")
        return f"Erro ao fazer download: {str(e)}", 500

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

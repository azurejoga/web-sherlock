import os
import json
import threading
import time
from datetime import datetime
from flask import Flask, render_template, request, jsonify, send_file, session, redirect, url_for, flash
from werkzeug.utils import secure_filename
import logging

from sherlock_runner import SherlockRunner
from export_utils import ExportUtils
from translations import get_translations, get_supported_languages

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

# Global variables for tracking search progress
search_progress = {}
search_results = {}

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

@app.route('/')
def index():
    language = session.get('language', 'pt')
    translations = get_translations(language)
    return render_template('index.html', 
                         translations=translations, 
                         language=language,
                         languages=get_supported_languages())

@app.route('/set_language/<language>')
def set_language(language):
    if language in get_supported_languages():
        session['language'] = language
    return redirect(url_for('index'))

@app.route('/search', methods=['POST'])
def search():
    try:
        language = session.get('language', 'pt')
        translations = get_translations(language)
        
        # Get form data
        usernames = request.form.get('usernames', '').strip()
        uploaded_file = request.files.get('json_file')
        
        # Get usernames from various sources
        username_list = []
        
        # From text input
        if usernames:
            username_list.extend([u.strip() for u in usernames.split('\n') if u.strip()])
        
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
        
        # Initialize progress tracking
        search_progress[search_id] = {
            'status': 'starting',
            'progress': 0,
            'message': translations['search_starting'],
            'completed': False
        }
        
        # For testing, create mock results immediately
        if username_list[0].lower() in ['test', 'demo', 'example']:
            logging.info(f"Creating test results for search_id: {search_id}")
            # Create test results immediately
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
            search_progress[search_id] = {
                'status': 'completed',
                'progress': 100,
                'message': translations['search_completed'],
                'completed': True
            }
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
            logging.error(f"Search results not found for ID: {search_id}")
            return "Resultados não encontrados", 404
        
        results = search_results[search_id]
        language = session.get('language', 'pt')
        
        logging.info(f"Creating JSON download for search_id: {search_id}")
        
        # Create JSON content directly
        import json
        from translations import get_translations
        translations = get_translations(language)
        
        # Translate status fields
        translated_results = results.copy()
        
        for profile in translated_results.get('found_profiles', []):
            if profile['status'] == 'found':
                profile['status'] = translations['found']
        
        for profile in translated_results.get('not_found_profiles', []):
            if profile['status'] == 'not_found':
                profile['status'] = translations['not_found']
        
        json_content = json.dumps(translated_results, indent=2, ensure_ascii=False)
        
        # Create response with proper headers
        from flask import Response
        response = Response(
            json_content,
            mimetype='application/json',
            headers={
                'Content-Disposition': f'attachment; filename=sherlock_results_{search_id}.json',
                'Content-Type': 'application/json; charset=utf-8'
            }
        )
        
        logging.info(f"JSON download successful for search_id: {search_id}")
        return response
        
    except Exception as e:
        logging.error(f"Download error: {str(e)}")
        import traceback
        traceback.print_exc()
        return f"Erro ao fazer download: {str(e)}", 500

@app.errorhandler(404)
def not_found_error(error):
    language = session.get('language', 'pt')
    translations = get_translations(language)
    return render_template('base.html', 
                         error_message=translations['error_404'],
                         translations=translations,
                         language=language), 404

@app.errorhandler(500)
def internal_error(error):
    language = session.get('language', 'pt')
    translations = get_translations(language)
    return render_template('base.html',
                         error_message=translations['error_500'],
                         translations=translations,
                         language=language), 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)

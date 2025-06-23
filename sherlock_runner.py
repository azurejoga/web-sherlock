import subprocess
import json
import os
import re
import logging
from typing import List, Dict, Any

class SherlockRunner:
    def __init__(self):
        self.sherlock_path = self._find_sherlock()
    
    def _find_sherlock(self):
        """Find Sherlock installation"""
        # Try integrated sherlock first
        integrated_path = './sherlock/sherlock_project/__main__.py'
        if os.path.exists(integrated_path):
            return integrated_path
            
        # Try common locations
        possible_paths = [
            './sherlock/sherlock.py',
            '../sherlock/sherlock.py',
            '../../sherlock/sherlock.py',
            '/usr/local/bin/sherlock',
            'sherlock'
        ]
        
        for path in possible_paths:
            if os.path.exists(path) or self._command_exists(path):
                return path
        
        return 'sherlock'  # Fallback to PATH
    
    def _command_exists(self, command):
        """Check if command exists in PATH"""
        try:
            subprocess.run(['which', command], capture_output=True, check=True)
            return True
        except subprocess.CalledProcessError:
            return False
    
    def run_search(self, usernames: List[str], options: Dict[str, Any], search_id: str, progress_tracker: Dict, translations: Dict) -> Dict:
        """Run Sherlock search with given usernames and options"""
        try:
            results = {
                'usernames': usernames,
                'found_profiles': [],
                'not_found_profiles': [],
                'search_timestamp': None,
                'total_sites_checked': 0,
                'options_used': options
            }
            
            total_usernames = len(usernames)
            
            for i, username in enumerate(usernames):
                # Update progress
                progress = int((i / total_usernames) * 90)  # Reserve 10% for final processing
                progress_tracker[search_id]['progress'] = progress
                progress_tracker[search_id]['message'] = f"{translations['searching_user']} {username}..."
                
                user_results = self._search_username(username, options)
                
                # Process results for this username
                for site_name, site_data in user_results.items():
                    profile_data = {
                        'username': username,
                        'site': site_name,
                        'url': site_data.get('url', ''),
                        'status': site_data.get('status', 'unknown'),
                        'response_time': site_data.get('response_time', 0)
                    }
                    
                    if site_data.get('status') == 'found':
                        results['found_profiles'].append(profile_data)
                    else:
                        results['not_found_profiles'].append(profile_data)
            
            # Final processing
            progress_tracker[search_id]['progress'] = 95
            progress_tracker[search_id]['message'] = translations['processing_results']
            
            results['total_sites_checked'] = len(results['found_profiles']) + len(results['not_found_profiles'])
            results['search_timestamp'] = self._get_timestamp()
            
            return results
            
        except Exception as e:
            logging.error(f"Sherlock search error: {str(e)}")
            raise e
    
    def _search_username(self, username: str, options: Dict[str, Any]) -> Dict:
        """Search for a single username using Sherlock"""
        try:
            # Build command
            if self.sherlock_path.endswith('__main__.py'):
                cmd = ['python3', '-m', 'sherlock_project.sherlock']
                # Set working directory to sherlock folder
                working_dir = './sherlock'
            else:
                cmd = ['python3', self.sherlock_path]
                working_dir = None
            
            # Add options
            if options.get('print_all'):
                cmd.append('--print-all')
            if options.get('print_found'):
                cmd.append('--print-found')
            if options.get('nsfw'):
                cmd.append('--nsfw')
            if options.get('local'):
                cmd.append('--local')
            
            if options.get('timeout'):
                cmd.extend(['--timeout', str(options['timeout'])])
            
            # Always add no-color for better parsing
            cmd.append('--no-color')
            
            # Add username
            cmd.append(username)
            
            # Run command
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=300, cwd=working_dir)
            
            # Parse output
            return self._parse_sherlock_output(result.stdout, result.stderr, username)
            
        except subprocess.TimeoutExpired:
            logging.warning(f"Sherlock search timed out for username: {username}")
            return {f"timeout_error": {"status": "timeout", "url": "", "response_time": 0}}
        except Exception as e:
            logging.error(f"Error searching username {username}: {str(e)}")
            return {f"error": {"status": "error", "url": "", "response_time": 0, "error": str(e)}}
    
    def _parse_sherlock_output(self, stdout: str, stderr: str, username: str) -> Dict:
        """Parse Sherlock command output"""
        results = {}
        
        try:
            # Split output into lines
            lines = stdout.split('\n')
            
            for line in lines:
                line = line.strip()
                if not line:
                    continue
                
                # Look for site results
                # Sherlock typically outputs: [+] Site: URL or [-] Site: Not Found
                if line.startswith('[+]'):
                    # Found profile
                    match = re.search(r'\[?\+\]?\s*([^:]+):\s*(.+)', line)
                    if match:
                        site_name = match.group(1).strip()
                        url = match.group(2).strip()
                        results[site_name] = {
                            'status': 'found',
                            'url': url,
                            'response_time': 0
                        }
                elif line.startswith('[-]'):
                    # Not found
                    match = re.search(r'\[?\-\]?\s*([^:]+):', line)
                    if match:
                        site_name = match.group(1).strip()
                        results[site_name] = {
                            'status': 'not_found',
                            'url': '',
                            'response_time': 0
                        }
                elif 'http' in line and not line.startswith('['):
                    # Direct URL output
                    parts = line.split()
                    if len(parts) >= 2:
                        site_name = parts[0]
                        url = parts[1] if parts[1].startswith('http') else line
                        results[site_name] = {
                            'status': 'found',
                            'url': url,
                            'response_time': 0
                        }
            
            # If no results parsed, create fallback entries
            if not results:
                # Try to find URLs in output
                url_pattern = r'https?://[^\s]+'
                urls = re.findall(url_pattern, stdout)
                
                for i, url in enumerate(urls):
                    site_name = self._extract_site_name(url)
                    results[site_name] = {
                        'status': 'found',
                        'url': url,
                        'response_time': 0
                    }
            
        except Exception as e:
            logging.error(f"Error parsing Sherlock output: {str(e)}")
            results['parse_error'] = {
                'status': 'error',
                'url': '',
                'response_time': 0,
                'error': str(e)
            }
        
        return results
    
    def _extract_site_name(self, url: str) -> str:
        """Extract site name from URL"""
        try:
            from urllib.parse import urlparse
            parsed = urlparse(url)
            domain = parsed.netloc
            # Remove 'www.' if present
            if domain.startswith('www.'):
                domain = domain[4:]
            return domain.split('.')[0].title()
        except:
            return "Unknown"
    
    def _get_timestamp(self) -> str:
        """Get current timestamp"""
        from datetime import datetime
        return datetime.now().strftime("%Y-%m-%d %H:%M:%S")

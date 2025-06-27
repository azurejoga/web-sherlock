import subprocess
import json
import os
import re
import logging
from typing import List, Dict, Any, Optional
from datetime import datetime
from concurrent.futures import ThreadPoolExecutor, as_completed
import multiprocessing

class SherlockRunner:
    def __init__(self):
        self.sherlock_path = self._find_sherlock()
        self.working_dir = self._get_working_dir()
        
    def _find_sherlock(self):
        """Find Sherlock installation"""
        # Check integrated sherlock
        integrated_path = './sherlock/sherlock_project/__main__.py'
        if os.path.exists(integrated_path):
            return 'sherlock_project'
            
        return 'sherlock_project'  # Default fallback
    
    def _get_working_dir(self):
        """Get working directory for Sherlock"""
        if os.path.exists('./sherlock/sherlock_project/__main__.py'):
            return './sherlock'
        return './sherlock'
    
    def run_search(self, usernames: List[str], options: Dict[str, Any], 
                  search_id: str, history_manager=None, username_owner: Optional[str] = None) -> Dict:
        """Run UNIFIED Sherlock search - single search for ALL usernames"""
        try:
            logging.info(f"Starting UNIFIED search for {len(usernames)} usernames in ONE operation")
            
            results = {
                'usernames': usernames,
                'found_profiles': [],
                'not_found_profiles': [],
                'search_timestamp': self._get_timestamp(),
                'total_sites_checked': 0,
                'options_used': options,
                'search_id': search_id
            }
            
            # Execute SINGLE unified search with ALL usernames
            unified_results = self._search_all_usernames_unified(usernames, options)
            
            # Process all results from unified search
            for username, user_results in unified_results.items():
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
            
            logging.info(f"UNIFIED search completed: {len(results['found_profiles'])} found from all usernames")
            
            # Final processing
            results['total_sites_checked'] = len(results['found_profiles']) + len(results['not_found_profiles'])
            
            # Save results immediately - SINGLE save operation
            if history_manager and username_owner:
                try:
                    # Save results to file
                    results_file = f'results/sherlock_results_{search_id}.json'
                    os.makedirs('results', exist_ok=True)
                    
                    with open(results_file, 'w', encoding='utf-8') as f:
                        json.dump(results, f, indent=2, ensure_ascii=False)
                    
                    # Update search status in history ONCE
                    history_manager.update_search_status(
                        username_owner, 
                        search_id,
                        'completed',
                        results['total_sites_checked'],
                        len(results['found_profiles']),
                        results_file
                    )
                    
                    logging.info(f"UNIFIED results saved for search {search_id}")
                    
                except Exception as e:
                    logging.error(f"Error saving unified results: {str(e)}")
            
            logging.info(f"UNIFIED search completed: {len(results['found_profiles'])} found, {len(results['not_found_profiles'])} not found")
            return results
            
        except Exception as e:
            logging.error(f"UNIFIED search error: {str(e)}")
            return {
                'usernames': usernames,
                'found_profiles': [],
                'not_found_profiles': [],
                'search_timestamp': self._get_timestamp(),
                'total_sites_checked': 0,
                'options_used': options,
                'search_id': search_id,
                'error': str(e)
            }
    
    def _search_all_usernames_unified(self, usernames: List[str], options: Dict[str, Any]) -> Dict:
        """Execute single Sherlock command with all usernames at once"""
        try:
            # Build command with all usernames
            cmd = ['python3', '-m', self.sherlock_path]
            
            # Optimize timeout - 3 seconds per site for balanced speed and completeness
            cmd.extend(['--timeout', '3'])
            cmd.append('--no-color')
            
            # Add options - CORRECTED logic for print_all
            if options.get('print_all', False):
                cmd.append('--print-all')
            elif options.get('print_found', False):
                cmd.append('--print-found')
            
            if options.get('nsfw', False):
                cmd.append('--nsfw')
            if options.get('local', False):
                cmd.append('--local')
                
            # Add ALL usernames to single command
            cmd.extend(usernames)
            
            logging.info(f"UNIFIED command with {len(usernames)} usernames: {' '.join(cmd[:10])}...")
            
            # Execute single command with all usernames - Longer timeout for multiple users
            total_timeout = max(60, len(usernames) * 15)  # At least 15 seconds per username
            result = subprocess.run(
                cmd, 
                capture_output=True, 
                text=True, 
                timeout=total_timeout,
                cwd=self.working_dir
            )
            
            logging.info(f"Sherlock command completed with return code: {result.returncode}")
            
            # Parse unified output
            return self._parse_unified_output(result.stdout, result.stderr, usernames)
            
        except subprocess.TimeoutExpired:
            logging.warning(f"Unified search timeout for {len(usernames)} usernames")
            # Return empty results for all usernames
            return {username: {} for username in usernames}
        except Exception as e:
            logging.error(f"Unified search error: {str(e)}")
            # Return empty results for all usernames
            return {username: {} for username in usernames}

    def _parse_unified_output(self, stdout: str, stderr: str, usernames: List[str]) -> Dict:
        """Parse output from unified search with multiple usernames - IMPROVED parser"""
        results = {username: {} for username in usernames}
        
        try:
            lines = stdout.split('\n')
            
            # Debug output
            logging.info(f"Parsing output with {len(lines)} lines for {len(usernames)} usernames")
            if len(lines) < 50:  # Only log if output is short
                logging.debug(f"Output lines: {lines[:20]}")
            
            # Method 1: Parse each line looking for patterns
            for line in lines:
                line = line.strip()
                if not line:
                    continue
                
                # Look for [+] found results with username
                if line.startswith('[+]'):
                    match = re.search(r'\[\+\]\s*([^:]+):\s*(https?://[^\s]+)', line)
                    if match:
                        site_name = match.group(1).strip()
                        url = match.group(2).strip()
                        
                        # Try to determine which username this belongs to
                        matched_username = None
                        for username in usernames:
                            if username.lower() in url.lower() or username in url:
                                matched_username = username
                                break
                        
                        # If no match in URL, check if line contains username
                        if not matched_username:
                            for username in usernames:
                                if username.lower() in line.lower():
                                    matched_username = username
                                    break
                        
                        # If still no match, assign to first username (fallback)
                        if not matched_username and usernames:
                            matched_username = usernames[0]
                        
                        if matched_username:
                            results[matched_username][site_name] = {
                                'status': 'found',
                                'url': url,
                                'response_time': 0
                            }
                
                # Look for [-] not found results
                elif line.startswith('[-]'):
                    match = re.search(r'\[-\]\s*([^:]+):', line)
                    if match:
                        site_name = match.group(1).strip()
                        
                        # Try to determine which username this belongs to
                        matched_username = None
                        for username in usernames:
                            if username.lower() in line.lower():
                                matched_username = username
                                break
                        
                        # If no match, assign to first username (fallback)
                        if not matched_username and usernames:
                            matched_username = usernames[0]
                        
                        if matched_username:
                            results[matched_username][site_name] = {
                                'status': 'not_found',
                                'url': '',
                                'response_time': 0
                            }
            
            # Method 2: If no results found, try alternative parsing
            total_results = sum(len(user_results) for user_results in results.values())
            if total_results == 0:
                logging.warning("No results found with method 1, trying alternative parsing")
                
                # Look for any URLs in the output and distribute them among usernames
                urls = re.findall(r'https?://[^\s]+', stdout)
                logging.info(f"Found {len(urls)} URLs in alternative parsing")
                
                for i, url in enumerate(urls):
                    site_name = self._extract_site_name(url)
                    username_index = i % len(usernames)  # Distribute URLs among usernames
                    username = usernames[username_index]
                    
                    if site_name not in results[username]:
                        results[username][site_name] = {
                            'status': 'found',
                            'url': url,
                            'response_time': 0
                        }
            
            # Log results summary
            for username, user_results in results.items():
                found_count = sum(1 for result in user_results.values() if result.get('status') == 'found')
                not_found_count = sum(1 for result in user_results.values() if result.get('status') == 'not_found')
                logging.info(f"Username '{username}': {found_count} found, {not_found_count} not found")
            
        except Exception as e:
            logging.error(f"Error parsing unified output: {str(e)}")
        
        return results


    
    def _parse_sherlock_output(self, stdout: str, stderr: str, username: str) -> Dict:
        """Parse Sherlock command output"""
        results = {}
        
        try:
            lines = stdout.split('\n')
            
            for line in lines:
                line = line.strip()
                if not line:
                    continue
                
                # Look for [+] found results
                if line.startswith('[+]'):
                    # Pattern: [+] SiteName: https://example.com/user
                    match = re.search(r'\[\+\]\s*([^:]+):\s*(https?://[^\s]+)', line)
                    if match:
                        site_name = match.group(1).strip()
                        url = match.group(2).strip()
                        results[site_name] = {
                            'status': 'found',
                            'url': url,
                            'response_time': 0
                        }
                
                # Look for [-] not found results (if print-all was used)
                elif line.startswith('[-]'):
                    match = re.search(r'\[\-\]\s*([^:]+):', line)
                    if match:
                        site_name = match.group(1).strip()
                        results[site_name] = {
                            'status': 'not_found',
                            'url': '',
                            'response_time': 0
                        }
                
                # Look for direct URLs without [+] prefix
                elif 'http' in line and not line.startswith('['):
                    # Try to extract site and URL
                    url_match = re.search(r'https?://[^\s]+', line)
                    if url_match:
                        url = url_match.group(0)
                        site_name = self._extract_site_name(url)
                        results[site_name] = {
                            'status': 'found',
                            'url': url,
                            'response_time': 0
                        }
            
            # If no results found, try alternative parsing
            if not results:
                # Look for any URLs in the output
                urls = re.findall(r'https?://[^\s]+', stdout)
                for url in urls:
                    site_name = self._extract_site_name(url)
                    if site_name not in results:
                        results[site_name] = {
                            'status': 'found',
                            'url': url,
                            'response_time': 0
                        }
            
            logging.info(f"Parsed {len(results)} results for {username}")
            
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
            domain = parsed.netloc.lower()
            
            # Remove 'www.' prefix
            if domain.startswith('www.'):
                domain = domain[4:]
            
            # Get main domain name
            parts = domain.split('.')
            if len(parts) >= 2:
                return parts[0].title()
            return domain.title()
            
        except Exception:
            return "Unknown"
    
    def _get_timestamp(self) -> str:
        """Get current timestamp"""
        return datetime.now().strftime("%Y-%m-%d %H:%M:%S")
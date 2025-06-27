import csv
import json
import os
import zipfile
from datetime import datetime
from io import StringIO
import logging

try:
    from reportlab.pdfgen import canvas
    from reportlab.lib.pagesizes import letter, A4
    from reportlab.lib.units import inch
    REPORTLAB_AVAILABLE = True
except ImportError:
    REPORTLAB_AVAILABLE = False
    logging.warning("ReportLab not available. PDF export will be limited.")

from translations import get_translations

class ExportUtils:
    def __init__(self, language='en'):
        self.language = language
        self.translations = get_translations(language)
        self.results_folder = 'results'
        os.makedirs(self.results_folder, exist_ok=True)
    
    def export_csv(self, results, search_id):
        """Export results to CSV format"""
        from flask import Response
        from io import StringIO
        
        # Create CSV content in memory
        output = StringIO()
        fieldnames = ['username', 'site', 'url', 'status', 'response_time']
        writer = csv.DictWriter(output, fieldnames=fieldnames)
        
        # Write header
        header_row = {
            'username': self.translations['username'],
            'site': self.translations['social_network'],
            'url': self.translations['profile_url'],
            'status': self.translations['status'],
            'response_time': self.translations['response_time']
        }
        writer.writerow(header_row)
        
        # Write found profiles
        for profile in results.get('found_profiles', []):
            writer.writerow({
                'username': profile['username'],
                'site': profile['site'],
                'url': profile['url'],
                'status': self.translations['found'],
                'response_time': profile.get('response_time', 0)
            })
        
        # Write not found profiles
        for profile in results.get('not_found_profiles', []):
            writer.writerow({
                'username': profile['username'],
                'site': profile['site'],
                'url': profile['url'],
                'status': self.translations['not_found'],
                'response_time': profile.get('response_time', 0)
            })
        
        csv_content = output.getvalue()
        output.close()
        
        # Create response with proper headers
        response = Response(
            csv_content,
            mimetype='text/csv',
            headers={
                'Content-Disposition': f'attachment; filename=sherlock_results_{search_id}.csv',
                'Content-Type': 'text/csv; charset=utf-8'
            }
        )
        
        return response
    
    def export_pdf(self, results, search_id):
        """Export results to PDF format"""
        from flask import Response
        from io import BytesIO
        
        if REPORTLAB_AVAILABLE:
            return self._export_pdf_reportlab(results, search_id)
        else:
            return self._export_pdf_simple(results, search_id)
    
    def _export_pdf_reportlab(self, results, search_id):
        """Export PDF using ReportLab"""
        from flask import Response
        from io import BytesIO
        from reportlab.pdfgen import canvas
        from reportlab.lib.pagesizes import A4
        
        try:
            buffer = BytesIO()
            c = canvas.Canvas(buffer, pagesize=A4)
            width, height = A4
            
            # Title
            c.setFont("Helvetica-Bold", 16)
            c.drawString(50, height - 50, f"{self.translations['search_results']} - Web Sherlock")
            
            # Timestamp
            c.setFont("Helvetica", 10)
            timestamp = results.get('search_timestamp', datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
            c.drawString(50, height - 70, f"{self.translations['timestamp']}: {timestamp}")
            
            # Summary
            c.setFont("Helvetica", 12)
            y_position = height - 100
            
            total_found = len(results.get('found_profiles', []))
            total_not_found = len(results.get('not_found_profiles', []))
            
            c.drawString(50, y_position, f"{self.translations['usernames_searched']}: {', '.join(results.get('usernames', []))}")
            y_position -= 20
            c.drawString(50, y_position, f"{self.translations['profiles_found']}: {total_found}")
            y_position -= 20
            c.drawString(50, y_position, f"{self.translations['profiles_not_found']}: {total_not_found}")
            y_position -= 40
            
            # Found profiles section
            if total_found > 0:
                c.setFont("Helvetica-Bold", 14)
                c.drawString(50, y_position, self.translations['found_profiles'])
                y_position -= 20
                
                c.setFont("Helvetica", 10)
                for profile in results.get('found_profiles', []):
                    if y_position < 50:  # New page if needed
                        c.showPage()
                        y_position = height - 50
                    
                    c.drawString(60, y_position, f"{profile['username']} @ {profile['site']}")
                    y_position -= 15
                    c.drawString(70, y_position, profile['url'])
                    y_position -= 25
            
            c.save()
            
            pdf_content = buffer.getvalue()
            buffer.close()
            
            # Create response
            response = Response(
                pdf_content,
                mimetype='application/pdf',
                headers={
                    'Content-Disposition': f'attachment; filename=sherlock_results_{search_id}.pdf',
                    'Content-Type': 'application/pdf'
                }
            )
            
            return response
            
        except Exception as e:
            logging.error(f"Error creating PDF with ReportLab: {str(e)}")
            return self._export_pdf_simple(results, search_id)
    
    def _export_pdf_simple(self, results, search_id):
        """Simple PDF export (fallback)"""
        from flask import Response
        
        # Create a simple text content as PDF fallback
        txt_content = self._generate_text_content(results)
        
        # Create response with PDF headers (text content as fallback)
        response = Response(
            txt_content,
            mimetype='application/pdf',
            headers={
                'Content-Disposition': f'attachment; filename=sherlock_results_{search_id}.pdf',
                'Content-Type': 'application/pdf'
            }
        )
        
        return response
    
    def export_txt(self, results, search_id):
        """Export results to TXT format"""
        from flask import Response
        
        content = self._generate_text_content(results)
        
        # Create response with proper headers
        response = Response(
            content,
            mimetype='text/plain',
            headers={
                'Content-Disposition': f'attachment; filename=sherlock_results_{search_id}.txt',
                'Content-Type': 'text/plain; charset=utf-8'
            }
        )
        
        return response
    
    def _generate_text_content(self, results):
        """Generate text content for TXT and simple PDF export"""
        content = []
        
        # Header
        content.append(f"{self.translations['search_results']} - Web Sherlock")
        content.append("=" * 50)
        
        # Timestamp
        timestamp = results.get('search_timestamp', datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
        content.append(f"{self.translations['timestamp']}: {timestamp}")
        content.append("")
        
        # Summary
        total_found = len(results.get('found_profiles', []))
        total_not_found = len(results.get('not_found_profiles', []))
        
        content.append(f"{self.translations['usernames_searched']}: {', '.join(results.get('usernames', []))}")
        content.append(f"{self.translations['profiles_found']}: {total_found}")
        content.append(f"{self.translations['profiles_not_found']}: {total_not_found}")
        content.append("")
        
        # Found profiles
        if total_found > 0:
            content.append(f"{self.translations['found_profiles']}:")
            content.append("-" * 30)
            
            for profile in results.get('found_profiles', []):
                content.append(f"• {profile['username']} @ {profile['site']}")
                content.append(f"  {self.translations['profile_url']}: {profile['url']}")
                content.append("")
        
        # Not found profiles
        if total_not_found > 0:
            content.append(f"{self.translations['not_found_profiles']}:")
            content.append("-" * 30)
            
            for profile in results.get('not_found_profiles', []):
                content.append(f"• {profile['username']} @ {profile['site']}")
            content.append("")
        
        return '\n'.join(content)
    
    def export_zip_simple(self, results, search_id):
        """Export CSV and JSON formats in a ZIP file with security enhancements"""
        from flask import Response
        from io import BytesIO, StringIO
        import json
        import re
        
        try:
            # Sanitize search_id to prevent path traversal
            safe_search_id = re.sub(r'[^\w\-_]', '', str(search_id))
            if not safe_search_id:
                safe_search_id = 'results'
            
            # Create ZIP content in memory
            zip_buffer = BytesIO()
            
            # Define secure file list - only known, controlled filenames
            files_to_zip = []
            
            with zipfile.ZipFile(zip_buffer, 'w', zipfile.ZIP_DEFLATED) as zipf:
                # Generate CSV content
                csv_output = StringIO()
                fieldnames = ['username', 'site', 'url', 'status', 'response_time']
                writer = csv.DictWriter(csv_output, fieldnames=fieldnames)
                
                # Write CSV header
                header_row = {
                    'username': self.translations['username'],
                    'site': self.translations['social_network'],
                    'url': self.translations['profile_url'],
                    'status': self.translations['status'],
                    'response_time': self.translations['response_time']
                }
                writer.writerow(header_row)
                
                # Write CSV data with input validation
                for profile in results.get('found_profiles', []):
                    # Sanitize profile data
                    safe_profile = {
                        'username': str(profile.get('username', ''))[:100],
                        'site': str(profile.get('site', ''))[:100],
                        'url': str(profile.get('url', ''))[:500],
                        'status': self.translations['found'],
                        'response_time': profile.get('response_time', 0)
                    }
                    writer.writerow(safe_profile)
                
                for profile in results.get('not_found_profiles', []):
                    # Sanitize profile data
                    safe_profile = {
                        'username': str(profile.get('username', ''))[:100],
                        'site': str(profile.get('site', ''))[:100],
                        'url': str(profile.get('url', ''))[:500],
                        'status': self.translations['not_found'],
                        'response_time': profile.get('response_time', 0)
                    }
                    writer.writerow(safe_profile)
                
                # Secure filename for CSV
                csv_filename = f'sherlock_results_{safe_search_id}.csv'
                zipf.writestr(csv_filename, csv_output.getvalue())
                files_to_zip.append(csv_filename)
                csv_output.close()
                
                # Generate JSON content with data sanitization
                translated_results = results.copy()
                
                # Sanitize JSON data
                if 'found_profiles' in translated_results:
                    for profile in translated_results['found_profiles']:
                        profile['username'] = str(profile.get('username', ''))[:100]
                        profile['site'] = str(profile.get('site', ''))[:100]
                        profile['url'] = str(profile.get('url', ''))[:500]
                        if profile.get('status') == 'found':
                            profile['status'] = self.translations['found']
                
                if 'not_found_profiles' in translated_results:
                    for profile in translated_results['not_found_profiles']:
                        profile['username'] = str(profile.get('username', ''))[:100]
                        profile['site'] = str(profile.get('site', ''))[:100]
                        profile['url'] = str(profile.get('url', ''))[:500]
                        if profile.get('status') == 'not_found':
                            profile['status'] = self.translations['not_found']
                
                json_content = json.dumps(translated_results, indent=2, ensure_ascii=False)
                
                # Secure filename for JSON
                json_filename = f'sherlock_results_{safe_search_id}.json'
                zipf.writestr(json_filename, json_content)
                files_to_zip.append(json_filename)
            
            zip_content = zip_buffer.getvalue()
            zip_buffer.close()
            
            # Secure response headers
            safe_filename = f'sherlock_results_{safe_search_id}.zip'
            response = Response(
                zip_content,
                mimetype='application/zip',
                headers={
                    'Content-Disposition': f'attachment; filename="{safe_filename}"',
                    'Content-Type': 'application/zip',
                    'Content-Security-Policy': "default-src 'none'",
                    'X-Content-Type-Options': 'nosniff',
                    'Cache-Control': 'no-cache, no-store, must-revalidate'
                }
            )
            
            logging.info(f"Secure ZIP export created: {len(files_to_zip)} files")
            return response
            
        except Exception as e:
            logging.exception("Secure ZIP export failed")
            raise e

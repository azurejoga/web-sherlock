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
    def __init__(self, language='pt'):
        self.language = language
        self.translations = get_translations(language)
        self.results_folder = 'results'
        os.makedirs(self.results_folder, exist_ok=True)
    
    def export_csv(self, results, search_id):
        """Export results to CSV format"""
        filename = os.path.join(self.results_folder, f"sherlock_results_{search_id}.csv")
        
        with open(filename, 'w', newline='', encoding='utf-8') as csvfile:
            fieldnames = ['username', 'site', 'url', 'status', 'response_time']
            writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
            
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
        
        return filename
    
    def export_json(self, results, search_id):
        """Export results to JSON format"""
        filename = os.path.join(self.results_folder, f"sherlock_results_{search_id}.json")
        
        # Translate status fields
        translated_results = results.copy()
        
        for profile in translated_results.get('found_profiles', []):
            if profile['status'] == 'found':
                profile['status'] = self.translations['found']
        
        for profile in translated_results.get('not_found_profiles', []):
            if profile['status'] == 'not_found':
                profile['status'] = self.translations['not_found']
        
        with open(filename, 'w', encoding='utf-8') as jsonfile:
            json.dump(translated_results, jsonfile, indent=2, ensure_ascii=False)
        
        return filename
    
    def export_pdf(self, results, search_id):
        """Export results to PDF format"""
        filename = os.path.join(self.results_folder, f"sherlock_results_{search_id}.pdf")
        
        if REPORTLAB_AVAILABLE:
            return self._export_pdf_reportlab(results, filename)
        else:
            return self._export_pdf_simple(results, filename)
    
    def _export_pdf_reportlab(self, results, filename):
        """Export PDF using ReportLab"""
        try:
            from reportlab.pdfgen import canvas
            from reportlab.lib.pagesizes import A4
            
            c = canvas.Canvas(filename, pagesize=A4)
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
            return filename
            
        except Exception as e:
            logging.error(f"Error creating PDF with ReportLab: {str(e)}")
            return self._export_pdf_simple(results, filename)
    
    def _export_pdf_simple(self, results, filename):
        """Simple PDF export (fallback)"""
        # Create a simple text file as PDF fallback
        txt_content = self._generate_text_content(results)
        
        # Save as text file with .pdf extension for simplicity
        with open(filename, 'w', encoding='utf-8') as f:
            f.write(txt_content)
        
        return filename
    
    def export_txt(self, results, search_id):
        """Export results to TXT format"""
        filename = os.path.join(self.results_folder, f"sherlock_results_{search_id}.txt")
        
        content = self._generate_text_content(results)
        
        with open(filename, 'w', encoding='utf-8') as txtfile:
            txtfile.write(content)
        
        return filename
    
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
        """Export all formats in a ZIP file"""
        zip_filename = os.path.join(self.results_folder, f"sherlock_results_{search_id}.zip")
        
        try:
            # Generate all export files
            csv_file = self.export_csv(results, search_id)
            json_file = self.export_json(results, search_id)
            txt_file = self.export_txt(results, search_id)
            pdf_file = self.export_pdf(results, search_id)
            
            # Create ZIP file with all formats
            with zipfile.ZipFile(zip_filename, 'w', zipfile.ZIP_DEFLATED) as zipf:
                files_to_zip = [
                    (csv_file, f"sherlock_results_{search_id}.csv"),
                    (json_file, f"sherlock_results_{search_id}.json"),
                    (txt_file, f"sherlock_results_{search_id}.txt"),
                    (pdf_file, f"sherlock_results_{search_id}.pdf")
                ]
                
                for file_path, archive_name in files_to_zip:
                    if os.path.exists(file_path):
                        zipf.write(file_path, archive_name)
            
            # Clean up individual files
            for file_path, _ in files_to_zip:
                try:
                    if os.path.exists(file_path):
                        os.remove(file_path)
                except OSError:
                    pass
            
            return zip_filename
            
        except Exception as e:
            logging.error(f"Error creating ZIP file: {str(e)}")
            raise e

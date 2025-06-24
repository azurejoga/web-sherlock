import csv
import json
import os
import zipfile
from datetime import datetime
import logging
import tempfile
from io import StringIO

try:
    from reportlab.pdfgen import canvas
    from reportlab.lib.pagesizes import A4
    REPORTLAB_AVAILABLE = True
except ImportError:
    REPORTLAB_AVAILABLE = False
    logging.warning("ReportLab not available. PDF export will be limited.")

from translations import get_translations

class ExportUtils:
    def __init__(self, language='pt'):
        self.language = language
        self.translations = get_translations(language)
        self.results_folder = os.path.abspath('results')
        os.makedirs(self.results_folder, exist_ok=True)

    def _sanitize_filename(self, name):
        return ''.join(c for c in name if c.isalnum() or c in ('-', '_'))

    def export_csv(self, results, search_id):
        filename = os.path.join(self.results_folder, f"sherlock_results_{self._sanitize_filename(search_id)}.csv")

        try:
            with open(filename, 'w', newline='', encoding='utf-8') as csvfile:
                fieldnames = ['username', 'site', 'url', 'status', 'response_time']
                writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
                writer.writerow({
                    'username': self.translations['username'],
                    'site': self.translations['social_network'],
                    'url': self.translations['profile_url'],
                    'status': self.translations['status'],
                    'response_time': self.translations['response_time']
                })
                for profile in results.get('found_profiles', []):
                    writer.writerow({
                        'username': profile['username'],
                        'site': profile['site'],
                        'url': profile['url'],
                        'status': self.translations['found'],
                        'response_time': profile.get('response_time', 0)
                    })
                for profile in results.get('not_found_profiles', []):
                    writer.writerow({
                        'username': profile['username'],
                        'site': profile['site'],
                        'url': profile['url'],
                        'status': self.translations['not_found'],
                        'response_time': profile.get('response_time', 0)
                    })
        except Exception as e:
            logging.exception(f"Failed to export CSV: {e}")
            raise

        return filename

    def export_json(self, results, search_id):
        filename = os.path.join(self.results_folder, f"sherlock_results_{self._sanitize_filename(search_id)}.json")
        try:
            results_copy = json.loads(json.dumps(results))
            for profile in results_copy.get('found_profiles', []):
                profile['status'] = self.translations['found']
            for profile in results_copy.get('not_found_profiles', []):
                profile['status'] = self.translations['not_found']

            with open(filename, 'w', encoding='utf-8') as f:
                json.dump(results_copy, f, indent=2, ensure_ascii=False)
        except Exception as e:
            logging.exception(f"Failed to export JSON: {e}")
            raise

        return filename

    def export_txt(self, results, search_id):
        filename = os.path.join(self.results_folder, f"sherlock_results_{self._sanitize_filename(search_id)}.txt")
        content = self._generate_text_content(results)

        try:
            with open(filename, 'w', encoding='utf-8') as f:
                f.write(content)
        except Exception as e:
            logging.exception(f"Failed to export TXT: {e}")
            raise

        return filename

    def export_pdf(self, results, search_id):
        filename = os.path.join(self.results_folder, f"sherlock_results_{self._sanitize_filename(search_id)}.pdf")

        if REPORTLAB_AVAILABLE:
            try:
                return self._export_pdf_reportlab(results, filename)
            except Exception as e:
                logging.error(f"PDF export with ReportLab failed: {e}")

        return self._export_pdf_simple(results, filename)

    def _export_pdf_reportlab(self, results, filename):
        c = canvas.Canvas(filename, pagesize=A4)
        width, height = A4
        y = height - 50

        c.setFont("Helvetica-Bold", 14)
        c.drawString(50, y, f"{self.translations['search_results']} - Web Sherlock")
        y -= 20

        c.setFont("Helvetica", 10)
        timestamp = results.get('search_timestamp', datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
        c.drawString(50, y, f"{self.translations['timestamp']}: {timestamp}")
        y -= 30

        total_found = len(results.get('found_profiles', []))
        total_not_found = len(results.get('not_found_profiles', []))
        usernames = ', '.join(results.get('usernames', []))

        c.drawString(50, y, f"{self.translations['usernames_searched']}: {usernames}")
        y -= 20
        c.drawString(50, y, f"{self.translations['profiles_found']}: {total_found}")
        y -= 20
        c.drawString(50, y, f"{self.translations['profiles_not_found']}: {total_not_found}")
        y -= 30

        c.setFont("Helvetica", 9)
        for profile in results.get('found_profiles', []):
            if y < 60:
                c.showPage()
                y = height - 50
            c.drawString(60, y, f"{profile['username']} @ {profile['site']}")
            y -= 15
            c.drawString(70, y, profile['url'])
            y -= 25

        c.save()
        return filename

    def _export_pdf_simple(self, results, filename):
        content = self._generate_text_content(results)
        try:
            with open(filename, 'w', encoding='utf-8') as f:
                f.write(content)
        except Exception as e:
            logging.exception(f"Failed to write fallback PDF (TXT): {e}")
            raise
        return filename

    def _generate_text_content(self, results):
        lines = [
            f"{self.translations['search_results']} - Web Sherlock",
            "=" * 50,
            f"{self.translations['timestamp']}: {results.get('search_timestamp', datetime.now().strftime('%Y-%m-%d %H:%M:%S'))}",
            "",
            f"{self.translations['usernames_searched']}: {', '.join(results.get('usernames', []))}",
            f"{self.translations['profiles_found']}: {len(results.get('found_profiles', []))}",
            f"{self.translations['profiles_not_found']}: {len(results.get('not_found_profiles', []))}",
            ""
        ]

        if results.get('found_profiles'):
            lines.append(f"{self.translations['found_profiles']}:\n" + "-" * 30)
            for profile in results['found_profiles']:
                lines.append(f"- {profile['username']} @ {profile['site']}")
                lines.append(f"  {self.translations['profile_url']}: {profile['url']}\n")

        if results.get('not_found_profiles'):
            lines.append(f"{self.translations['not_found_profiles']}:\n" + "-" * 30)
            for profile in results['not_found_profiles']:
                lines.append(f"- {profile['username']} @ {profile['site']}")

        return '\n'.join(lines)

    def export_zip_simple(self, results, search_id):
        zip_filename = os.path.join(self.results_folder, f"sherlock_results_{self._sanitize_filename(search_id)}.zip")

        try:
            csv_file = self.export_csv(results, search_id)
            json_file = self.export_json(results, search_id)
            txt_file = self.export_txt(results, search_id)
            pdf_file = self.export_pdf(results, search_id)

            with zipfile.ZipFile(zip_filename, 'w', zipfile.ZIP_DEFLATED) as zipf:
                for f in [csv_file, json_file, txt_file, pdf_file]:
                    if os.path.exists(f):
                        zipf.write(f, os.path.basename(f))

            for f in [csv_file, json_file, txt_file, pdf_file]:
                try:
                    if os.path.exists(f):
                        os.remove(f)
                except Exception:
                    logging.warning(f"Failed to remove temporary file: {f}")

        except Exception as e:
            logging.exception(f"ZIP export failed: {e}")
            raise

        return zip_filename

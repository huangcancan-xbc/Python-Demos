from pathlib import Path
import re
import unittest

ROOT = Path(__file__).resolve().parents[1]


class StaticUiRegressionTestCase(unittest.TestCase):
    def read(self, relative_path):
        return (ROOT / relative_path).read_text(encoding='utf-8')

    def test_css_defines_indigo_300_and_no_template_uses_primary_tokens(self):
        css = self.read('app/static/css/style.css')
        self.assertIn('--indigo-300:', css)
        for template in (ROOT / 'app/templates').rglob('*.html'):
            text = template.read_text(encoding='utf-8')
            self.assertNotIn('--primary-500', text, str(template))
            self.assertNotIn('--primary-700', text, str(template))

    def test_index_intro_has_single_style_attribute(self):
        html = self.read('app/templates/index.html')
        intro_line = next(line for line in html.splitlines() if 'max-width' in line)
        self.assertLessEqual(intro_line.count('style='), 1)

    def test_personal_settings_is_not_empty_hash_link(self):
        html = self.read('app/templates/base.html')
        self.assertNotIn('href="#"><i class="bi bi-person-gear', html)

    def test_forms_do_not_disable_native_validation(self):
        for relative_path in [
            'app/templates/login.html',
            'app/templates/register.html',
            'app/templates/exam/form.html',
            'app/templates/classroom/form.html',
            'app/templates/arrangement/create.html',
        ]:
            self.assertNotIn('novalidate', self.read(relative_path), relative_path)

    def test_seat_maps_have_scroll_wrapper(self):
        for relative_path in [
            'app/templates/classroom/detail.html',
            'app/templates/arrangement/detail.html',
        ]:
            self.assertIn('seat-map-scroll', self.read(relative_path), relative_path)

    def test_progress_bar_text_is_not_inside_progress_bar(self):
        html = self.read('app/templates/arrangement/detail.html')
        self.assertNotRegex(html, re.compile(r'<div class="progress-bar"[^>]*>\s*已分配', re.S))

    def test_core_templates_do_not_use_bootstrap_badge_backgrounds(self):
        for template in (ROOT / 'app/templates').rglob('*.html'):
            text = template.read_text(encoding='utf-8')
            self.assertNotIn('badge bg-', text, str(template))


if __name__ == '__main__':
    unittest.main()

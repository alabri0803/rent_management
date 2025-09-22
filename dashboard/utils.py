from io import BytesIO
from django.http import HttpResponse
from django.template.loader import get_template
from xhtml2pdf import pisa
from django.utils.translation import gettext as _
import os
from django.conf import settings
from django.contrib.staticfiles import finders

def link_callback(uri, rel):
    """
    حل مبسط للمشكلة
    """
    if uri.endswith('.ttf') and 'fonts' in uri:
        # بناء المسار يدوياً للخطوط
        font_path = os.path.join(settings.BASE_DIR, 'static', 'fonts', 'Amiri-Regular.ttf')
        if os.path.exists(font_path):
            return font_path

    # للملفات الأخرى، استخدم المسار الطبيعي
    result = finders.find(uri)
    if result:
        return result
    return uri

def font_to_base64(font_path):
    """تحويل الخط إلى base64"""
    try:
        with open(font_path, 'rb') as font_file:
            font_data = font_file.read()
            return base64.b64encode(font_data).decode('utf-8')
    except:
        return None
        
def render_to_pdf(template_path: str, context: dict) -> HttpResponse:
        # إضافة الخط كـ base64 إلى context
    font_path = finders.find('fonts/Amiri-Regular.ttf')
    if font_path:
        font_base64 = font_to_base64(font_path)
        context['amiri_font_base64'] = font_base64

    template = get_template(template_path)
    html = template.render(context)
    result = BytesIO()
    # Ensure you have a font that supports Arabic installed on your system or provide a path to a .ttf file.
    pdf = pisa.pisaDocument(BytesIO(html.encode("UTF-8")), result)
    if not pdf.err:
        return HttpResponse(result.getvalue(), content_type='application/pdf')
    return HttpResponse(_("We had some errors") + f"<pre>{html}</pre>")
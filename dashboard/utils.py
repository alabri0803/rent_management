from io import BytesIO
from django.http import HttpResponse
from django.template.loader import get_template
from xhtml2pdf import pisa
from django.utils.translation import gettext as _
import os
from django.conf import settings
from django.contrib.staticfiles import finders
import base64

def link_callback(uri, rel):
    """
    حل متقدم لدعم الخطوط العربية مع تحسينات
    """
    # للخطوط العربية
    if uri.startswith('fonts/') or uri.endswith(('.ttf', '.otf', '.woff', '.woff2')):
        font_name = os.path.basename(uri)

        # البحث في مجلدات متعددة
        possible_paths = [
            finders.find(f'fonts/{font_name}'),
            finders.find(f'static/fonts/{font_name}'),
            os.path.join(settings.BASE_DIR, 'static', 'fonts', font_name),
            os.path.join(settings.BASE_DIR, 'staticfiles', 'fonts', font_name),
            os.path.join(settings.STATIC_ROOT, 'fonts', font_name) if settings.STATIC_ROOT else None,
            os.path.join(settings.BASE_DIR, 'fonts', font_name),
        ]

        for path in possible_paths:
            if path and os.path.exists(path):
                return path

        print(f"Font not found: {font_name}")

    # للصور
    if uri.startswith('images/') or uri.endswith(('.png', '.jpg', '.jpeg', '.gif')):
        result = finders.find(uri)
        if result:
            return result

    # للروابط المطلقة
    if uri.startswith('http'):
        return uri

    # البحث العام
    result = finders.find(uri)
    if result:
        return result

    return None

def font_to_base64(font_path):
    """تحويل الخط إلى base64"""
    try:
        with open(font_path, 'rb') as font_file:
            font_data = font_file.read()
            return base64.b64encode(font_data).decode('utf-8')
    except Exception as e:
        print(f"Error converting font to base64: {e}")
        return None

def get_system_fonts_stack():
    """
    إرجاع سلسلة خطوط النظام الكاملة
    """
    return (
        "'Scheherazade New', 'Traditional Arabic', 'Arial', 'Times New Roman', sans-serif"
    )

def get_arabic_fonts_stack():
    """
    إرجاع سلسلة خطوط عربية كاملة
    """
    return (
        "'Scheherazade New', 'Traditional Arabic', 'Amiri', 'Lateef', 'Arial', sans-serif"
    )

def get_monospace_fonts_stack():
    """
    إرجاع سلسلة خطوط Monospace
    """
    return (
        "'Courier New', 'Monaco', 'Menlo', 'Ubuntu Mono', monospace"
    )

def get_comprehensive_fonts_context():
    """
    إرجاع جميع سلاسل الخطوط للإستخدام في القوالب
    """
    return {
        'system_fonts_stack': get_system_fonts_stack(),
        'arabic_fonts_stack': get_arabic_fonts_stack(),
        'monospace_fonts_stack': get_monospace_fonts_stack(),
        'safe_fonts_stack': get_arabic_fonts_stack(),
        'serif_fonts_stack': "'Times New Roman', 'Georgia', 'Traditional Arabic', serif",
    }

def load_all_fonts():
    """
    تحميل جميع الخطوط المتاحة
    """
    font_base64_data = {}

    # الخطوط العربية الأساسية (يجب أن تكون موجودة في مجلد static/fonts/)
    arabic_fonts = [
        'ScheherazadeNew-Regular.ttf',
        'Traditional-Arabic.ttf',
        'Amiri-Regular.ttf',
        'Lateef-Regular.ttf',
        'Arial.ttf',
        'Times-New-Roman.ttf',
        'Courier-New.ttf',
    ]

    for font_name in arabic_fonts:
        font_path = None

        # البحث في مسارات متعددة
        possible_paths = [
            finders.find(f'fonts/{font_name}'),
            os.path.join(settings.BASE_DIR, 'static', 'fonts', font_name),
            os.path.join(settings.BASE_DIR, 'staticfiles', 'fonts', font_name),
            os.path.join(settings.BASE_DIR, 'fonts', font_name),
        ]

        for path in possible_paths:
            if path and os.path.exists(path):
                font_path = path
                break

        if font_path and os.path.exists(font_path):
            font_base64 = font_to_base64(font_path)
            font_key = font_name.replace('-', '_').replace('.', '_').lower()
            font_base64_data[f'{font_key}_base64'] = font_base64
            font_base64_data[f'{font_key}_name'] = font_name.replace('.ttf', '')
            font_base64_data[f'{font_key}_available'] = True
            print(f"Font loaded successfully: {font_name}")
        else:
            font_key = font_name.replace('-', '_').replace('.', '_').lower()
            font_base64_data[f'{font_key}_available'] = False
            print(f"Font not found: {font_name}")

    return font_base64_data

def render_to_pdf(template_path: str, context: dict) -> HttpResponse:
    # تحميل جميع سلاسل الخطوط
    fonts_context = get_comprehensive_fonts_context()
    context.update(fonts_context)

    # تحميل الخطوط كبيانات base64
    font_base64_data = load_all_fonts()
    context.update(font_base64_data)

    # إضافة معلومات إضافية للقالب
    context.update({
        'pdf_generation': True,
        'rtl_direction': True,
        'language': 'ar',
        'static_url': settings.STATIC_URL,
    })

    template = get_template(template_path)
    html = template.render(context)
    result = BytesIO()

    # إنشاء PDF مع callback للخطوط
    pdf = pisa.pisaDocument(
        BytesIO(html.encode('UTF-8')), 
        result, 
        encoding='UTF-8',
        link_callback=link_callback
    )

    if not pdf.err:
        response = HttpResponse(result.getvalue(), content_type='application/pdf')
        filename = context.get('filename', 'document.pdf')
        response['Content-Disposition'] = f'inline; filename="{filename}"'
        return response
    else:
        return HttpResponse(_("حدث خطأ في إنشاء PDF") + f"<pre>{pdf.err}</pre>")

def generate_pdf_response(template_path, context=None, filename=None):
    """
    دالة مساعدة لإنشاء PDF مع الخطوط الكاملة
    """
    if context is None:
        context = {}

    if filename:
        context['filename'] = filename

    return render_to_pdf(template_path, context)
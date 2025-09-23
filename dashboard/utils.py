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
    حل متقدم لدعم الخطوط العربية
    """
    # للخطوط العربية
    if uri.startswith('fonts/') or uri.endswith(('.ttf', '.otf')):
        font_name = os.path.basename(uri)
        font_path = finders.find(f'fonts/{font_name}')
        if font_path:
            return font_path

        # البحث في مجلدات متعددة
        possible_paths = [
            os.path.join(settings.BASE_DIR, 'static', 'fonts', font_name),
            os.path.join(settings.BASE_DIR, 'staticfiles', 'fonts', font_name),
            os.path.join(settings.STATIC_ROOT, 'fonts', font_name) if settings.STATIC_ROOT else None,
        ]

        for path in possible_paths:
            if path and os.path.exists(path):
                return path

    # للصور والملفات الأخرى
    result = finders.find(uri)
    if result:
        if not isinstance(result, (list, tuple)):
            return result
        else:
            return result[0] if result else None

    # للروابط المطلقة
    if uri.startswith('http'):
        return uri

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
        'Scheherazade',
    )

def get_arabic_fonts_stack():
    """
    إرجاع سلسلة خطوط عربية كاملة
    """
    return (
        'Scheherazade',
    )

def get_monospace_fonts_stack():
    """
    إرجاع سلسلة خطوط Monospace
    """
    return (
        'Scheherazade',
    )

def get_comprehensive_fonts_context():
    """
    إرجاع جميع سلاسل الخطوط للإستخدام في القوالب
    """
    return {
        'system_fonts_stack': get_system_fonts_stack(),
        'arabic_fonts_stack': get_arabic_fonts_stack(),
        'monospace_fonts_stack': get_monospace_fonts_stack(),
        'safe_fonts_stack': 'Scheherazade',
        'serif_fonts_stack': 'Scheherazade',
    }

def load_all_fonts():
    """
    تحميل جميع الخطوط المتاحة
    """
    font_base64_data = {}

    # الخطوط العربية الأساسية
    arabic_fonts = [
        'Scheherazade-Regular.tt',
    ]

    # الخطوط النظامية الإضافية
    system_fonts = [
        'Scheherazade-Regular.tt',
    ]

    all_fonts = list(set(arabic_fonts + system_fonts))

    for font_name in all_fonts:
        font_path = finders.find(f'fonts/{font_name}')
        if not font_path:
            # البحث في مسارات أخرى
            possible_paths = [
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
        else:
            font_key = font_name.replace('-', '_').replace('.', '_').lower()
            font_base64_data[f'{font_key}_available'] = False

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

# دالة مساعدة للاستخدام السريع
def generate_pdf_response(template_path, context=None, filename=None):
    """
    دالة مساعدة لإنشاء PDF مع الخطوط الكاملة
    """
    if context is None:
        context = {}

    if filename:
        context['filename'] = filename

    return render_to_pdf(template_path, context)
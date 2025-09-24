# utils/pdf_utils.py
from io import BytesIO
from django.http import HttpResponse
from django.template.loader import get_template
from xhtml2pdf import pisa
from django.utils.translation import gettext as _
import os
from django.conf import settings
from django.contrib.staticfiles import finders
import base64
import logging

# إعداد logger للتتبع
logger = logging.getLogger(__name__)

def link_callback(uri, rel):
    """
    حل متقدم لدعم الخطوط العربية مع تحسينات
    """
    try:
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
                os.path.join('/usr/share/fonts/truetype/', font_name),  # للمسارات النظامية
            ]

            for path in possible_paths:
                if path and os.path.exists(path):
                    logger.info(f"Font found: {path}")
                    return path

            logger.warning(f"Font not found: {font_name}")

        # للصور
        elif uri.startswith('images/') or uri.endswith(('.png', '.jpg', '.jpeg', '.gif', '.bmp')):
            result = finders.find(uri)
            if result:
                return result
            else:
                # البحث في مسارات مطلقة
                if uri.startswith('/'):
                    return uri

        # للروابط المطلقة
        elif uri.startswith('http://') or uri.startswith('https://'):
            return uri

        # البحث العام في static files
        result = finders.find(uri)
        if result:
            return result

    except Exception as e:
        logger.error(f"Error in link_callback: {e}")

    return None

def font_to_base64(font_path):
    """تحويل الخط إلى base64"""
    try:
        with open(font_path, 'rb') as font_file:
            font_data = font_file.read()
            return base64.b64encode(font_data).decode('utf-8')
    except Exception as e:
        logger.error(f"Error converting font to base64: {e}")
        return None

def get_system_fonts_stack():
    """
    إرجاع سلسلة خطوط النظام الكاملة
    """
    return (
        "'Scheherazade New', 'Traditional Arabic', 'Amiri', 'Lateef', 'Arial', 'Times New Roman', sans-serif"
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

def get_serif_fonts_stack():
    """
    إرجاع سلسلة خطوط Serif
    """
    return (
        "'Times New Roman', 'Georgia', 'Traditional Arabic', serif"
    )

def get_comprehensive_fonts_context():
    """
    إرجاع جميع سلاسل الخطوط للإستخدام في القوالب
    """
    return {
        'system_fonts_stack': get_system_fonts_stack(),
        'arabic_fonts_stack': get_arabic_fonts_stack(),
        'monospace_fonts_stack': get_monospace_fonts_stack(),
        'serif_fonts_stack': get_serif_fonts_stack(),
        'safe_fonts_stack': get_arabic_fonts_stack(),
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
        'Roboto-Regular.ttf',  # إضافة Roboto للغة الإنجليزية
    ]

    for font_name in arabic_fonts:
        font_path = None

        # البحث في مسارات متعددة
        possible_paths = [
            finders.find(f'fonts/{font_name}'),
            os.path.join(settings.BASE_DIR, 'static', 'fonts', font_name),
            os.path.join(settings.BASE_DIR, 'staticfiles', 'fonts', font_name),
            os.path.join(settings.BASE_DIR, 'fonts', font_name),
            os.path.join('/usr/share/fonts/truetype/', font_name),
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
            logger.info(f"Font loaded successfully: {font_name}")
        else:
            font_key = font_name.replace('-', '_').replace('.', '_').lower()
            font_base64_data[f'{font_key}_available'] = False
            logger.warning(f"Font not found: {font_name}")

    return font_base64_data

def check_fonts_availability():
    """
    التحقق من توفر الخطوط المطلوبة
    """
    required_fonts = [
        'ScheherazadeNew-Regular.ttf',
        'Traditional-Arabic.ttf',
        'Arial.ttf',
    ]

    available_fonts = []
    missing_fonts = []

    for font_name in required_fonts:
        font_path = finders.find(f'fonts/{font_name}')
        if font_path and os.path.exists(font_path):
            available_fonts.append(font_name)
        else:
            missing_fonts.append(font_name)

    return {
        'available': available_fonts,
        'missing': missing_fonts,
        'all_available': len(missing_fonts) == 0
    }

def render_to_pdf(template_path: str, context: dict) -> HttpResponse:
    """
    دالة رئيسية لتحويل HTML إلى PDF
    """
    try:
        # تحميل جميع سلاسل الخطوط
        fonts_context = get_comprehensive_fonts_context()
        context.update(fonts_context)

        # تحميل الخطوط كبيانات base64
        font_base64_data = load_all_fonts()
        context.update(font_base64_data)

        # التحقق من توفر الخطوط
        font_status = check_fonts_availability()
        context['font_status'] = font_status

        # إضافة معلومات إضافية للقالب
        context.update({
            'pdf_generation': True,
            'rtl_direction': True,
            'language': 'ar',
            'static_url': settings.STATIC_URL,
            'media_url': settings.MEDIA_URL,
        })

        # تحميل وتصيير القالب
        template = get_template(template_path)
        html = template.render(context)
        result = BytesIO()

        # إعدادات إنشاء PDF
        pdf_options = {
            'encoding': 'UTF-8',
            'link_callback': link_callback
        }

        # إنشاء PDF
        pdf = pisa.pisaDocument(
            BytesIO(html.encode('UTF-8')), 
            result, 
            **pdf_options
        )

        if not pdf.err:
            response = HttpResponse(result.getvalue(), content_type='application/pdf')
            filename = context.get('filename', 'document.pdf')
            response['Content-Disposition'] = f'inline; filename="{filename}"'

            # إضافة headers إضافية
            response['X-PDF-Generated-By'] = 'Django xhtml2pdf'
            response['X-PDF-Fonts-Available'] = str(font_status['all_available'])

            logger.info(f"PDF generated successfully: {filename}")
            return response
        else:
            logger.error(f"PDF generation error: {pdf.err}")
            error_html = f"""
            <html>
            <body>
                <h1>خطأ في إنشاء PDF</h1>
                <p>حدث خطأ أثناء إنشاء الملف PDF:</p>
                <pre>{pdf.err}</pre>
                <h2>تفاصيل الخطأ:</h2>
                <p>القالب: {template_path}</p>
                <p>الحالة: {font_status}</p>
            </body>
            </html>
            """
            return HttpResponse(error_html, status=500)

    except Exception as e:
        logger.error(f"Unexpected error in render_to_pdf: {e}")
        error_html = f"""
        <html>
        <body>
            <h1>خطأ غير متوقع</h1>
            <p>حدث خطأ غير متوقع: {str(e)}</p>
        </body>
        </html>
        """
        return HttpResponse(error_html, status=500)

def generate_pdf_response(template_path, context=None, filename=None):
    """
    دالة مساعدة لإنشاء PDF مع الخطوط الكاملة
    """
    if context is None:
        context = {}

    if filename:
        context['filename'] = filename

    return render_to_pdf(template_path, context)

def create_simple_pdf(html_content, filename="document.pdf"):
    """
    دالة لإنشاء PDF من محتوى HTML مباشر
    """
    try:
        result = BytesIO()

        pdf = pisa.pisaDocument(
            BytesIO(html_content.encode('UTF-8')), 
            result, 
            encoding='UTF-8',
            link_callback=link_callback
        )

        if not pdf.err:
            response = HttpResponse(result.getvalue(), content_type='application/pdf')
            response['Content-Disposition'] = f'inline; filename="{filename}"'
            return response
        else:
            return HttpResponse(f"Error generating PDF: {pdf.err}")

    except Exception as e:
        return HttpResponse(f"Error: {str(e)}")

# دالة مساعدة لتحويل الأرقام إلى كلمات عربية
def number_to_arabic_words(number):
    """
    تحويل الأرقام إلى كلمات عربية (مبسطة)
    يمكن استبدالها بمكتبة متخصصة
    """
    try:
        units = ['', 'واحد', 'اثنان', 'ثلاثة', 'أربعة', 'خمسة', 'ستة', 'سبعة', 'ثمانية', 'تسعة']
        tens = ['', 'عشرة', 'عشرون', 'ثلاثون', 'أربعون', 'خمسون', 'ستون', 'سبعون', 'ثمانون', 'تسعون']
        hundreds = ['', 'مائة', 'مئتان', 'ثلاثمائة', 'أربعمائة', 'خمسمائة', 'ستمائة', 'سبعمائة', 'ثمانمائة', 'تسعمائة']

        if number == 0:
            return "صفر"

        # تحويل إلى عدد صحيح
        integer_part = int(number)
        decimal_part = round((number - integer_part) * 100)

        words = []

        # معالجة الأجزاء (يمكن تطوير هذه الدالة)
        if integer_part > 0:
            words.append(f"{integer_part}")

        if decimal_part > 0:
            words.append(f"و {decimal_part} فلس")

        result = " ".join(words)
        return result + " ريال عماني"

    except Exception as e:
        logger.error(f"Error converting number to words: {e}")
        return f"{number} ريال عماني"
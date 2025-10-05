from io import BytesIO
from django.http import HttpResponse
from django.template.loader import get_template
from django.utils.translation import gettext as _
from django.conf import settings
import logging

logger = logging.getLogger(__name__)

# الدالة الرئيسية لتوليد PDF
def generate_pdf_receipt(template_path: str, context: dict) -> HttpResponse:
    """
    دالة ذكية تحاول استخدام WeasyPrint أولاً ثم xhtml2pdf كبديل
    """
    try:
        # حاول استخدام WeasyPrint أولاً (أفضل للعربية)
        return render_to_pdf_weasyprint(template_path, context)
    except ImportError:
        # إذا لم يكن WeasyPrint متاحاً، استخدم xhtml2pdf
        return render_to_pdf(template_path, context)

# باستخدام WeasyPrint (موصى به للعربية)
def render_to_pdf_weasyprint(template_path: str, context: dict) -> HttpResponse:
    try:
        from weasyprint import HTML
        import tempfile

        template = get_template(template_path)
        html = template.render(context)

        # إنشاء ملف PDF
        pdf_file = HTML(string=html, base_url=settings.BASE_DIR).write_pdf()

        response = HttpResponse(pdf_file, content_type='application/pdf')
        response['Content-Disposition'] = f'inline; filename="receipt_{context.get("payment").id}.pdf"'
        return response

    except Exception as e:
        # في حالة الخطأ، نرجع HTML للتصحيح
        template = get_template(template_path)
        html = template.render(context)
        return HttpResponse(f"Error generating PDF with WeasyPrint: {str(e)}<hr>{html}")

# باستخدام xhtml2pdf (بديل)
def render_to_pdf(template_path: str, context: dict) -> HttpResponse:
    try:
        from xhtml2pdf import pisa

        template = get_template(template_path)
        html = template.render(context)

        result = BytesIO()
        pdf = pisa.pisaDocument(BytesIO(html.encode("UTF-8")), result)

        if not pdf.err:
            response = HttpResponse(result.getvalue(), content_type='application/pdf')
            response['Content-Disposition'] = f'inline; filename="receipt_{context.get("payment").id}.pdf"'
            return response
        else:
            return HttpResponse(f"PDF generation error: {pdf.err}")

    except Exception as e:
        template = get_template(template_path)
        html = template.render(context)
        return HttpResponse(f"Error generating PDF: {str(e)}<hr>{html}")


def auto_translate_to_english(arabic_text):
    """
    ترجمة تلقائية من العربية إلى الإنجليزية
    """
    if not arabic_text or not arabic_text.strip():
        return ""
    
    try:
        from deep_translator import GoogleTranslator
        translator = GoogleTranslator(source='ar', target='en')
        translation = translator.translate(arabic_text)
        return translation
    except Exception as e:
        logger.error(f"Translation error: {str(e)}")
        return arabic_text
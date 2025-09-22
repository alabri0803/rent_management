# utils_weasyprint.py
from django.http import HttpResponse
from django.template.loader import render_to_string
from weasyprint import HTML, CSS
from weasyprint.text.fonts import FontConfiguration

def render_to_pdf_weasyprint(template_path, context):
    html_string = render_to_string(template_path, context)

    font_config = FontConfiguration()
    css = CSS(string='''
        @font-face {
            font-family: 'Amiri';
            src: url('{% static "fonts/Amiri-Regular.ttf" %}');
        }
        body {
            font-family: 'Amiri', sans-serif;
            direction: rtl;
            text-align: right;
        }
        .en {
            direction: ltr;
            text-align: left;
            font-family: Arial, sans-serif;
        }
    ''', font_config=font_config)

    response = HttpResponse(content_type='application/pdf')
    response['Content-Disposition'] = 'filename="lease_cancellation.pdf"'

    HTML(string=html_string).write_pdf(
        response, 
        stylesheets=[css], 
        font_config=font_config
    )

    return response
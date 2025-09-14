from io import BytesIO
from django.http import HttpResponse
from django.template.loader import get_template
from xhtml2pdf import pisa
from django.utils.translation import gettext_lazy as _

def render_to_pdf(template_path: str, context: dict) -> HttpResponse:
  template = get_template(template_path)
  html = template.render(context)
  result = BytesIO()
  pdf = pisa.pisaDocument(BytesIO(html.encode("UTF-8")), result)
  if not pdf.err:
    return HttpResponse(result.getvalue(), content_type='application/pdf')
  return HttpResponse(_('We had some errors<pre>') + html + f"</pre>{html}</pre>")
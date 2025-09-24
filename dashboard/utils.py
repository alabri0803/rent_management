from io import BytesIO
from django.http import HttpResponse
from django.template.loader import get_template
from xhtml2pdf import pisa
from django.utils.translation import gettext as _
from django.conf import settings
import os

def link_callback(uri, rel):
    """
    Convert HTML URIs to absolute system paths so xhtml2pdf can access those
    resources
    """
    # use short variable names
    sUrl = settings.STATIC_URL      # Typically /static/
    sRoot = settings.STATIC_ROOT    # Typically /home/userX/project_static/
    mUrl = settings.MEDIA_URL       # Typically /media/
    mRoot = settings.MEDIA_ROOT     # Typically /home/userX/project_media/

    # convert URIs to absolute system paths
    if uri.startswith(mUrl):
        path = os.path.join(mRoot, uri.replace(mUrl, ""))
    elif uri.startswith(sUrl):
        path = os.path.join(sRoot, uri.replace(sUrl, ""))
    else:
        return uri  # handle absolute uri (e.g. http://some.tld/foo.png)

    # make sure that file exists
    if not os.path.isfile(path):
            raise Exception(
                'media URI must start with %s or %s' % (sUrl, mUrl)
            )
    return path

def render_to_pdf(template_path: str, context: dict) -> HttpResponse:
    template = get_template(template_path)
    html = template.render(context)
    result = BytesIO()

    # Pass the link_callback to pisaDocument to handle static files (like fonts)
    pdf = pisa.pisaDocument(BytesIO(html.encode("UTF-8")), result, link_callback=link_callback)

    if not pdf.err:
        return HttpResponse(result.getvalue(), content_type='application/pdf')
    return HttpResponse(_("We had some errors") + f"<pre>{html}</pre>")
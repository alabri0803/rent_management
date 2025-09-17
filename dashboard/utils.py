from io import BytesIO
from django.http import HttpResponse
from django.template.loader import get_template
from xhtml2pdf import pisa
from django.utils.translation import gettext as _

def render_to_pdf(template_path: str, context: dict) -> HttpResponse:
    template = get_template(template_path)
    html = template.render(context)
    result = BytesIO()
    # Ensure you have a font that supports Arabic installed on your system or provide a path to a .ttf file.
    pdf = pisa.pisaDocument(BytesIO(html.encode("UTF-8")), result)
    if not pdf.err:
        return HttpResponse(result.getvalue(), content_type='application/pdf')
    return HttpResponse(_("We had some errors") + f"<pre>{html}</pre>")
```
```eof
```python:dashboard/management/commands/update_lease_statuses.py:dashboard/management/commands/update_lease_statuses.py
from django.core.management.base import BaseCommand
from dashboard.models import Lease
from django.utils.translation import gettext as _

class Command(BaseCommand):
    help = 'Updates the status of all leases based on their end dates.'

    def handle(self, *args, **kwargs):
        self.stdout.write(self.style.SUCCESS(_('Starting lease status update process...')))
        updated_count = 0
        leases_to_check = Lease.objects.exclude(status__in=['expired', 'cancelled'])

        for lease in leases_to_check:
            original_status = lease.status
            lease.update_status() # This method is in the model
            if lease.status != original_status:
                lease.save()
                updated_count += 1
                self.stdout.write(f"  - {_('Lease')} {lease.contract_number} {_('status updated to')} {lease.get_status_display()}")

        self.stdout.write(self.style.SUCCESS(_('Process finished. Updated %(count)d leases.') % {'count': updated_count}))
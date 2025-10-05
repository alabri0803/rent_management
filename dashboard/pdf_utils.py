from reportlab.lib import colors
from reportlab.lib.pagesizes import A4, landscape
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch, cm
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer, PageBreak, Image
from reportlab.lib.enums import TA_CENTER, TA_RIGHT, TA_LEFT
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from arabic_reshaper import reshape
from bidi.algorithm import get_display
from django.http import HttpResponse
from datetime import datetime
from decimal import Decimal
import os


class PDFReportGenerator:
    """مولد تقارير PDF بتنسيق احترافي مع دعم اللغة العربية"""
    
    # ألوان النظام
    COLORS = {
        'header_bg': colors.HexColor('#4472C4'),
        'header_text': colors.white,
        'row_even': colors.HexColor('#F2F2F2'),
        'row_odd': colors.white,
        'total_bg': colors.HexColor('#D9E1F2'),
        'success_bg': colors.HexColor('#C6EFCE'),
        'warning_bg': colors.HexColor('#FCE4D6'),
    }
    
    def __init__(self, title_ar="تقرير", title_en="Report", orientation='portrait'):
        """
        تهيئة مولد التقارير
        
        Args:
            title_ar: العنوان بالعربي
            title_en: العنوان بالإنجليزي
            orientation: اتجاه الصفحة ('portrait' أو 'landscape')
        """
        self.title_ar = title_ar
        self.title_en = title_en
        self.pagesize = landscape(A4) if orientation == 'landscape' else A4
        self.elements = []
        self.styles = getSampleStyleSheet()
        self.logo_path = None
        
        # تسجيل الخطوط العربية
        self._register_fonts()
        
        # إنشاء أنماط مخصصة
        self._create_custom_styles()
    
    def _register_fonts(self):
        """تسجيل الخطوط العربية"""
        font_path = 'static/fonts/Amiri-Regular.ttf'
        if os.path.exists(font_path):
            try:
                pdfmetrics.registerFont(TTFont('Arabic', font_path))
            except:
                pass
    
    def _create_custom_styles(self):
        """إنشاء أنماط مخصصة للتقرير"""
        # نمط العنوان الرئيسي
        self.styles.add(ParagraphStyle(
            name='TitleArabic',
            parent=self.styles['Heading1'],
            fontName='Arabic',
            fontSize=20,
            alignment=TA_CENTER,
            textColor=self.COLORS['header_bg'],
            spaceAfter=12,
            leading=28
        ))
        
        self.styles.add(ParagraphStyle(
            name='TitleEnglish',
            parent=self.styles['Heading1'],
            fontSize=18,
            alignment=TA_CENTER,
            textColor=colors.HexColor('#1F4788'),
            spaceAfter=20,
            leading=24
        ))
        
        # نمط العناوين الفرعية
        self.styles.add(ParagraphStyle(
            name='SubtitleArabic',
            parent=self.styles['Heading2'],
            fontName='Arabic',
            fontSize=16,
            alignment=TA_CENTER,
            textColor=self.COLORS['header_bg'],
            spaceAfter=10,
            spaceBefore=10,
            leading=22
        ))
        
        self.styles.add(ParagraphStyle(
            name='SubtitleEnglish',
            parent=self.styles['Heading2'],
            fontSize=14,
            alignment=TA_CENTER,
            textColor=colors.HexColor('#1F4788'),
            spaceAfter=15,
            leading=18
        ))
        
        # نمط النص العربي
        self.styles.add(ParagraphStyle(
            name='NormalArabic',
            parent=self.styles['Normal'],
            fontName='Arabic',
            fontSize=11,
            alignment=TA_RIGHT,
            leading=16
        ))
    
    def set_logo(self, logo_path):
        """تعيين مسار شعار الشركة"""
        if os.path.exists(logo_path):
            self.logo_path = logo_path
        return self
    
    def add_header(self, include_logo=True):
        """إضافة ترويسة التقرير مع الشعار"""
        # إضافة الشعار إذا كان موجوداً
        if include_logo and self.logo_path:
            try:
                img = Image(self.logo_path, width=1.5*inch, height=1.5*inch)
                self.elements.append(img)
                self.elements.append(Spacer(1, 0.2*inch))
            except:
                pass
        
        # العنوان بالعربي
        title_ar = self.format_arabic(self.title_ar)
        self.elements.append(Paragraph(title_ar, self.styles['TitleArabic']))
        
        # العنوان بالإنجليزي
        self.elements.append(Paragraph(self.title_en, self.styles['TitleEnglish']))
        
        # التاريخ
        date_str = datetime.now().strftime('%Y-%m-%d %H:%M')
        date_ar = self.format_arabic(f"تاريخ التقرير: {date_str}")
        self.elements.append(Paragraph(date_ar, self.styles['NormalArabic']))
        self.elements.append(Paragraph(f"Report Date: {date_str}", self.styles['Normal']))
        
        self.elements.append(Spacer(1, 0.3*inch))
        
        return self
    
    def add_section_title(self, title_ar, title_en):
        """إضافة عنوان قسم"""
        self.elements.append(Spacer(1, 0.2*inch))
        
        title_ar_formatted = self.format_arabic(title_ar)
        self.elements.append(Paragraph(title_ar_formatted, self.styles['SubtitleArabic']))
        self.elements.append(Paragraph(title_en, self.styles['SubtitleEnglish']))
        
        self.elements.append(Spacer(1, 0.1*inch))
        
        return self
    
    def add_table(self, headers, data, col_widths=None):
        """
        إضافة جدول للتقرير
        
        Args:
            headers: قائمة العناوين (ثنائية اللغة)
            data: البيانات
            col_widths: عرض الأعمدة
        """
        if not data:
            return self
        
        # تنسيق العناوين العربية
        formatted_headers = []
        for header in headers:
            if any('\u0600' <= char <= '\u06FF' for char in str(header)):
                formatted_headers.append(Paragraph(self.format_arabic(str(header)), 
                                                  self.styles['NormalArabic']))
            else:
                formatted_headers.append(Paragraph(str(header), self.styles['Normal']))
        
        # تنسيق البيانات
        formatted_data = [formatted_headers]
        for row in data:
            formatted_row = []
            for cell in row:
                cell_str = str(cell) if cell is not None else "-"
                if any('\u0600' <= char <= '\u06FF' for char in cell_str):
                    formatted_row.append(Paragraph(self.format_arabic(cell_str), 
                                                  self.styles['NormalArabic']))
                else:
                    formatted_row.append(Paragraph(cell_str, self.styles['Normal']))
            formatted_data.append(formatted_row)
        
        # إنشاء الجدول
        if col_widths:
            table = Table(formatted_data, colWidths=col_widths)
        else:
            table = Table(formatted_data)
        
        # تنسيق الجدول
        table_style = TableStyle([
            # العناوين
            ('BACKGROUND', (0, 0), (-1, 0), self.COLORS['header_bg']),
            ('TEXTCOLOR', (0, 0), (-1, 0), self.COLORS['header_text']),
            ('ALIGN', (0, 0), (-1, 0), 'CENTER'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 11),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
            ('TOPPADDING', (0, 0), (-1, 0), 12),
            
            # البيانات
            ('ALIGN', (0, 1), (-1, -1), 'CENTER'),
            ('FONTSIZE', (0, 1), (-1, -1), 9),
            ('TOPPADDING', (0, 1), (-1, -1), 8),
            ('BOTTOMPADDING', (0, 1), (-1, -1), 8),
            
            # الحدود
            ('GRID', (0, 0), (-1, -1), 1, colors.black),
            
            # صفوف متبادلة الألوان
            ('ROWBACKGROUNDS', (0, 1), (-1, -1), 
             [self.COLORS['row_odd'], self.COLORS['row_even']]),
        ])
        
        table.setStyle(table_style)
        self.elements.append(table)
        self.elements.append(Spacer(1, 0.2*inch))
        
        return self
    
    def add_summary_table(self, data):
        """
        إضافة جدول ملخص
        
        Args:
            data: قائمة من المجاميع [(label_ar, label_en, value), ...]
        """
        formatted_data = []
        for row in data:
            if len(row) == 3:
                label_ar, label_en, value = row
                formatted_row = [
                    Paragraph(self.format_arabic(label_ar), self.styles['NormalArabic']),
                    Paragraph(label_en, self.styles['Normal']),
                    Paragraph(str(value), self.styles['Normal'])
                ]
                formatted_data.append(formatted_row)
        
        if not formatted_data:
            return self
        
        table = Table(formatted_data, colWidths=[3*inch, 3*inch, 2*inch])
        
        table_style = TableStyle([
            ('BACKGROUND', (0, 0), (-1, -1), self.COLORS['total_bg']),
            ('TEXTCOLOR', (0, 0), (-1, -1), colors.HexColor('#1F4788')),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('FONTNAME', (0, 0), (-1, -1), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, -1), 11),
            ('TOPPADDING', (0, 0), (-1, -1), 10),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 10),
            ('GRID', (0, 0), (-1, -1), 1, colors.black),
        ])
        
        table.setStyle(table_style)
        self.elements.append(table)
        self.elements.append(Spacer(1, 0.3*inch))
        
        return self
    
    def add_page_break(self):
        """إضافة فاصل صفحات"""
        self.elements.append(PageBreak())
        return self
    
    def format_arabic(self, text):
        """تنسيق النص العربي للعرض الصحيح"""
        try:
            reshaped_text = reshape(text)
            bidi_text = get_display(reshaped_text)
            return bidi_text
        except:
            return text
    
    def format_currency(self, amount):
        """تنسيق المبالغ المالية"""
        if isinstance(amount, Decimal):
            amount = float(amount)
        return f"{amount:,.2f} ر.ع"
    
    def build(self, filename=None):
        """
        بناء ملف PDF
        
        Returns:
            HttpResponse مع ملف PDF
        """
        if not filename:
            filename = f"{self.title_en.replace(' ', '_')}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf"
        
        response = HttpResponse(content_type='application/pdf')
        response['Content-Disposition'] = f'attachment; filename="{filename}"'
        
        # إنشاء المستند
        doc = SimpleDocTemplate(
            response,
            pagesize=self.pagesize,
            rightMargin=0.5*inch,
            leftMargin=0.5*inch,
            topMargin=0.5*inch,
            bottomMargin=0.5*inch
        )
        
        # بناء PDF
        doc.build(self.elements)
        
        return response

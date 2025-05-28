# views.py
from django.views.generic import DetailView, ListView

from .models import FAQ, FAQCategory


class FAQListView(ListView):
    model = FAQ
    template_name = "faq/faq_list.html"
    context_object_name = "faqs"

    def get_queryset(self):
        return FAQ.objects.filter(is_active=True).order_by("order")

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["categories"] = FAQCategory.objects.filter(is_active=True).order_by("order")
        return context


class FAQCategoryDetailView(DetailView):
    model = FAQCategory
    template_name = "faq/faq_category_detail.html"
    context_object_name = "category"

    def get_queryset(self):
        return FAQCategory.objects.filter(is_active=True)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["faqs"] = FAQ.objects.filter(category=self.object, is_active=True).order_by("order")
        context["categories"] = FAQCategory.objects.filter(is_active=True).order_by("order")
        return context


class FAQDetailView(DetailView):
    model = FAQ
    template_name = "faq/faq_detail.html"
    context_object_name = "faq"

    def get_queryset(self):
        return FAQ.objects.filter(is_active=True)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        # Obtener preguntas relacionadas explícitas
        related_faqs = self.object.related_questions.filter(is_active=True)

        # Si no hay suficientes preguntas relacionadas explícitas, añadir otras preguntas
        max_related_faqs = 5
        if related_faqs.count() < max_related_faqs:
            # Excluir la pregunta actual y las ya relacionadas
            excluded_ids = [self.object.id, *related_faqs.values_list("id", flat=True)]

            # Obtener preguntas adicionales ordenadas por su orden
            additional_faqs = (
                FAQ.objects.filter(is_active=True)
                .exclude(id__in=excluded_ids)
                .order_by("order")[: 5 - related_faqs.count()]
            )

            # Combinar resultados
            related_faqs = list(related_faqs) + list(additional_faqs)

        context["related_faqs"] = related_faqs
        return context

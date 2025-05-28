# views.py
from django.views.generic import DetailView
from django.views.generic import ListView

from .models import FAQ
from .models import FAQCategory


class FAQListView(ListView):
    model = FAQ
    template_name = "faq/faq_list.html"
    context_object_name = "faqs"

    def get_queryset(self):
        # Assuming faq.category.name (or similar FK access) is used in the template
        return FAQ.objects.filter(is_active=True).select_related("category").order_by("order")

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        # Assuming FAQCategory doesn't have frequently accessed FKs in this listing context.
        # If it had, e.g., a parent_category FK, select_related('parent_category') would be added.
        context["categories"] = FAQCategory.objects.filter(is_active=True).order_by("order")
        return context


class FAQCategoryDetailView(DetailView):
    model = FAQCategory
    template_name = "faq/faq_category_detail.html"
    context_object_name = "category"

    def get_queryset(self):
        # Assuming FAQCategory fields themselves are displayed, not deep FKs.
        # If it had, e.g., a parent_category FK, select_related('parent_category') would be added.
        return FAQCategory.objects.filter(is_active=True)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        # Assuming faq.category.name is used for FAQs listed under a category.
        # Note: category is already self.object, so select_related('category') on FAQ objects
        # might seem redundant for category name itself, but good practice if other FAQ FKs were accessed.
        context["faqs"] = (
            FAQ.objects.filter(category=self.object, is_active=True).select_related("category").order_by("order")
        )
        context["categories"] = FAQCategory.objects.filter(is_active=True).order_by("order")
        return context


class FAQDetailView(DetailView):
    model = FAQ
    template_name = "faq/faq_detail.html"
    context_object_name = "faq"

    def get_queryset(self):
        # Assuming the main faq object might display its category (faq.category.name)
        return FAQ.objects.filter(is_active=True).select_related("category")

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        # Obtener preguntas relacionadas explícitas
        # Assuming related_faq.category.name might be accessed in the template
        related_faqs_qs = self.object.related_questions.filter(is_active=True).select_related("category")

        # Si no hay suficientes preguntas relacionadas explícitas, añadir otras preguntas
        max_related_faqs = 5
        current_related_count = related_faqs_qs.count()
        final_related_faqs = list(related_faqs_qs)

        if current_related_count < max_related_faqs:
            # Excluir la pregunta actual y las ya relacionadas
            excluded_ids = [self.object.id] + [faq.id for faq in final_related_faqs]

            # Obtener preguntas adicionales ordenadas por su orden
            # Assuming additional_faq.category.name might be accessed
            additional_faqs = (
                FAQ.objects.filter(is_active=True)
                .exclude(id__in=excluded_ids)
                .select_related("category")
                .order_by("order")[: max_related_faqs - current_related_count]
            )

            # Combinar resultados
            final_related_faqs.extend(list(additional_faqs))

        context["related_faqs"] = final_related_faqs
        return context

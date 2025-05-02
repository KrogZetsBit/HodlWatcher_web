# admin.py
from django.contrib import admin
from modeltranslation.admin import TranslationAdmin

from .models import FAQ
from .models import FAQCategory


class RelatedFAQsInline(admin.TabularInline):
    model = FAQ.related_questions.through
    fk_name = "from_faq"
    verbose_name = "Pregunta relacionada"
    verbose_name_plural = "Preguntas relacionadas"
    extra = 1


@admin.register(FAQ)
class FAQAdmin(TranslationAdmin):
    list_display = (
        "question",
        "category",
        "order",
        "is_active",
        "created_at",
        "updated_at",
    )
    list_filter = ("is_active", "category")
    search_fields = ("question", "answer")
    prepopulated_fields = {"slug": ("question",)}
    list_editable = ("order", "is_active", "category")
    exclude = ("related_questions",)
    inlines = [RelatedFAQsInline]
    fieldsets = (
        (None, {"fields": ("question", "answer", "slug", "category")}),
        ("Opciones", {"fields": ("order", "is_active")}),
    )

    class Media:
        js = (
            "https://ajax.googleapis.com/ajax/libs/jquery/1.9.1/jquery.min.js",
            "https://ajax.googleapis.com/ajax/libs/jqueryui/1.10.2/jquery-ui.min.js",
            "modeltranslation/js/tabbed_translation_fields.js",
        )
        css = {
            "screen": ("modeltranslation/css/tabbed_translation_fields.css",),
        }


@admin.register(FAQCategory)
class FAQCategoryAdmin(TranslationAdmin):
    list_display = ("name", "order", "is_active")
    list_editable = ("order", "is_active")
    prepopulated_fields = {"slug": ("name",)}

    class Media:
        js = (
            "https://ajax.googleapis.com/ajax/libs/jquery/1.9.1/jquery.min.js",
            "https://ajax.googleapis.com/ajax/libs/jqueryui/1.10.2/jquery-ui.min.js",
            "modeltranslation/js/tabbed_translation_fields.js",
        )
        css = {
            "screen": ("modeltranslation/css/tabbed_translation_fields.css",),
        }

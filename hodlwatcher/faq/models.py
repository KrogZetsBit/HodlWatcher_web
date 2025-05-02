# models.py
from ckeditor.fields import RichTextField
from django.db import models
from django.urls import reverse
from django.utils.text import slugify
from django.utils.translation import gettext_lazy as _


class FAQCategory(models.Model):
    name = models.CharField(max_length=100, verbose_name=_("Nombre"))
    slug = models.SlugField(max_length=100, unique=True, blank=True)
    order = models.PositiveIntegerField(default=0, verbose_name=_("Orden"))
    is_active = models.BooleanField(default=True, verbose_name=_("Activo"))

    class Meta:
        ordering = ["order"]
        verbose_name = _("Categoría de FAQ")
        verbose_name_plural = _("Categorías de FAQ")

    def __str__(self):
        return self.name

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.name)
        super().save(*args, **kwargs)

    def get_absolute_url(self):
        return reverse("faq_category_detail", kwargs={"slug": self.slug})


class FAQ(models.Model):
    question = models.CharField(max_length=255, verbose_name=_("Pregunta"))
    answer = RichTextField(verbose_name=_("Respuesta"))
    category = models.ForeignKey(
        FAQCategory,
        on_delete=models.CASCADE,
        related_name="faqs",
        verbose_name=_("Categoría"),
        null=True,
        blank=True,
    )
    order = models.PositiveIntegerField(default=0, verbose_name=_("Orden"))
    slug = models.SlugField(max_length=255, unique=True, blank=True)
    is_active = models.BooleanField(default=True, verbose_name=_("Activo"))
    related_questions = models.ManyToManyField(
        "self",
        blank=True,
        symmetrical=False,
        verbose_name=_("Preguntas relacionadas"),
        related_name="related_to",
    )
    created_at = models.DateTimeField(auto_now_add=True, verbose_name=_("Fecha de creación"))
    updated_at = models.DateTimeField(auto_now=True, verbose_name=_("Fecha de actualización"))

    class Meta:
        ordering = ["order"]
        verbose_name = _("Pregunta Frecuente")
        verbose_name_plural = _("Preguntas Frecuentes")

    def __str__(self):
        return self.question

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.question)
        super().save(*args, **kwargs)

    def get_absolute_url(self):
        return reverse("faq_detail", kwargs={"slug": self.slug})

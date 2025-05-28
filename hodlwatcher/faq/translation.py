# translation.py
from modeltranslation.translator import TranslationOptions, translator

from .models import FAQ, FAQCategory


class FAQTranslationOptions(TranslationOptions):
    fields = ("question", "answer")


class FAQCategoryTranslationOptions(TranslationOptions):
    fields = ("name",)


translator.register(FAQ, FAQTranslationOptions)
translator.register(FAQCategory, FAQCategoryTranslationOptions)

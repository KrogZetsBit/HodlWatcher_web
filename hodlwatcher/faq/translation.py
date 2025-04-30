# translation.py
from modeltranslation.translator import TranslationOptions
from modeltranslation.translator import translator

from .models import FAQ
from .models import FAQCategory


class FAQTranslationOptions(TranslationOptions):
    fields = ("question", "answer")


class FAQCategoryTranslationOptions(TranslationOptions):
    fields = ("name",)


translator.register(FAQ, FAQTranslationOptions)
translator.register(FAQCategory, FAQCategoryTranslationOptions)

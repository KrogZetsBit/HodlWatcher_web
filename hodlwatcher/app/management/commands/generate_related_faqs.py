from django.core.management.base import BaseCommand

from hodlwatcher.faq.models import FAQ
from hodlwatcher.faq.utils import generate_related_questions


class Command(BaseCommand):
    help = "Automatically generates related questions for all FAQs"

    def add_arguments(self, parser):
        parser.add_argument(
            "--num",
            type=int,
            default=3,
            help="Number of related questions to generate per FAQ",
        )

    def handle(self, *args, **options):
        num_related = options["num"]
        faqs = FAQ.objects.filter(is_active=True)

        self.stdout.write("Generating related questions...")

        for faq in faqs:
            # Limpiar relaciones existentes
            faq.related_questions.clear()

            # Generar nuevas relaciones
            related_faqs = generate_related_questions(faq.id, num_related)

            # Añadir relaciones
            for related in related_faqs:
                faq.related_questions.add(related)

            self.stdout.write(f'  - "{faq.question}" → {len(related_faqs)} related questions')

        self.stdout.write(self.style.SUCCESS("¡Successfully generated related questions!"))

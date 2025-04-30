from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

from .models import FAQ


def generate_related_questions(faq_id, num_related=5):
    """
    Generates related questions based on text similarity
    Requires: pip install scikit-learn
    """

    # Obtener la pregunta actual
    current_faq = FAQ.objects.get(id=faq_id)

    # Obtener todas las demás preguntas activas
    other_faqs = FAQ.objects.filter(is_active=True).exclude(id=faq_id)

    if not other_faqs.exists():
        return []

    # Crear un corpus de texto para el análisis
    corpus = [current_faq.question + " " + current_faq.answer]
    corpus.extend([faq.question + " " + faq.answer for faq in other_faqs])

    # Vectorizar el texto usando TF-IDF
    vectorizer = TfidfVectorizer(stop_words="english")
    tfidf_matrix = vectorizer.fit_transform(corpus)

    # Calcular similitud de coseno entre la pregunta actual y las demás
    cosine_similarities = cosine_similarity(tfidf_matrix[0:1], tfidf_matrix[1:]).flatten()

    # Obtener los índices de las preguntas más similares
    related_indices = cosine_similarities.argsort()[: -num_related - 1 : -1]

    # Obtener una lista de IDs
    other_faqs_ids = list(other_faqs.values_list("id", flat=True))
    # Obtener los IDs relacionados
    related_ids = [other_faqs_ids[int(i)] for i in related_indices]

    return FAQ.objects.filter(id__in=related_ids)

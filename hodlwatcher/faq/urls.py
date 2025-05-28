from django.urls import path

from .views import FAQCategoryDetailView, FAQDetailView, FAQListView

urlpatterns = [
    path("", FAQListView.as_view(), name="faq_list"),
    path("<slug:slug>/", FAQDetailView.as_view(), name="faq_detail"),
    path(
        "category/<slug:slug>/",
        FAQCategoryDetailView.as_view(),
        name="faq_category_detail",
    ),
]

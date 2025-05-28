from django.conf import settings
from django.conf.urls.i18n import i18n_patterns
from django.conf.urls.static import static
from django.contrib import admin
from django.contrib.sitemaps.views import sitemap
from django.urls import include, path
from django.utils.translation import gettext_lazy as _
from django.views import defaults as default_views
from django.views.i18n import JavaScriptCatalog

from .sitemaps import StaticViewSitemap, UserViewSitemap, WatchdogViewSitemap

admin.site.site_header = _("HodlWatcher Administration")
admin.site.site_title = _("HodlWatcher Admin")


sitemaps = {
    "static": StaticViewSitemap,
    "user": UserViewSitemap,
    "watchdog": WatchdogViewSitemap,
}

urlpatterns = [
    path("jsi18/", JavaScriptCatalog.as_view(), name="jsi18n"),
    path("yubin/", include("django_yubin.urls")),
    path("robots.txt", include("robots.urls")),
    path(
        "sitemap.xml",
        sitemap,
        {"sitemaps": sitemaps},
        name="django.contrib.sitemaps.views.sitemap",
    ),
    path("ckeditor/", include("ckeditor_uploader.urls")),
    *static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT),
]

urlpatterns += i18n_patterns(
    path("i18n/", include("django.conf.urls.i18n")),
    path(settings.ADMIN_URL, admin.site.urls),
    path("", include("hodlwatcher.app.urls")),
    path("faq/", include("hodlwatcher.faq.urls")),
    path("accounts/", include("allauth.urls")),
)

if settings.DEBUG:
    # This allows the error pages to be debugged during development, just visit
    # these url in browser to see how these error pages look like.
    urlpatterns += [
        path(
            "400/",
            default_views.bad_request,
            kwargs={"exception": Exception("Bad Request!")},
        ),
        path(
            "403/",
            default_views.permission_denied,
            kwargs={"exception": Exception("Permission Denied")},
        ),
        path(
            "404/",
            default_views.page_not_found,
            kwargs={"exception": Exception("Page not Found")},
        ),
        path("500/", default_views.server_error),
    ]
    if "debug_toolbar" in settings.INSTALLED_APPS:
        import debug_toolbar

        urlpatterns = [
            path("__debug__/", include(debug_toolbar.urls)),
            *urlpatterns,
        ]

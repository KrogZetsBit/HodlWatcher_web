from django.contrib.sitemaps import Sitemap
from django.urls import reverse


class StaticViewSitemap(Sitemap):
    priority = 0.9
    changefreq = "daily"

    def items(self):
        return ["home", "finder", "contact", "account_login", "account_signup"]

    def location(self, item):
        return reverse(item)


class UserViewSitemap(Sitemap):
    priority = 0.8
    changefreq = "weekly"

    def items(self):
        return ["profile", "watchdogs_list", "link_telegram"]

    def location(self, item):
        return reverse(item)


class WatchdogViewSitemap(Sitemap):
    priority = 0.7
    changefreq = "daily"

    def items(self):
        return ["create_watchdog"]

    def location(self, item):
        return reverse(item)

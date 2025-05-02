from django.urls import path

from .views import BuscadorView
from .views import ContactView
from .views import DeleteWatchdogView
from .views import IndexView
from .views import LinkTelegramView
from .views import ProfileUpdateView
from .views import UnlinkTelegramView
from .views import WatchdogActivateView
from .views import WatchdogCreateView
from .views import WatchdogDeactivateView
from .views import WatchdogListView
from .views import delete_account

urlpatterns = [
    path("", IndexView.as_view(), name="home"),
    path("contact/", ContactView.as_view(), name="contact"),
    path("profile/", ProfileUpdateView.as_view(), name="profile"),
    path("delete-account/", delete_account, name="delete_account"),
    path("finder/", BuscadorView.as_view(), name="finder"),
    path("watchdogs/list/", WatchdogListView.as_view(), name="watchdogs_list"),
    path("watchdog/new/", WatchdogCreateView.as_view(), name="create_watchdog"),
    path(
        "watchdog/<uuid:pk>/deactivate/",
        WatchdogDeactivateView.as_view(),
        name="deactivate_watchdog",
    ),
    path(
        "watchdog/<uuid:pk>/activate/",
        WatchdogActivateView.as_view(),
        name="activate_watchdog",
    ),
    path(
        "watchdog/<uuid:pk>/delete/",
        DeleteWatchdogView.as_view(),
        name="delete_watchdog",
    ),
    path("link-telegram/", LinkTelegramView.as_view(), name="link_telegram"),
    path("unlink-telegram/", UnlinkTelegramView.as_view(), name="unlink_telegram"),
]

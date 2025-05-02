from django.core.management import call_command
from django.core.management.base import BaseCommand
from django.core.management.base import CommandError
from django.db import DEFAULT_DB_ALIAS
from django.db import connections
from django.db.migrations.loader import MigrationLoader


class Command(BaseCommand):
    """
    Check if there are pending migrations.
    If there are pending migrations it's possible apply them
    by executing this command with the param --execute
    """

    help = "Verify if there are migrations left and if so, execute them"

    def add_arguments(self, parser):
        parser.add_argument(
            "--database",
            action="store",
            dest="database",
            default=DEFAULT_DB_ALIAS,
            help='Nominates a database to synchronize. Defaults to the "default" database.',
        )
        parser.add_argument(
            "--execute",
            action="store_true",
            dest="execute",
            default=False,
            help="Execute the migrations if pending, application by application",
        )

    def handle(self, *args, **options):
        self.stdout.write(" Verifying if the are migrations left ".center(100, "="))

        # Get the database we're operating from
        db = options.get("database")
        execute_if_pending = options.get("execute")
        connection = connections[db]

        # process the apps in order to see if there are pending applications
        pending_apps = self.verify_pending(connection)

        if not pending_apps:
            self.stdout.write(" End of the process: not apps pending ".center(100, "="))
            return

        if not execute_if_pending:
            # only warning that there are applications with pending migrations
            commando_error = f"There are this apps: {pending_apps} with pending migrations"
            raise CommandError(commando_error)

        # at this point apps with pending migrations exists and proceed to execute them
        self.stdout.write(f"Migrating the apps: {pending_apps}".center(100, "."))
        for app_name in pending_apps:
            call_command("migrate", app_name)

        self.stdout.write(" End of the process: applied migrations ".center(100, "="))

    @staticmethod
    def verify_pending(connection):
        """
        Obtain the list of apps with pending migrations

        :param connection:
        :return:
        """
        # Load migrations from disk/DB
        loader = MigrationLoader(connection, ignore_no_migrations=True)
        graph = loader.graph

        applications_with_pending_migrations = set()

        # For each app, retrieve the pending migrations
        for app_name in sorted(loader.migrated_apps):
            shown = set()
            for node in graph.leaf_nodes(app_name):
                for plan_node in graph.forwards_plan(node):
                    if plan_node not in shown and plan_node[0] == app_name:
                        if plan_node in loader.applied_migrations:
                            continue

                        applications_with_pending_migrations.add(app_name)
                        shown.add(plan_node)

        return applications_with_pending_migrations

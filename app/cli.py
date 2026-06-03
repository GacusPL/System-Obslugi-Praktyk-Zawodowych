import click
from flask.cli import with_appcontext
from app.seed import seed_db

@click.command("seed")
@with_appcontext
def seed_command():
    """Seeds the database with learning outcomes and default admin user."""
    seed_db()
    click.echo("Seeding completed successfully.")

def register_cli_commands(app):
    app.cli.add_command(seed_command)

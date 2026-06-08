import click
from flask.cli import with_appcontext
from app.seed import seed_db
from app.seed_demo import seed_demo_db

@click.command("seed")
@with_appcontext
def seed_command():
    """Seeds the database with learning outcomes and default admin user."""
    seed_db()
    click.echo("Seeding completed successfully.")

@click.command("seed-demo")
@with_appcontext
def seed_demo_command():
    """Seeds the database with demo learning outcomes, users, practices, journals, reports, etc."""
    seed_demo_db()
    click.echo("Demo seeding completed successfully.")

def register_cli_commands(app):
    app.cli.add_command(seed_command)
    app.cli.add_command(seed_demo_command)


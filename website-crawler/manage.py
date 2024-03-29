import os
import unittest

from dotenv import load_dotenv
from app.main.constant import paths
# from flask_migrate import Migrate, MigrateCommand
from flask_script import Manager

from app.main import create_app, db
from app import blueprint

load_dotenv()
app = create_app(os.getenv('CURRENT_ENV') or 'dev')
app.register_blueprint(blueprint)
app.app_context().push()

manager = Manager(app)


# migrate = Migrate(app, db)
# manager.add_command('db', MigrateCommand)


@manager.command
def run():
    if paths.mode == "Local":
        app.run(port=5000)


@manager.command
def test():
    """Runs the unit tests."""
    tests = unittest.TestLoader().discover('app/test', pattern='test*.py')
    result = unittest.TextTestRunner(verbosity=2).run(tests)
    if result.wasSuccessful():
        return 0
    return 1


if __name__ == '__main__':
    manager.run()

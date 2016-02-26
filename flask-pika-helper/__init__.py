import flask
from functools import wraps
from functools import partial

def publish_event(f):
    @wraps(f)
    def wrapper(*args, **kwargs):
        event_logger = getattr(flask.current_app, 'extensions', {})\
            .get('flask_event_logger')
        stack_top = event_logger._get_stack_top()
        stack_top.event_logger_callbacks = getattr(stack_top, 'event_logger_callbacks', [])
        return f(*args, **kwargs)
    return wrapper


class FlaskEventLogger(object):

    def __init__(self, app=None, db=None):
        self.app = app
        if app is not None:
            self.init_app(app, db)
        app.after_request = self._publish_events

    def init_app(self, app, db):
        if not hasattr(app, 'extensions'):
            app.extensions = {}
        app.extensions['flask_event_logger'] = self
        self.init_db_signal_handler(app, db)
        self.set_amq_connection_params(app)
        app.after_request(_publish_message)

    def init_db_signal_handlers(app, db):
        if app.get('SQLALCHEMY_TRACK_MODIFICATIONS', False):
            models_committed.connect(self._committed_signal_handler)

    def _committed_signal_handler(self, changes=None):
        callbacks_array = getattr(stack_top, 'event_logger_callbacks', None)
        if callbacks_array is None:
            return
        publish_method = functools.partial(self._publish_event, changes)
        callbacks_array.append(publish_method)

    def _publish_events(self):
        callbacks_array = getattr(stack_top, 'event_logger_callbacks', [])
        for call in callbacks_array:
            call()

    def _publish_event(self, changes=None):

    def _get_stack_top(self):
        if flask._app_ctx_stack.top is not None:
            return flask._app_ctx_stack.top
        raise RuntimeError('No application context present')

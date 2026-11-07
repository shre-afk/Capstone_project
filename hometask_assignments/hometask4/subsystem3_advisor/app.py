"""Flask pages and JSON endpoints for the energy advisor prototype."""

from flask import Flask, jsonify, render_template

from .advisor import build_advice
from .errors import AdvisorErrorHandler, SummaryNotFoundError


def create_app(repository):
    app = Flask(__name__)
    AdvisorErrorHandler(app)

    @app.get('/')
    def index():
        return render_template('index.html', summaries=repository.list_summaries())

    @app.get('/api/summaries')
    def summaries():
        return jsonify(repository.list_summaries())

    @app.get('/api/advice/<int:building_id>')
    def advice(building_id):
        summary = repository.get_summary(building_id)
        if summary is None:
            raise SummaryNotFoundError(f'No energy summary for building {building_id}.')
        return jsonify(build_advice(summary))

    return app

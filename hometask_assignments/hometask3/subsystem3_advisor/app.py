"""Flask pages and JSON endpoints for the energy advisor prototype."""

from flask import Flask, abort, jsonify, render_template


def create_app(repository):
    app = Flask(__name__)

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
            abort(404)
        if summary['after_hours_kwh'] > 0:
            message = 'Review equipment schedules and check whether after-hours operation is necessary.'
        else:
            message = 'Compare consumption with previous periods before deciding on changes.'
        return jsonify({**summary, 'advice': message})

    return app

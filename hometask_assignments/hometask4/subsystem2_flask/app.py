"""The Flask web app - now with proper error handling"""
 
from flask import Flask, jsonify, render_template, request
 
from config import CO2_KG_PER_KWH, EUR_PER_KWH
from errors import DataErrorHandler, NotFoundError
from validators import check_plausible, parse_period, parse_reading
 
WHOLE_YEAR = ("2016-01-01 00:00:00", "2017-01-01 00:00:00")
 
 
def create_app(repository):
    app = Flask(__name__)
    DataErrorHandler(app)
 
    def building_or_404(building_id):
        building = repository.get_building(building_id)
        if building is None:
            raise NotFoundError(f"no building with id {building_id}", {"building_id": building_id})
        return building
 
    def period_from_url():
        return parse_period(request.args.get("start", WHOLE_YEAR[0]),
                            request.args.get("end", WHOLE_YEAR[1]))
 
    @app.route("/")
    def home():
        return render_template("index.html", buildings=repository.list_buildings())
 
    @app.route("/api/buildings")
    def list_buildings():
        return jsonify(repository.list_buildings())
 
    @app.route("/api/buildings/<int:building_id>")
    def get_building(building_id):
        return jsonify(building_or_404(building_id))
 
    @app.route("/api/buildings/<int:building_id>/readings")
    def get_readings(building_id):
        building_or_404(building_id)
        start, end = period_from_url()
        rows = repository.get_readings(building_id, start, end)
        for row in rows:
            row["ts_utc"] = str(row["ts_utc"])
        return jsonify(rows)
 
    @app.route("/api/buildings/<int:building_id>/kpis")
    def get_kpis(building_id):
        building_or_404(building_id)
        start, end = period_from_url()
        rows = repository.get_readings(building_id, start, end)
        energy = round(sum(row["value"] for row in rows), 2)
        return jsonify({
            "building_id": building_id,
            "readings": len(rows),
            "energy_kwh": energy,
            "cost_eur": round(energy * EUR_PER_KWH, 2),
            "co2_kg": round(energy * CO2_KG_PER_KWH, 1),
        })
 
    @app.route("/api/readings", methods=["POST"])
    def add_reading():
        meter_id, ts_utc, value = parse_reading(request.get_json(silent=True))
        meter = repository.get_meter(meter_id)
        if meter is None:
            raise NotFoundError(f"no meter with id {meter_id}", {"meter_id": meter_id})
        check_plausible(value, meter["type"])
        repository.add_reading(meter_id, ts_utc, value)
        return jsonify({"stored": {"meter_id": meter_id, "ts_utc": ts_utc, "value": value}}), 201
 
    return app
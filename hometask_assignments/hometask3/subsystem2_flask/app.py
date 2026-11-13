"""The Flask web app - Its JSON uses the same names as the capstone's api.get_kpis()"""
 
from flask import Flask, abort, jsonify, render_template, request
 
from config import CO2_KG_PER_KWH, EUR_PER_KWH
 
WHOLE_YEAR = ("2016-01-01 00:00:00", "2017-01-01 00:00:00")   # default period if none is given
 
 
def create_app(repository):
    app = Flask(__name__)
 
    @app.route("/")
    def home():
        return render_template("index.html", buildings=repository.list_buildings())
 
    @app.route("/api/buildings")
    def list_buildings():
        return jsonify(repository.list_buildings())
 
    @app.route("/api/buildings/<int:building_id>")
    def get_building(building_id):
        building = repository.get_building(building_id)
        if building is None:
            abort(404)
        return jsonify(building)
 
    @app.route("/api/buildings/<int:building_id>/readings")
    def get_readings(building_id):
        start = request.args.get("start", WHOLE_YEAR[0])
        end = request.args.get("end", WHOLE_YEAR[1])
        rows = repository.get_readings(building_id, start, end)
        for row in rows:
            row["ts_utc"] = str(row["ts_utc"])      # MySQL gives datetime objects, JSON wants text
        return jsonify(rows)
 
    @app.route("/api/buildings/<int:building_id>/kpis")
    def get_kpis(building_id):
        start = request.args.get("start", WHOLE_YEAR[0])
        end = request.args.get("end", WHOLE_YEAR[1])
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
        data = request.get_json()
        repository.add_reading(data["meter_id"], data["ts_utc"], float(data["value"]))
        return jsonify({"stored": data}), 201
 
    return app
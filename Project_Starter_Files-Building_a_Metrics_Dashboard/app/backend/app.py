import logging
import pymongo
from flask_pymongo import PyMongo
from flask import Flask, render_template, request, jsonify

from flask_opentracing import FlaskTracing
from prometheus_flask_exporter.multiprocess import GunicornInternalPrometheusMetrics
from jaeger_client import Config
from jaeger_client.metrics.prometheus import PrometheusMetricsFactory



app = Flask(__name__)
metrics = GunicornInternalPrometheusMetrics(app)

logging.getLogger("").handlers = []
logging.basicConfig(format="%(message)s", level=logging.DEBUG)
logger = logging.getLogger(__name__)

app.config["MONGO_DBNAME"] = "example-mongodb"
app.config[
    "MONGO_URI"
] = "mongodb://example-mongodb-svc.default.svc.cluster.local:27017/example-mongodb"

mongo = PyMongo(app)


def init_tracer(service):

    config = Config(
        config={
            "sampler": {"type": "const", "param": 1},
            "logging": True,
            "reporter_batch_size": 1,
        },
        service_name=service,
        validate=True,
        metrics_factory=PrometheusMetricsFactory(service_name_label=service),
    )

    return config.initialize_tracer()

tracer = init_tracer("backend")
flask_tracer = FlaskTracing(tracer, True, app)


@app.route("/")
def homepage():
    with tracer.start_span("backend-homepage"):
        return "Hello World"


@app.route("/api")
def my_api():
    with tracer.start_span("backend-api"):
        answer = "something"
        return jsonify(repsonse=answer)


@app.route("/star", methods=["POST"])
def add_star():
    with tracer.start_span("backend-star"):
        star = mongo.db.stars
        name = request.json["name"]
        distance = request.json["distance"]
        star_id = star.insert({"name": name, "distance": distance})
        new_star = star.find_one({"_id": star_id})
        output = {"name": new_star["name"], "distance": new_star["distance"]}
        return jsonify({"result": output})


if __name__ == "__main__":
    app.run()

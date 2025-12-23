from flask import Flask, jsonify

from nasa.routes import nasa_bp


def create_app() -> Flask:
    app = Flask(__name__)
    app.register_blueprint(nasa_bp)

    @app.get("/health")
    def health():
        return jsonify({"status": "ok"}), 200

    return app


if __name__ == "__main__":
    app = create_app()
    # Flask 3 uses debug via env; fine to pass debug=True locally too.
    app.run(host="0.0.0.0", port=5000, debug=True)

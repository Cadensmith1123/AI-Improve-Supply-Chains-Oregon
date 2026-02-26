# app.py
import sys
import os

# Add parent directory to path so we can import 'db' package
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from flask import Flask, render_template, request, redirect, url_for, abort, jsonify
import access_db as db
# import blueprint
from map_route import map_bp
from routes_bp import routes_bp
from products_bp import products_bp
from assets_bp import assets_bp

app = Flask(__name__)

# register the blueprint
app.register_blueprint(map_bp)
app.register_blueprint(routes_bp)
app.register_blueprint(products_bp)
app.register_blueprint(assets_bp)


@app.get("/health")
def health():
    return {"status": "ok"}


@app.get("/")
def home():
    return redirect(url_for("routes.routes_list"))


if __name__ == "__main__":
    app.run(debug=True)

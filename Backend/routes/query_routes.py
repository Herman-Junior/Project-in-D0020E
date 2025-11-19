from flask import Blueprint, jsonify
import pymysql

query_bp = Blueprint('query', __name__)
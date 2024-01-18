from flask import Flask, jsonify, request
from docker_wrapper import DockerError
import json
import argparse
from typing import Optional
from image_store import ImageStore

from machine_manager import MachineManager, Config

app = Flask(__name__)

machine_manager: Optional[MachineManager] = None

@app.route('/create', methods=['POST'])
def create():
    request_data = request.get_json()
    lang = request_data.get('lang')

    if not lang:
        return jsonify({"status": "error", "message": "Missing 'lang' parameter"}), 400

    try:
        linter = machine_manager.create_linter(lang)
    except ValueError as e:
        return jsonify({"status": "error", "message": str(e)}), 400
    except RuntimeError as e:
        return jsonify({"status": "error", "message": str(e)}), 500

    response = {
        'status': 'ok',
        'id': f'127.0.0.1:{linter.host_port}',
    }

    return jsonify(response), 200


@app.route('/delete', methods=['POST'])
def delete():
    request_data = request.get_json()
    ip_port = request_data.get('ip_port')

    if not ip_port:
        return jsonify({"status": "error", "message": "Missing 'ip_port' parameter"}), 400

    try:
        machine_manager.delete_linter(ip_port)
    except ValueError as e:
        return jsonify({"status": "error", "message": str(e)}), 400
    except RuntimeError as e:
        return jsonify({"status": "error", "message": str(e)}), 500


    return jsonify({"status": "ok"}), 200


@app.route('/init-update', methods=['POST'])
def init_update():
    request_data = request.get_json()
    lang = request_data.get('lang')

    if not lang:
        return jsonify({"status": "error", "message": "Missing 'lang' parameter"}), 400
    
    version = request_data.get('version')

    if not version:
        return jsonify({"status": "error", "message": "Missing 'version' parameter"}), 400
    
    try:
        machine_manager.init_update(lang, version)
    except ValueError as e:
        return jsonify({"status": "error", "message": str(e)}), 400
    except RuntimeError as e:
        return jsonify({"status": "error", "message": str(e)}), 500

    return '/init-update'


@app.route('/update', methods=['POST'])
def update():
    request_data = request.get_json()
    lang = request_data.get('lang')

    if not lang:
        return jsonify({"status": "error", "message": "Missing 'lang' parameter"}), 400

    try:
        machine_manager.update(lang)
    except ValueError as e:
        return jsonify({"status": "error", "message": str(e)}), 400
    except RuntimeError as e:
        return jsonify({"status": "error", "message": str(e)}), 500

    return jsonify({"status": "ok"}), 200


@app.route('/rollback', methods=['POST'])
def rollback():
    request_data = request.get_json()
    lang = request_data.get('lang')

    if not lang:
        return jsonify({"status": "error", "message": "Missing 'lang' parameter"}), 400

    try:
        machine_manager.rollback(lang)
    except ValueError as e:
        return jsonify({"status": "error", "message": str(e)}), 400
    except RuntimeError as e:
        return jsonify({"status": "error", "message": str(e)}), 500
    
    return jsonify({"status": "ok"}), 200


@app.route('/status')
def status():
    return jsonify(linters=machine_manager.status()), 200


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('config_path', type=str, help='Path to config file')
    parser.add_argument('linters_path', type=str, help='Path to file with linter definitions')
    args = parser.parse_args()

    if args.config_path:
        app.config.from_file(args.config_path, load=json.load)
    else:
        print('No config file provided, exiting')
        exit(1)

    if args.linters_path:
        image_store = ImageStore.from_json_file(args.linters_path)
    else:
        print('No linters file provided, exiting')
        exit(1)

    machine_manager = MachineManager(
        image_store=ImageStore.from_json_file(args.linters_path), 
        update_steps=app.config['UPDATE_STEPS'],
        config=Config(timeout=app.config['STOP_TIMEOUT']) # Yes, this is ugly, will fix later
        )
    app.run(host='0.0.0.0', port=5000)
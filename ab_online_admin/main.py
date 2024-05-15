import urllib
import re
import tempfile
import requests
import sys
from flask import Flask, render_template, request, redirect, url_for, Blueprint
from collections import defaultdict
from werkzeug.utils import secure_filename
from argparse import ArgumentParser
from ab_online import API

AB_VERSIONS = {}
PLUGINS = {}


ab_online_web = Blueprint('ab_online_web', __name__)


@ab_online_web.route("/", methods=["GET", "POST", "DELETE"])
def home():
    if request.method == "POST":
        data = request.form
        action = data.get("action")
        session = data.get("session")
        database = data.get("database")
        if action == "toggle_session":
            running = API.session.list(running=True)
            if session in running:
                API.session.stop(session)
            else:
                API.session.start(session)
        elif action == "delete_session":
            API.session.delete(session)
        elif action == "edit_session":
            return redirect(url_for("ab_online_web.edit_session", session=session))
        elif action == "new_session":
            return redirect(url_for("ab_online_web.edit_session", session="@"))
        elif action == "delete_database":
            API.db.remove(database)
        elif action == "new_database":
            db_file = request.files["new_database"]
            if db_file.filename == '':
                pass
            filename = secure_filename(db_file.filename)
            with tempfile.TemporaryDirectory() as tmpdirname:
                print(tmpdirname)
                filepath = os.path.join(tmpdirname, filename)
                db_file.save(filepath)
                API.db.add(file=filepath, name=filename)
    sessions_list = API.session.list()
    sessions_infos = [
        [session, API.session.export_json(session)] for session in sessions_list
    ]
    running = API.session.list(running=True)
    databases_list = API.db.list(extension=True)
    return render_template(
        "home.html",
        sessions_list=sessions_list,
        running=running,
        sessions_infos=sessions_infos,
        databases_list=databases_list,
    )


@ab_online_web.route("/edit/<session>", methods=["GET", "POST", "DELETE"])
def edit_session(session=None):
    if request.method == "POST":
        data = request.form.to_dict(flat=False)
        session_dict = format_session_post(data)
        return redirect(url_for("ab_online_web.home"))
    session_infos = "@"
    if session != "@":
        session_infos = API.session.export_json(session)
    global AB_VERSIONS
    global PLUGINS
    return render_template(
        "edit_session.html",
        ab_versions=AB_VERSIONS,
        plugins=PLUGINS,
        databases=API.db.list(extension=True),
        session_infos=session_infos,
        session=session
    )


def format_session_post(data: dict):
    session_dict = {}
    session_dict["name"] = data["name"][0]
    session_dict["password"] = data["password"][0]
    session_dict["machines"] = int(data["machines"][0])
    session_dict["ab_channel"] = data["ab_channel"][0]
    session_dict["ab_version"] = data["ab_version"][0]
    session_dict["databases"] = []
    session_dict["plugins"] = []
    session_dict["projects"] = []

    for key, value in data.items():
        nb = key.split("-")[-1]
        if "project-name" in key:
            if f"project-databases-{nb}" in data.keys():
                databases_list = data[f"project-databases-{nb}"]
            else:
                databases_list = []
            if f"project-plugins-{nb}" in data.keys():
                plugins_list = [p.split("ab-plugin-")[1]
                                for p in data[f"project-plugins-{nb}"]]
            else:
                plugins_list = []
            session_dict["projects"].append({
                "name": data[f"project-name-{nb}"][0],
                "databases": databases_list,
                "plugins": plugins_list
            })
        elif "database-name" in key:
            session_dict["databases"].append({
                "name": data[f"database-name-{nb}"][0],
                "filename": data[f"database-{nb}"][0],
                "location": "local"
            })
        elif "plugin-version" in key:
            session_dict["plugins"].append({
                "name": data[f"plugin-{nb}"][0].split("ab-plugin-")[1],
                "ab_channel": data[f"plugin-{nb}"][0].split("/")[1],
                "version": data[f"plugin-version-{nb}"][0]
            })
    session = API.session.import_dict(session_dict)
    API.session.export_json(session, file=session.file)


def update_ab_versions():
    """get all existing ab channels and versions
    """
    user_agent = 'Mozilla/5.0 (Windows; U; Windows NT 5.1; en-US; rv:1.9.0.7) Gecko/2009021910 Firefox/3.0.7'
    url = "http://anaconda.org/search?q=activity-browser"
    headers = {'User-Agent': user_agent, }
    request = urllib.request.Request(
        url, None, headers)  # The assembled request
    response = urllib.request.urlopen(request)
    data = response.read()  # The data u need
    html = data.decode("utf-8")
    channels_list = re.findall('<a href="/.*/activity-browser">', html)
    channels_list = [i.split("/")[1] for i in channels_list]
    # channels_list = ["conda-forge"]

    ab_versions = {}
    for channel in channels_list:
        response = requests.get(
            f"https://api.anaconda.org/package/{channel}/activity-browser")
        ab_versions[channel] = response.json()["versions"]
    global AB_VERSIONS
    AB_VERSIONS = ab_versions
    return ab_versions


def update_plugins():
    """get all existing plugins
    """
    user_agent = 'Mozilla/5.0 (Windows; U; Windows NT 5.1; en-US; rv:1.9.0.7) Gecko/2009021910 Firefox/3.0.7'
    url = "http://anaconda.org/search?q=ab-plugin"
    headers = {'User-Agent': user_agent, }
    request = urllib.request.Request(
        url, None, headers)  # The assembled request
    response = urllib.request.urlopen(request)
    data = response.read()  # The data u need
    html = data.decode("utf-8")
    plugins_list = re.findall('<a href="/.*/ab-plugin-.*">', html)
    plugins_list = [i.split("\"")[1] for i in plugins_list]

    plugins_versions = {}
    for plugin in plugins_list:
        response = requests.get(f"https://api.anaconda.org/package{plugin}")
        plugins_versions[plugin] = response.json()["versions"]
    global PLUGINS
    PLUGINS = plugins_versions
    return plugins_versions


def launch_server(args):
    # arg parser for the standard anaconda-project options
    parser = ArgumentParser(prog="ab-online-web",
                            description="A web interface for Activity Browser Online")
    parser.add_argument('--host', action='append', default=[],
                        help='Hostname to allow in requests')
    parser.add_argument('--port', action='store', default=8086, type=int,
                        help='Port to listen on')
    parser.add_argument('--prefix', action='store', default='',
                        help='Prefix in front of urls')

    args = parser.parse_args(args)

    print("Getting Activity Browser versions from Anaconda...")
    update_ab_versions()
    print("Getting plugins from Anaconda...")
    update_plugins()

    app = Flask(__name__)
    app.register_blueprint(
        ab_online_web, url_prefix=args.prefix)

    app.config['PREFERRED_URL_SCHEME'] = 'https'

    app.run(host=args.host,
            port=args.port)

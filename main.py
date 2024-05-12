import urllib
import re
import requests
from flask import Flask, render_template, request, redirect, url_for
from collections import defaultdict
from ab_online import API

app = Flask(__name__)


@app.route("/", methods=["GET", "POST", "DELETE"])
def home():
    sessions_list = API.session.list()
    running = API.session.list(running=True)
    sessions_infos = [
        [session, API.session.export_json(session)] for session in sessions_list
    ]
    if request.method == "POST":
        data = request.form
        action = data.get("action")
        session = data.get("session")
        if action == "toggle":
            if session in running:
                API.session.stop(session)
            else:
                API.session.start(session)
        elif action == "delete":
            running = API.session.list(running=True)
            return render_template(
                "home.html",
                sessions_list=sessions_list,
                running=running,
                sessions_infos=sessions_infos,
            )
        elif action == "edit":
            return redirect(url_for("edit_session", session=session))
        elif action == "new":
            return redirect(url_for("edit_session", session="@"))
    elif request.method == "GET":
        running = API.session.list(running=True)
        return render_template(
            "home.html",
            sessions_list=sessions_list,
            running=running,
            sessions_infos=sessions_infos,
        )


@app.route("/edit/<session>", methods=["GET", "POST", "DELETE"])
def edit_session(session=None):
    if request.method == "POST":
        data = request.form.to_dict(flat=False)
        print(data)
        session_dict = format_session_post(data)
        return redirect(url_for("home"))
    session_infos = "@"
    if session != "@":
        session_infos = API.session.export_json(session)
    return render_template(
        "edit_session.html",
        ab_versions=list_ab_versions(),
        plugins=list_plugins(),
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
        print(key)
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


def list_ab_versions():
    """get all existing ab channels and versions
    """
    user_agent = 'Mozilla/5.0 (Windows; U; Windows NT 5.1; en-US; rv:1.9.0.7) Gecko/2009021910 Firefox/3.0.7'
    url = "http://anaconda.org/search?q=activity-browser"
    headers = {'User-Agent': user_agent, }
    request = urllib.request.Request(
        url, None, headers)  # The assembled request
    # response = urllib.request.urlopen(request)
    # data = response.read() # The data u need
    # html = data.decode("utf-8")
    # channels_list = re.findall('<a href="/.*/activity-browser">',html)
    # channels_list = [i.split("/")[1] for i in channels_list]
    channels_list = ["conda-forge", "bsteubing", "haasad"]

    ab_versions = {}
    for channel in channels_list:
        response = requests.get(
            f"https://api.anaconda.org/package/{channel}/activity-browser")
        ab_versions[channel] = response.json()["versions"]
    return ab_versions


def list_plugins():
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
    return plugins_versions

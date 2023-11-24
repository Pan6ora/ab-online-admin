from flask import Flask, render_template, request
from ab_online import API

app = Flask(__name__)


@app.route("/", methods=["GET", "POST", "DELETE"])
def hello_world():
    sessions_list = API.session.list()
    running = API.session.list(running=True)
    sessions_infos = [
        [session, API.session.export_json(session)] for session in sessions_list
    ]
    if request.method == "POST":
        data = request.form
        action = request.form.get("action")
        if action == "toggle_session":
            session = request.form.get("session")
            if session in running:
                API.session.stop(session)
            else:
                API.session.start(session)
    running = API.session.list(running=True)
    return render_template(
        "main.html",
        sessions_list=sessions_list,
        running=running,
        sessions_infos=sessions_infos,
    )

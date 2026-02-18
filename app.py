from flask import Flask, render_template, request, redirect, url_for
from flask_login import LoginManager, login_user, login_required, logout_user, current_user
from config import Config
from models import db, Judge, Project, Score
from normalization import normalize_scores
import numpy as np

app = Flask(__name__)
app.config.from_object(Config)

db.init_app(app)

login_manager = LoginManager()
login_manager.init_app(app)

@login_manager.user_loader
def load_user(user_id):
    return Judge.query.get(int(user_id))

@app.route("/")
def home():
    return redirect(url_for("login"))

@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        user = Judge.query.filter_by(username=request.form["username"]).first()
        if user and user.password == request.form["password"]:
            login_user(user)
            if user.role == "admin":
                return redirect(url_for("admin_dashboard"))
            return redirect(url_for("judge_dashboard"))
    return render_template("login.html")

@app.route("/judge")
@login_required
def judge_dashboard():
    projects = Project.query.all()
    return render_template("judge_dashboard.html", projects=projects)

@app.route("/score/<int:project_id>", methods=["GET", "POST"])
@login_required
def score(project_id):
    if request.method == "POST":
        total = sum([
            float(request.form["problem"]),
            float(request.form["design"]),
            float(request.form["validation"]),
            float(request.form["management"]),
            float(request.form["presentation"])
        ])

        new_score = Score(
            judge_id=current_user.id,
            project_id=project_id,
            raw_total=total
        )
        db.session.add(new_score)
        db.session.commit()
        return redirect(url_for("judge_dashboard"))

    project = Project.query.get(project_id)
    return render_template("score.html", project=project)

@app.route("/admin")
@login_required
def admin_dashboard():
    scores = Score.query.all()
    judges = Judge.query.filter_by(role="judge").all()

    for judge in judges:
        judge_scores = [s.raw_total for s in scores if s.judge_id == judge.id]
        if judge_scores:
            normalized = normalize_scores(judge_scores)
            judge_entries = [s for s in scores if s.judge_id == judge.id]
            for i, s in enumerate(judge_entries):
                s.normalized_total = normalized[i]

    db.session.commit()

    projects = Project.query.all()
    department_scores = {}

    for project in projects:
        proj_scores = [s.normalized_total for s in Score.query.filter_by(project_id=project.id)]
        if proj_scores:
            avg = np.mean(proj_scores)
            department_scores.setdefault(project.department, []).append(avg)

    ranking = {}
    for dept, scores in department_scores.items():
        top5 = sorted(scores, reverse=True)[:5]
        ranking[dept] = np.mean(top5)

    ranking = sorted(ranking.items(), key=lambda x: x[1], reverse=True)

    return render_template("admin_dashboard.html", ranking=ranking)

@app.route("/logout")
@login_required
def logout():
    logout_user()
    return redirect(url_for("login"))

if __name__ == "__main__":
    app.run()

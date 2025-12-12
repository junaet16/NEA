from flask import Flask, render_template, request, session, redirect, url_for, jsonify
import login

app = Flask(__name__)
app.secret_key = "idk"


def setUpConfig(app, databaseFile):
    app.config["DATABASE_FILE"] = databaseFile


@app.route('/', methods=['GET', 'POST']) #Need to finish account creation
def loginPage():
    databaseFile = app.config["DATABASE_FILE"]
    message = None
    if request.method == 'POST':
        action = request.form.get('actionName')
        username = request.form.get('username')
        password = request.form.get('password')

        if action == 'login':
            loginMessage = login.login(databaseFile, username, password)
            if loginMessage == "Login Successful":
                session["username"] = username
                return redirect(url_for("mainPage"))
            else:
                message = loginMessage
        elif action == 'signUp':
            message = ("Sign Up", username, password) #Finish this

    return render_template("login.html", message=message)


@app.route('/main', methods=['GET', 'POST'])
def mainPage():
    username = session["username"]

    return render_template("mainPage.html")


@app.route("/get_stations")
def get_stations():
    searchTerm = request.args.get("search", "")


if __name__ == '__main__':
    databaseFile = "final.db"
    setUpConfig(app, databaseFile)
    app.run()
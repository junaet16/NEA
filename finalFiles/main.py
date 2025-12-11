from flask import Flask, render_template, request
import login

app = Flask(__name__)


@app.route('/', methods=['GET', 'POST'])
def login():
    message = None
    if request.method == 'POST':
        action = request.form.get('actionName')
        username = request.form.get('username')
        password = request.form.get('password')

        if action == 'login':
            message = ("Login", username, password)
        elif action == 'signUp':
            message = ("Sign Up", username, password)

    return render_template("login.html", message=message)


if __name__ == '__main__':
    app.run()
from flask import Flask, render_template

app = Flask(__name__)

@app.route('/')
def index():
    return render_template("index.html")

@app.route('/assignments')
def assignments():
    return render_template("assignments.html")

@app.route('/flightroute')
def flightroute():
    return render_template("flightroute.html")

@app.route('/heisenberg')
def heisenberg():
    return render_template("heisenberg.html")

@app.route('/minecraft')
def minecraft():
    return render_template("minecraft.html")

@app.route('/visualizations')
def visualizations():
    return render_template("visualizations.html")


if __name__ == '__main__':
    app.run(debug=True)

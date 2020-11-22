from flask import Flask, render_template

app = Flask(__name__)

@app.route('/')
def index():
    return render_template('index.html', title='Sean Grate',
                           is_home=True,
                           nav_buttons=['About', 'Research', 'Projects'])

@app.route('/assignments')
def assignments():
    return render_template('assignments.html', title='TA Assignments',
                           is_home=False,
                           nav_buttons=['Background', 'Algorithm'])

@app.route('/flightroute')
def flightroute():
    return render_template('flightroute.html', title='Estimating Flight Routes',
                           is_home=False,
                           nav_buttons=['Background', 'Approaches'])

@app.route('/heisenberg')
def heisenberg():
    return render_template('heisenberg.html', title='Discrete Heisenberg Group',
                           is_home=False,
                           nav_buttons=['Background', 'Setup', 'Results'])

@app.route('/minecraft')
def minecraft():
    return render_template('minecraft.html', title='Generating Minecraft Worlds',
                           is_home=False,
                           nav_buttons=['Background', 'Approach'])

@app.route('/visualizations')
def visualizations():
    return render_template('visualizations.html', title='Visualizing Algebraic Surfaces',
                           is_home=False,
                           nav_buttons=['27 Lines', 'Twisted Cubic', 'Calculus III'])


@app.route('/test')
def test():
    return render_template('test.html')


if __name__ == '__main__':
    # app.run(debug=True)
    app.run(host='0.0.0.0', port='80')

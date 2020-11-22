from flask import Flask, render_template

application = Flask(__name__)

@application.route('/')
def index():
    return render_template('index.html', title='Sean Grate',
                           is_home=True,
                           nav_buttons=['About', 'Research', 'Projects'])

@application.route('/assignments')
def assignments():
    return render_template('assignments.html', title='TA Assignments',
                           is_home=False,
                           nav_buttons=['Background', 'Algorithm'])

@application.route('/flightroute')
def flightroute():
    return render_template('flightroute.html', title='Estimating Flight Routes',
                           is_home=False,
                           nav_buttons=['Background', 'Approaches'])

@application.route('/heisenberg')
def heisenberg():
    return render_template('heisenberg.html', title='Discrete Heisenberg Group',
                           is_home=False,
                           nav_buttons=['Background', 'Setup', 'Results'])

@application.route('/minecraft')
def minecraft():
    return render_template('minecraft.html', title='Generating Minecraft Worlds',
                           is_home=False,
                           nav_buttons=['Background', 'Approach'])

@application.route('/visualizations')
def visualizations():
    return render_template('visualizations.html', title='Visualizing Algebraic Surfaces',
                           is_home=False,
                           nav_buttons=['27 Lines', 'Twisted Cubic', 'Calculus III'])


@application.route('/test')
def test():
    return render_template('test.html')


if __name__ == '__main__':
    application.run(debug=True)

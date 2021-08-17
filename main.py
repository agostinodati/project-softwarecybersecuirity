import flask
import mysql.connector
import configparser

app = flask.Flask(__name__)

# Connect to the database
config = configparser.ConfigParser()
config.read('config.ini')

mydb = mysql.connector.connect(
  host=config['DB']['host'],
  user=config['DB']['user'],
  passwd=config['DB']['password'],
  database=config['DB']['database']
)

# Homepage
@app.route("/")
def main():
	return flask.render_template('index.html')



if __name__ == "__main__":
    app.config['ENV'] = 'development'
    app.config['DEBUG'] = True
    app.config['TESTING'] = True
    app.run()
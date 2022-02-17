from operator import ne
import os
import flask
from flask import request
import flask_praetorian
import flask_cors
from flask import got_request_exception
import sqlite3
from flask_restful import Resource, Api
from models import db, User
from cycles import AncienLots, Cycles, LotData, Peches, Semis, Stats, Lots, AncienCycle
from stocks import Stocks, VenteAliments, Clients, Entre
from user import UserList
from utils import changeDate, changeDateBack
from simple import Aliment, AlimentationTotal, Pompes, Bassins, ShowTable, AddInTable, Alimentation, EspecesRes, ChangementEau, Notifications
from ventes import EspecesVente, VenteCrevette, VentePoissons, VentePoissonsJour, VentesParJour
from analyseEau import AnalyseEau, AnalyseEauGraph, AnalyseOx
from emailUser import sendErrorMail

guard = flask_praetorian.Praetorian()
cors = flask_cors.CORS()


# Initialize flask app for the example
app = flask.Flask(__name__, static_folder='./build', static_url_path='/')
app.debug = True
app.config['SECRET_KEY'] = 'dsfnqsdjgqghksfjgfnjksfd'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['JWT_ACCESS_LIFESPAN'] = {'days': 7}
app.config['JWT_REFRESH_LIFESPAN'] = {'days': 31}

# Initialize the flask-praetorian instance for the app
with app.app_context():
    guard.init_app(app=app, user_class=User)

# Initialize a local database for the example
dbPath = "database.db"
app.config['SQLALCHEMY_DATABASE_URI'] = f"sqlite:///{os.path.join(os.getcwd(), dbPath)}"
db.init_app(app)
db.create_all(app=app)

# Initializes CORS so that the api_tool can talk to the example app
cors.init_app(app)

# Initializes Api
api = Api(app)


def log_exception(sender, exception, **extra):
    """ Log an exception to our logging framework """
    sendErrorMail(sender, exception)


got_request_exception.connect(log_exception, app)

# Add users for the example
with app.app_context():
    db.create_all()
    if db.session.query(User).filter_by(username='legacy').count() < 1:
        db.session.add(User(
            id=0,
            username='legacy',
            password=guard.hash_password('123456'),
            roles='legacy'
        ))
    if db.session.query(User).filter_by(username='Alex').count() < 1:
        db.session.add(User(
            username='Alex',
            password=guard.hash_password('123456'),
            roles='admin'
        ))
    if db.session.query(User).filter_by(username='Corinne').count() < 1:
        db.session.add(User(
            username='Corinne',
            password=guard.hash_password('123456'),
            roles='boss'
        ))
    db.session.commit()


class Login(Resource):
    def post(self):
        """
        Logs a user in by parsing a POST request containing user credentials and
        issuing a JWT token.
        .. example::
            $ curl http://localhost:5000/api/login -X POST \
                -d '{"username":"Yasoob","password":"strongpassword"}'
        """
        req = request.get_json(force=True)
        username = req.get('username', None)
        password = req.get('password', None)
        user = guard.authenticate(username, password)
        ret = {'access_token': guard.encode_jwt_token(user)}
        return ret, 200


class Refresh(Resource):
    def post(self):
        """
        Refreshes an existing JWT by creating a new one that is a copy of the old
        except that it has a refrehsed access expiration.
        .. example::
        $ curl http://localhost:5000/api/refresh -X GET \
            -H "Authorization: Bearer <your_token>"
        """
        old_token = guard.read_token_from_header()
        new_token = guard.refresh_jwt_token(old_token)
        ret = {'access_token': new_token}
        return ret, 200


class User(Resource):
    @flask_praetorian.auth_required
    def get(self):
        user_id = flask_praetorian.current_user_id()
        conn = sqlite3.connect(dbPath)
        c = conn.cursor()
        c.execute(
            f"SELECT email, username, roles, is_active FROM User WHERE id={user_id}")
        fetch = c.fetchone()
        conn.close()
        if fetch[3] != 1:
            return {"message": "user inactive"}, 400
        else:
            return {"email": fetch[0], "name": fetch[1], "role": fetch[2]}, 200

    @flask_praetorian.auth_required
    def put(self):
        user_id = flask_praetorian.current_user_id()
        conn = sqlite3.connect(dbPath)
        c = conn.cursor()
        c.execute(
            f"SELECT email, username, roles, is_active FROM User WHERE id={user_id}")
        fetch = c.fetchone()
        if fetch[3] != 1:
            conn.close()
            return {"message": "user inactive"}, 400
        else:
            data = request.json
            if "password" in data:
                password = guard.hash_password(data['password'])
                c.execute(
                    f"UPDATE USER SET password = '{password}' WHERE id = {user_id}")
                conn.commit()
                conn.close()
                return {"message", "user updated"}, 400
            email = data["email"]
            username = data["username"]
            c.execute(
                f"UPDATE USER SET email = '{email}', username = '{username}' WHERE id = {user_id}")
            conn.commit()
            conn.close()
            return {"message", "user updated"}, 400

    @flask_praetorian.auth_required
    def post(self):
        user_id = flask_praetorian.current_user_id()
        conn = sqlite3.connect(dbPath)
        c = conn.cursor()
        c.execute(
            f"SELECT email, username, roles, is_active FROM User WHERE id={user_id}")
        fetch = c.fetchone()
        if fetch[3] != 1:
            conn.close()
            return {"message": "user inactive"}, 400
        else:
            data = request.json
            email = data["email"]
            password = guard.hash_password(data['password'])
            username = data["name"]
            role = data["role"]
            c.execute(
                f"INSERT INTO USER (username, email, password, roles, is_active) VALUES ('{username}', '{email}', '{password}', '{role}',{1})")
            conn.commit()
            conn.close()
            return {"message", "user added"}, 400


api.add_resource(Login, '/api/login')
api.add_resource(Refresh, '/api/refresh')
api.add_resource(User, '/api/user')
api.add_resource(UserList, '/api/user/list')
api.add_resource(ShowTable, '/api/table/<table>')
api.add_resource(AddInTable, '/api/addInTable/<table>')
api.add_resource(Cycles, '/api/cycles', '/api/cycles/<bassin>')
api.add_resource(
    AncienCycle, '/api/ancienCycle/<bassin>/<dateDebut>/<dateFin>')
api.add_resource(Bassins, '/api/bassins')
api.add_resource(AnalyseEau, '/api/analyseEau/<date>', '/api/analyseEau')
api.add_resource(AnalyseOx, '/api/analyseOx')
api.add_resource(AnalyseEauGraph, '/api/analyseEauGraph/<bassin>/<date>')
api.add_resource(LotData, '/api/lotData/<lot_id>')
api.add_resource(Lots, '/api/lots')
api.add_resource(AncienLots, '/api/ancienLots/<cycle_id>')
api.add_resource(Alimentation, '/api/alimentation', '/api/alimentation/<date>')
api.add_resource(AlimentationTotal, '/api/alimentationTotal/<date>')
api.add_resource(Pompes, '/api/pompes')
api.add_resource(EspecesRes, '/api/especes')
api.add_resource(EspecesVente, '/api/especes/poissons')
api.add_resource(Semis, '/api/semis', '/api/semis/<lot_id>')
api.add_resource(Peches, '/api/peches', '/api/peches/<lot_id>')
api.add_resource(Stats, '/api/stats')
api.add_resource(VenteCrevette, '/api/ventes/crevettes')
api.add_resource(VenteAliments, '/api/ventes/aliments')
api.add_resource(Clients, '/api/clients', '/api/clients/<client>')
api.add_resource(Stocks, '/api/stocks/<filtre>/<dateDebut>', '/api/stocks')
api.add_resource(ChangementEau, '/api/changementEau')
api.add_resource(Entre, '/api/entre')
api.add_resource(Notifications, '/api/notifications')
api.add_resource(Aliment, '/api/aliments')
api.add_resource(VentesParJour, '/api/ventesParJour/<date>')
api.add_resource(VentePoissons, '/api/ventes/poissons/<espece>',
                 '/api/ventes/poissons')
api.add_resource(VentePoissonsJour, '/api/ventes/poissonsJour/<espece>/<date>')


@app.route('/')
def index():
    return app.send_static_file('index.html')


@app.errorhandler(404)
def not_found(e):
    return app.send_static_file('index.html')


# Run the example
if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)

# -*- coding: utf-8 -*-
import os
import config
import requests
import time
import datetime
import modules.data as data
import modules.scheduler as scheduler

from sqlite3 import Connection as SQLite3Connection
from flask import Flask, request, jsonify, abort, g, url_for
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import event
from sqlalchemy.engine import Engine
from sqlalchemy.orm import relationship, backref
from sqlalchemy.schema import PrimaryKeyConstraint, UniqueConstraint
from sqlalchemy.sql import func
from flask_httpauth import HTTPBasicAuth
from passlib.apps import custom_app_context as pwd_context
from itsdangerous import (TimedJSONWebSignatureSerializer
                          as Serializer, BadSignature, SignatureExpired)

# Declare app
app = Flask(__name__)
app.config["DEBUG"]                          = config.DEBUG
app.config['SECRET_KEY']                     = config.SECRET
app.config['SQLALCHEMY_DATABASE_URI']        = config.DATABASE_URI
app.config['SQLALCHEMY_COMMIT_ON_TEARDOWN']  = config.COMMIT_ON_TEARDOWN
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = config.TRACK_MODIFICATIONS

# Initialize Database and Models
db = SQLAlchemy(app)

# PRAGMAS
@event.listens_for(Engine, "connect")
def _set_sqlite_pragma(dbapi_connection, connection_record):
    if isinstance(dbapi_connection, SQLite3Connection):
        cursor = dbapi_connection.cursor()
        cursor.execute("PRAGMA foreign_keys=ON;")
        cursor.close()

class User(db.Model):
    __tablename__ = 'users'
    id = db.Column(db.Integer, primary_key = True)
    username = db.Column(db.String(32), index = True)
    password_hash = db.Column(db.String(128))

    def hash_password(self, password):
        self.password_hash = pwd_context.encrypt(password)

    def verify_password(self, password):
        return pwd_context.verify(password, self.password_hash)

    def generate_auth_token(self, expiration=600):
        s = Serializer(app.config['SECRET_KEY'], expires_in=expiration)
        return s.dumps({'id': self.id})

    @staticmethod
    def verify_auth_token(token):
        s = Serializer(app.config['SECRET_KEY'])
        try:
            data = s.loads(token)
        except SignatureExpired:
            return None    # valid token, but expired
        except BadSignature:
            return None    # invalid token
        user = User.query.get(data['id'])
        return user

class Phone(db.Model):
    __tablename__ = 'phone'
    __table_args__ = (
        PrimaryKeyConstraint("mac"),
        UniqueConstraint("ip"),
        UniqueConstraint("mac"),
        UniqueConstraint("id"),
        UniqueConstraint("number"),
    )
    ip         = db.Column(db.String())
    mac        = db.Column(db.String(),   primary_key=True)
    id         = db.Column(db.String(30))
    number     = db.Column(db.String(30))
    type       = db.Column(db.String(30)) # Kette oder Warteschleife
    model      = db.Column(db.String(30))
    department = db.Column(db.String(30))
    room       = db.Column(db.String(30))
    location   = db.Column(db.String(30))

    # Foreign Key Constraints
    #dialed   = db.relationship('Dialed',   backref='phone', cascade="all,delete", lazy = 'dynamic')
    #missed   = db.relationship('Missed',   backref='phone', onupdate="cascade", lazy = 'dynamic')
    #received = db.relationship('Received', backref='phone', onupdate="cascade", lazy = 'dynamic')

    def __repr__(self):
        return '<Phone %r, %r, %r>' % self.ip, self.mac, self.id

class Dialed(db.Model):
    __tablename__ = 'dialed'
    __table_args__ = (
        PrimaryKeyConstraint("datetime", "duration", "mac", "remotenr", sqlite_on_conflict='IGNORE'),
    )
    datetime   = db.Column(db.String(16))
    duration   = db.Column(db.String(10))
    ip         = db.Column(db.String())
    mac        = db.Column(db.String(), db.ForeignKey('phone.mac', onupdate="CASCADE"))
    type       = db.Column(db.String(30))
    localnr    = db.Column(db.String(30))
    localid    = db.Column(db.String(30))
    department = db.Column(db.String(30))
    room       = db.Column(db.String(30))
    location   = db.Column(db.String(30))
    remotenr   = db.Column(db.String(30))
    remoteid   = db.Column(db.String(30))

class Missed(db.Model):
    __tablename__ = 'missed'
    __table_args__ = (
        PrimaryKeyConstraint("datetime", "mac", "remotenr", sqlite_on_conflict='IGNORE'),
    )
    datetime   = db.Column(db.String(16))
    count      = db.Column(db.Integer)
    ip         = db.Column(db.String())
    mac        = db.Column(db.String(), db.ForeignKey('phone.mac', onupdate="CASCADE"))
    type       = db.Column(db.String(30))
    localnr    = db.Column(db.String(30))
    localid    = db.Column(db.String(30))
    department = db.Column(db.String(30))
    room       = db.Column(db.String(30))
    location   = db.Column(db.String(30))
    remotenr   = db.Column(db.String(30))
    remoteid   = db.Column(db.String(30))

class Received(db.Model):
    __tablename__ = 'received'
    __table_args__ = (
        PrimaryKeyConstraint("datetime", "duration", "mac", "remotenr", "remoteid", sqlite_on_conflict='IGNORE'),
    )
    datetime   = db.Column(db.String(16))
    duration   = db.Column(db.String(10))
    ip         = db.Column(db.String())
    mac        = db.Column(db.String(), db.ForeignKey('phone.mac', onupdate="CASCADE"))
    type       = db.Column(db.String(30))
    localnr    = db.Column(db.String(30))
    localid    = db.Column(db.String(30))
    department = db.Column(db.String(30))
    room       = db.Column(db.String(30))
    location   = db.Column(db.String(30))
    remotenr   = db.Column(db.String(30))
    remoteid   = db.Column(db.String(30))

# Initialize Auth
auth = HTTPBasicAuth()

@auth.verify_password
def verify_password(username_or_token, password):
    # first try to authenticate by token
    user = User.verify_auth_token(username_or_token)
    if not user:
        # try to authenticate with username/password
        user = User.query.filter_by(username=username_or_token).first()
        if not user or not user.verify_password(password):
            return False
    g.user = user
    return True

# Routes
# ------
# Alive
@app.route('/', methods=["GET"])
@auth.login_required
def lifesign():
    return 200

# Users
@app.route('/api/users', methods = ['POST'])
def add_user():
    username = request.json.get('username')
    password = request.json.get('password')
    if username is None or password is None:
        abort(400) # missing arguments
    if User.query.filter_by(username = username).first() is not None:
        abort(400) # existing user
    user = User(username = username)
    user.hash_password(password)
    db.session.add(user)
    db.session.commit()
    return jsonify({ 'username': user.username }), 201, {'Location': url_for('get_user', id = user.id, _external = True)}

@app.route('/api/users/<int:id>')
def get_user(id):
    user = User.query.get(id)
    if not user:
        abort(400)
    return jsonify({'username': user.username})

@app.route('/api/token')
@auth.login_required
def get_auth_token():
    token = g.user.generate_auth_token(600)
    return jsonify({'token': token.decode('ascii'), 'duration': 600})

# Phones
@app.route('/api/phone', methods=["POST"])
@auth.login_required
def add_phone():
    ip         = request.json.get('ip')
    mac        = request.json.get('mac')
    id         = request.json.get('id')
    number     = request.json.get('number')
    type       = request.json.get('type')
    model      = request.json.get('model')
    department = request.json.get('department')
    room       = request.json.get('room')
    location   = request.json.get('location')

    phone = Phone(ip=ip, id=id, mac=mac, number=number, type=type, model=model, department=department, room=room, location=location)
    db.session.add(phone)
    db.session.commit()

    return jsonify({'ip': phone.ip, 'mac': phone.mac, 'id': phone.id, 'number': phone.number, 'type':phone.type, 'model':phone.model, 'department':phone.department, 'room':phone.room, 'location':phone.location}), 201, {'Location': url_for('get_phone', phone = phone.ip, _external = True)}

@app.route('/api/phone/<phone>', methods=["GET"])
@auth.login_required
def get_phone(phone):
    phone = Phone.query.get(phone)
    if not phone:
        abort(400)
    return jsonify({'ip': phone.ip, 'mac': phone.mac, 'id': phone.id, 'number': phone.number, 'type':phone.type, 'model':phone.model, 'department':phone.department, 'room':phone.room, 'location':phone.location})

@app.route('/api/phone/<phone>', methods=["PATCH"])
@auth.login_required
def edit_phone(phone):
    phone = Phone.query.get(phone)

    phone.ip         = request.json.get('ip')           if 'ip' in request.json else phone.ip
    phone.mac        = request.json.get('mac')          if 'mac' in request.json else phone.mac
    phone.id         = request.json.get('id')           if 'id' in request.json else phone.id
    phone.number     = request.json.get('number')       if 'number' in request.json else phone.number
    phone.type       = request.json.get('type')         if 'type' in request.json else phone.type
    phone.model      = request.json.get('model')        if 'model' in request.json else phone.model
    phone.department = request.json.get('department')   if 'department' in request.json else phone.department
    phone.room       = request.json.get('room')         if 'room' in request.json else phone.location
    phone.location   = request.json.get('location')     if 'location' in request.json else phone.location

    db.session.commit()

    return jsonify({'ip': phone.ip, 'mac': phone.mac, 'id': phone.id, 'number': phone.number, 'type':phone.type, 'model':phone.model, 'department':phone.department, 'room':phone.room, 'location':phone.location}), 201, {'Location': url_for('get_phone', phone = phone.ip, _external = True)}

@app.route('/api/phone/<phone>', methods=["DELETE"])
@auth.login_required
def delete_phone(phone):
    phone = Phone.query.get(phone)
    db.session.delete(phone)
    db.session.commit()

    return jsonify({'ip': phone.ip, 'mac': phone.mac, 'id':phone.id, 'type':phone.type, 'model':phone.model, 'department':phone.department, 'room':phone.room, 'location':phone.location}), 201, {'Location': url_for('get_phone', phone = phone.ip, _external = True)}

@app.route('/api/phone/<phone>/calls', methods=["GET"])
@auth.login_required
def get_calls(phone):
    return data.parse_to_DB(phone, db, True)

# Update DB with newest calls from all phones
@app.route('/api/db/update', methods=["GET"])
def update():
    if request.remote_addr != '127.0.0.1':
        abort(403)

    phones = Phone.query.all()
    for phone in phones:
        try:
            calls = data.parse_html(phone.ip, False)
            if calls == None:
                print("No calls could be retrieved for", phone.ip)
            else:
                # Dialed
                for call in calls['list_dialed']:
                    dialed = Dialed(
                        datetime   = call[0],
                        duration   = call[1],
                        ip         = phone.ip,
                        mac        = phone.mac,
                        type       = phone.type,
                        localnr    = phone.number,
                        localid    = call[2],
                        department = phone.department,
                        room       = phone.room,
                        location   = phone.location,
                        remotenr   = call[3],
                        remoteid   = call[4],
                    )
                    db.session.add(dialed)
                    try:
                        db.session.commit()
                    except Exception:
                        db.session.rollback()

                # Missed
                for call in calls['list_missed']:
                    missed = Missed(
                        datetime   = call[0],
                        count      = call[1],
                        ip         = phone.ip,
                        mac        = phone.mac,
                        type       = phone.type,
                        localnr    = phone.number,
                        localid    = call[2],
                        department = phone.department,
                        room       = phone.room,
                        location   = phone.location,
                        remotenr   = call[3],
                        remoteid   = call[4],
                    )
                    db.session.add(missed)
                    try:
                        db.session.commit()
                    except Exception:
                        db.session.rollback()

                # Received
                for call in calls['list_received']:
                    received = Received(
                        datetime   = call[0],
                        duration   = call[1],
                        ip         = phone.ip,
                        mac        = phone.mac,
                        type       = phone.type,
                        localnr    = phone.number,
                        localid    = call[2],
                        department = phone.department,
                        room       = phone.room,
                        location   = phone.location,
                        remotenr   = call[3],
                        remoteid   = call[4],
                    )
                    db.session.add(received)
                    try:
                        db.session.commit()
                    except Exception:
                        db.session.rollback()

        except Exception as e:
            return "Update failed with the following error:\n\n" + str(e)
    return "Update successful!"

# Get Data
# Stats
@app.route('/api/stats/<frame>/<scope>', methods=["GET"])
def stats_monthly(frame, scope):
    if request.remote_addr != '127.0.0.1':
        abort(403)

    # Set path
    path = ""
    if frame == "monthly":
        path = "monthly_overview.sql"
    if frame == "daily":
        path = "daily_overview.sql"

    # Get data
    sql = data.read_sql(os.path.join("stats", path))
    sql = sql.replace('$NEXT'       , str(int(scope) + 1))
    sql = sql.replace('$CURRENT'    , str(int(scope)))
    sql = sql.replace('$PREVIOUS'   , str(int(scope) - 1))
    sql = sql.replace('$PENULTIMATE', str(int(scope) - 2))
    rows = db.engine.execute(sql)

    calls   = {
        'dialed'  : {'penultimate':0, 'previous':0, 'current':0 },
        'missed'  : {'penultimate':0, 'previous':0, 'current':0 },
        'received': {'penultimate':0, 'previous':0, 'current':0 },
        'summary' : {'penultimate':0, 'previous':0, 'current':0 }
    }
    for row in rows:
        if not row[0] == "dialed":
            calls['summary']['penultimate'] = calls['summary']['penultimate'] + row[1] if row[1] != None else 0
            calls['summary']['previous']    = calls['summary']['previous']    + row[2] if row[2] != None else 0
            calls['summary']['current']     = calls['summary']['current']     + row[3] if row[3] != None else 0
        try:
            percentage = float("{0:.2f}".format(((row[2]/row[1])*100)-100))
        except Exception as e:
            # division by zero
            percentage = 0
        calls[row[0]] = {
            'penultimate':  row[1] if row[1] != None else 0,
            'previous':     row[2] if row[2] != None else 0,
            'current':      row[3] if row[3] != None else 0,
            'change':       percentage
        }
    try:
        calls['summary']['change'] = float("{0:.2f}".format(((calls['summary']['previous'] /calls['summary']['penultimate'] )*100)-100))
    except:
        calls['summary']['change'] = 0 # \u221E

    return jsonify(calls)

@app.route('/api/stats/<frame>/<scope>/<localid>', methods=["GET"])
def stats_monthly_phone(frame, scope, localid):
    if request.remote_addr != '127.0.0.1':
        abort(403)
    # Set path
    path = ""
    if frame == "monthly":
        path = "monthly_phone.sql"
    if frame == "daily":
        path = "daily_phone.sql"

    # Get data
    sql  = data.read_sql(os.path.join("stats", path))
    sql  = sql.replace('$LOCALID'    , localid)
    sql  = sql.replace('$NEXT'       , str(int(scope) + 1))
    sql  = sql.replace('$CURRENT'    , str(int(scope)))
    sql  = sql.replace('$PREVIOUS'   , str(int(scope) - 1))
    sql  = sql.replace('$PENULTIMATE', str(int(scope) - 2))
    rows = db.engine.execute(sql)

    calls   = {
        'dialed'  : {'penultimate':0, 'previous':0, 'current':0 , 'change':0.0},
        'missed'  : {'penultimate':0, 'previous':0, 'current':0 , 'change':0.0},
        'received': {'penultimate':0, 'previous':0, 'current':0 , 'change':0.0},
        'summary' : {'penultimate':0, 'previous':0, 'current':0 , 'change':0.0}
    }
    for row in rows:
        if not row[0] == "dialed":
            calls['summary']['penultimate'] = calls['summary']['penultimate'] + row[1] if row[1] != None else 0
            calls['summary']['previous']    = calls['summary']['previous']    + row[2] if row[2] != None else 0
            calls['summary']['current']     = calls['summary']['current']     + row[3] if row[3] != None else 0
        try:
            percentage = float("{0:.2f}".format(((row[2]/row[1])*100)-100))
        except Exception as e:
            # division by zero
            percentage = 0
        calls[row[0]] = {
            'penultimate':  row[1] if row[1] != None else 0,
            'previous':     row[2] if row[2] != None else 0,
            'current':      row[3] if row[3] != None else 0,
            'change':       percentage
        }
    try:
        calls['summary']['change'] = float("{0:.2f}".format(((calls['summary']['previous'] /calls['summary']['penultimate'] )*100)-100))
    except:
        calls['summary']['change'] = 0 # \u221E

    return jsonify(calls)

# Graphs
@app.route('/api/graph/<frame>/<type>', methods=["GET"])
@auth.login_required
def stats_overview_graph(frame, type):
    if frame == "monthly":
        path      = config.SSL + "://" + "localhost:5000/api/stats/monthly/"
        responses = [requests.get(path + str(i)) for i in ["-9", "-6", "-3", "-0"]]

        data = []
        for response in responses:
            numbers = response.json()
            data = data + [numbers[type]["penultimate"], numbers[type]["previous"], numbers[type]["current"]]
        data.append(data[-1])

        # Create month labels
        months = ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Okt", "Nov", "Dec"]
        x = 12
        now    = time.localtime()
        labels = list(reversed([months[(time.localtime(time.mktime((now.tm_year, now.tm_mon - n, 1, 0, 0, 0, 0, 0, 0)))[:2][1]-1)] for n in range(x)]))

        return jsonify({"data":{"labels":labels, "datasets":[{"data":data}]}})

    if frame == "daily":
        path      = config.SSL + "://" + "localhost:5000/api/stats/daily/"
        responses = [requests.get(path + str(i)) for i in ["-6", "-3", "-0"]]

        data = []
        for response in responses:
            numbers = response.json()
            data = data + [numbers[type]["penultimate"], numbers[type]["previous"], numbers[type]["current"]]
        data = data[2:]
        data.append(data[-1])

        # Create month labels
        days = ["Mo", "Di", "Mi", "Do", "Fr", "Sa", "So"]
        day    = datetime.datetime.today().weekday() + 1
        #for day in range(1,8):
        #    print((days[day+1:day] + days[day:] + days[:day])[-7:])
        labels = (days[day+1:day] + days[day:] + days[:day])[-7:]

        return jsonify({"data":{"labels":labels, "datasets":[{"data":data}]}})
    else:
        return jsonify({})

@app.route('/api/graph/<frame>/<type>/<localid>', methods=["GET"])
@auth.login_required
def stats_overview_graph_phone(frame, type, localid):
    if frame == "monthly":
        path      = config.SSL + "://" + "localhost:5000/api/stats/monthly/"
        responses = [requests.get(path + str(i) + "/" + localid) for i in ["-9", "-6", "-3", "-0"]]

        data = []
        for response in responses:
            numbers = response.json()
            data = data + [numbers[type]["penultimate"], numbers[type]["previous"], numbers[type]["current"]]
        data.append(data[-1])

        # Create month labels
        months = ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Okt", "Nov", "Dec"]
        x = 12
        now    = time.localtime()
        labels = list(reversed([months[(time.localtime(time.mktime((now.tm_year, now.tm_mon - n, 1, 0, 0, 0, 0, 0, 0)))[:2][1]-1)] for n in range(x)]))

        return jsonify({"data":{"labels":labels, "datasets":[{"data":data}]}})

    if frame == "daily":
        path      = config.SSL + "://" + "localhost:5000/api/stats/daily/"
        responses = [requests.get(path + str(i) + "/" + localid) for i in ["-6", "-3", "-0"]]

        data = []
        for response in responses:
            numbers = response.json()
            data = data + [numbers[type]["penultimate"], numbers[type]["previous"], numbers[type]["current"]]
        data = data[2:]
        data.append(data[-1])

        # Create month labels
        days = ["Mo", "Di", "Mi", "Do", "Fr", "Sa", "So"]
        day    = datetime.datetime.today().weekday() + 1
        #for day in range(1,8):
        #    print((days[day+1:day] + days[day:] + days[:day])[-7:])
        labels = (days[day+1:day] + days[day:] + days[:day])[-7:]

        return jsonify({"data":{"labels":labels, "datasets":[{"data":data}]}})
    else:
        return jsonify({})

@app.route('/api/stats/phone/top/<type>', methods=["GET"])
@auth.login_required
def stats_overview_phone_top(type):
    # Get data
    rows = db.engine.execute(data.read_sql(os.path.join("top", "phone_" + type + ".sql")))

    stats = []
    for row in rows:
        stats.append((row[0], row[1], row[2]))

    return jsonify({'top':stats})

# Run Api and create DB tables
if __name__ == '__main__':
    print("Initializing API...")
    if not os.path.exists(config.DATABASE_URI):
        db.create_all()
    scheduler = scheduler.Scheduler(config.UPDATE_INTERVAL)

    print("\nStarting Log\n============")
    app.run(host='0.0.0.0', port=str(config.PORT), use_reloader=False)

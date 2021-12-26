import flask_sqlalchemy
import json
import pandas as pd
import numpy as np
import sqlite3
import math
import os
from utils import *

db = flask_sqlalchemy.SQLAlchemy()


class User(db.Model):
    __tablename__ = 'User'
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(100), unique=True)
    password = db.Column(db.String(100))
    username = db.Column(db.String(1000))
    roles = db.Column(db.Text)
    is_active = db.Column(db.Boolean, default=True, server_default='true')
    analysesEau = db.relationship('AnalyseEau', backref='User', lazy=True)
    notifications = db.relationship('Notifications', backref='User', lazy=True)
    alimentationJournalieres = db.relationship(
        'AlimentationJournalieres', backref='User', lazy=True)

    @property
    def rolenames(self):
        try:
            return self.roles.split(',')
        except Exception:
            return []

    @classmethod
    def lookup(cls, username):
        return cls.query.filter_by(username=username).one_or_none()

    @classmethod
    def identify(cls, id):
        return cls.query.get(id)

    @property
    def identity(self):
        return self.id

    def is_valid(self):
        return self.is_active


class Bassins(db.Model):
    __tablename__ = 'Bassins'
    id = db.Column(db.Integer, primary_key=True)
    libelle = db.Column(db.String(100), unique=True)
    surface = db.Column(db.Float)
    profondeur = db.Column(db.Float)
    cycles = db.relationship('Cycles', backref='Bassins', lazy=True)
    changementEau = db.relationship(
        'ChangementEau', backref='Pompes', lazy=True)
    analyseEau = db.relationship('AnalyseEau', backref='Bassins', lazy=True)
    analyseOx = db.relationship('AnalyseOx', backref='Bassins', lazy=True)
    alimentationJournaliere = db.relationship(
        'AlimentationJournalieres', backref='Bassins', lazy=True)


class Croissance(db.Model):
    __tablename__ = 'Croissance'
    id = db.Column(db.Integer, primary_key=True)
    espece_id = db.Column(db.Integer, db.ForeignKey(
        'Especes.id'), nullable=False)
    semaine = db.Column(db.Integer)
    nombre_par_livre = db.Column(db.Integer)
    pourcentage_aliment = db.Column(db.Float)


class Notifications(db.Model):
    __tablename__ = 'Notifications'
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey(
        'User.id'), nullable=False)
    text = db.Column(db.Text)
    link = db.Column(db.String(100))
    time = db.Column(db.Integer)
    priority = db.Column(db.Integer)
    seen = db.Column(db.Boolean)


class Especes(db.Model):
    __tablename__ = 'Especes'
    id = db.Column(db.Integer, primary_key=True)
    espece = db.Column(db.String(100))
    libelle = db.Column(db.String(100))
    type = db.Column(db.String(100))
    croissance = db.relationship('Croissance', backref='Especes', lazy=True)
    mortalie = db.relationship('Mortalite', backref='Especes', lazy=True)
    ventePoisson = db.relationship(
        'VentesPoisson', backref='Especes', lazy=True)


class VentesPoisson(db.Model):
    __tablename__ = 'VentesPoisson'
    id = db.Column(db.Integer, primary_key=True)
    espece_id = db.Column(db.Integer, db.ForeignKey(
        'Especes.id'), nullable=False)
    date = db.Column(db.DateTime)
    poids = db.Column(db.Integer)


class VentesCrevette(db.Model):
    __tablename__ = 'VentesCrevette'
    id = db.Column(db.Integer, primary_key=True)
    date = db.Column(db.DateTime)
    u5 = db.Column(db.Integer)
    u6 = db.Column(db.Integer)
    u8 = db.Column(db.Integer)
    u10 = db.Column(db.Integer)
    u12 = db.Column(db.Integer)
    u15 = db.Column(db.Integer)
    u16_u20 = db.Column(db.Integer)
    u21_u25 = db.Column(db.Integer)
    decortique = db.Column(db.Integer)


class Mortalite(db.Model):
    __tablename__ = 'Mortalite'
    id = db.Column(db.Integer, primary_key=True)
    espece_id = db.Column(db.Integer, db.ForeignKey(
        'Especes.id'), nullable=False)
    taux_initial = db.Column(db.Float)
    taux_hebdomadaire = db.Column(db.Float)


class Cycles(db.Model):
    __tablename__ = 'Cycles'
    id = db.Column(db.Integer, primary_key=True)
    lots = db.relationship('Lots', backref='Cycles', lazy=True)
    bassin_id = db.Column(db.Integer, db.ForeignKey(
        'Bassins.id'), nullable=False)
    type_aliment_id = db.Column(db.Integer, db.ForeignKey(
        'TypeAliment.id'), nullable=True)
    date_rempli = db.Column(db.DateTime, nullable=False)
    date_vide = db.Column(db.DateTime)
    surface = db.Column(db.Integer)
    taux_mortalite = db.Column(db.Float)


class Lots(db.Model):
    __tablename__ = 'Lots'
    id = db.Column(db.Integer, primary_key=True)
    cycle_id = db.Column(db.Integer, db.ForeignKey(
        'Cycles.id'), nullable=False)
    espece_id = db.Column(db.Integer, db.ForeignKey(
        'Especes.id'), nullable=False)
    peches = db.relationship('Peches', backref='Lots', lazy=True)
    semis = db.relationship('Semis', backref='Lots', lazy=True)
    statistiques = db.relationship('Statistiques', backref='Lots', lazy=True)
    poids_aliment_a_donner = db.Column(db.Integer, default=0)
    commentaire = db.Column(db.Text)
    termine = db.Column(db.Boolean)


class Peches(db.Model):
    __tablename__ = 'Peches'
    id = db.Column(db.Integer, primary_key=True)
    lot_id = db.Column(db.Integer, db.ForeignKey('Lots.id'), nullable=False)
    date = db.Column(db.DateTime, nullable=False)
    quantite = db.Column(db.Integer)
    poids = db.Column(db.Float)
    commentaire = db.Column(db.Text)
    destination = db.Column(db.String(100))


class Semis(db.Model):
    __tablename__ = 'Semis'
    id = db.Column(db.Integer, primary_key=True)
    lot_id = db.Column(db.Integer, db.ForeignKey('Lots.id'), nullable=False)
    date = db.Column(db.DateTime, nullable=False)
    quantite = db.Column(db.Integer)
    poids = db.Column(db.Float)
    commentaire = db.Column(db.Text)


class Statistiques(db.Model):
    __tablename__ = 'Statistiques'
    id = db.Column(db.Integer, primary_key=True)
    lot_id = db.Column(db.Integer, db.ForeignKey('Lots.id'), nullable=False)
    date = db.Column(db.DateTime, nullable=False)
    typestat = db.Column(db.String(100))
    quantitelb = db.Column(db.Float)
    mortalite = db.Column(db.Float)
    commentaire = db.Column(db.Text)


class Pompes(db.Model):
    __tablename__ = 'Pompes'
    id = db.Column(db.Integer, primary_key=True)
    libelle = db.Column(db.String(100))
    debit = db.Column(db.Integer)


class AnalyseEau(db.Model):
    __tablename__ = 'AnalyseEau'
    id = db.Column(db.Integer, primary_key=True)
    bassin_id = db.Column(db.Integer, db.ForeignKey(
        'Bassins.id'), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey(
        'User.id'), nullable=False)
    date = db.Column(db.DateTime, nullable=False)
    PH = db.Column(db.Float)
    Temp = db.Column(db.Float)
    SE = db.Column(db.Float)


class AnalyseOx(db.Model):
    __tablename__ = 'AnalyseOx'
    id = db.Column(db.Integer, primary_key=True)
    bassin_id = db.Column(db.Integer, db.ForeignKey(
        'Bassins.id'), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey(
        'User.id'), nullable=False)
    date = db.Column(db.DateTime, nullable=False)
    heure = db.Column(db.Integer)
    O2 = db.Column(db.Float)


class TypeAliment(db.Model):
    __tablename__ = 'TypeAliment'
    id = db.Column(db.Integer, primary_key=True)
    libelle = db.Column(db.String(100))
    stock = db.relationship('Stock', backref='TypeAliment', lazy=True)
    ventesAliments = db.relationship(
        'VentesAliments', backref='TypeAliment', lazy=True)
    alimentationJournaliere = db.relationship(
        'AlimentationJournalieres', backref='TypeAliment', lazy=True)


class AlimentationJournalieres(db.Model):
    __tablename__ = 'AlimentationJournalieres'
    id = db.Column(db.Integer, primary_key=True)
    bassin_id = db.Column(db.Integer, db.ForeignKey(
        'Bassins.id'), nullable=False)
    type_aliment_id = db.Column(db.Integer, db.ForeignKey(
        'TypeAliment.id'), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey(
        'User.id'), nullable=False)
    date = db.Column(db.DateTime, nullable=False)
    poids = db.Column(db.Float)
    poids_pm = db.Column(db.Float, default=0)
    maj = db.Column(db.Boolean)


class Clients(db.Model):
    __tablename__ = 'Clients'
    id = db.Column(db.Integer, primary_key=True)
    libelle = db.Column(db.String(100))
    adresse = db.Column(db.String(100))
    cedula = db.Column(db.String(100))


class VentesAliments(db.Model):
    __tablename__ = 'VentesAliments'
    id = db.Column(db.Integer, primary_key=True)
    type_aliment_id = db.Column(db.Integer, db.ForeignKey(
        'TypeAliment.id'), nullable=False)
    client = db.Column(db.Integer, db.ForeignKey(
        'Clients.id'), nullable=False)
    date = db.Column(db.DateTime, nullable=False)
    quantite = db.Column(db.Integer)
    commentaire = db.Column(db.Text)


class Stock(db.Model):
    __tablename__ = 'Stock'
    id = db.Column(db.Integer, primary_key=True)
    type_aliment_id = db.Column(db.Integer, db.ForeignKey(
        'TypeAliment.id'), nullable=False)
    date = db.Column(db.DateTime, nullable=False)
    stock = db.Column(db.Integer)
    vente = db.Column(db.Integer, default=0)
    alimentation = db.Column(db.Integer, default=0)
    ajustement = db.Column(db.Integer, default=0)
    entre = db.Column(db.Integer, default=0)
    commentaire = db.Column(db.Text)


class ChangementEau(db.Model):
    __tablename__ = 'ChangementEau'
    id = db.Column(db.Integer, primary_key=True)
    bassin_id = db.Column(db.Integer, db.ForeignKey(
        'Bassins.id'), nullable=False)
    pompe_id = db.Column(db.Integer, db.ForeignKey(
        'Pompes.id'), nullable=False)
    date = db.Column(db.DateTime, nullable=False)
    heures = db.Column(db.Integer)
    type_changement = db.Column(db.String(10))


path_directory = "csv"
db_directory = "database.db"


def transfertSimple(table_name, names_list, data, c):
    col = str(names_list).replace('[', '').replace(
        ']', '').replace("'", '').replace(' ', '')
    colPoints = ':' + col.replace(',', ',:')
    cmd = "INSERT INTO {table}({col}) VALUES ({colPoints})".format(
        table=table_name, col=col, colPoints=colPoints)
    for line in data:
        dt = dict()
        for i, name in enumerate(names_list):
            try:
                line[i] = line[i].replace(",", ".")
            except:
                pass
            dt[name] = line[i]
        c.execute(cmd, dt)


def transfertCycles(table_name, names_list, data, c):
    dataFrame = {'Bassin': data[::, 0],
                 'Cycle': data[::, 1]}

    df = pd.DataFrame(dataFrame, columns=['Bassin', 'Cycle'])
    df.to_csv('./csv/cycle_bassin.csv')

    names_list.remove('id')
    data = np.delete(data, 1, axis=1)

    col = str(names_list).replace('[', '').replace(
        ']', '').replace("'", '').replace(' ', '')
    colPoints = ':' + col.replace(',', ',:')
    cmd = "INSERT INTO {table}(id, {col}) VALUES (:id, {colPoints})".format(
        table=table_name, col=col, colPoints=colPoints)
    for j, line in enumerate(data):
        libelle = line[0]
        c.execute(f"SELECT id FROM Bassins WHERE libelle = '{libelle}'")
        fetch = c.fetchall()
        if len(fetch) == 1:
            line[0] = fetch[0][0]
            dt = dict()
            for i, name in enumerate(names_list):
                try:
                    line[i] = line[i].replace(",", ".")
                except:
                    pass
                dt[name] = line[i]
            dt['id'] = j
            c.execute(cmd, dt)
        else:
            print(line)

    return "Fini cycles"


def transfertCroissance(table_name, names_list, data, c):
    names_list.pop()

    col = str(names_list).replace('[', '').replace(
        ']', '').replace("'", '').replace(' ', '')
    colPoints = ':' + col.replace(',', ',:')
    cmd = "INSERT INTO {table}({col}) VALUES ({colPoints})".format(
        table=table_name, col=col, colPoints=colPoints)
    for line in data:
        espece = line[0]
        c.execute(f"SELECT id FROM Especes WHERE espece = '{espece}'")
        fetch = c.fetchall()
        if len(fetch) == 1:
            line[0] = fetch[0][0]
            dt = dict()
            for i, name in enumerate(names_list):
                try:
                    line[i] = line[i].replace(",", ".")
                except:
                    pass
                if name == "nombre_par_livre":
                    line[i] = float(line[i].replace(',', '.'))
                    if line[i] != 0:
                        dt[name] = line[i]
                    else:
                        dt[name] = grPoisson_To_nbrLivres(
                            float(line[-1].replace(',', '.')))
                else:
                    dt[name] = line[i]
            c.execute(cmd, dt)

    return "Fini croissances"


def transfertStock(table_name, names_list, data, c):
    names_list = ["date", "stock", "entre", "alimentation", "vente", "ajustement",
                  "commentaire", "type_aliment_id"]
    col = str(names_list).replace('[', '').replace(
        ']', '').replace("'", '').replace(' ', '')
    colPoints = ':' + col.replace(',', ',:')
    cmd = "INSERT INTO {table}({col}) VALUES ({colPoints})".format(
        table=table_name, col=col, colPoints=colPoints)
    oldStock = dict()
    for i, line in enumerate(data):
        dt = dict()
        dt["date"] = line[0]
        dt["alimentation"] = line[1]
        dt["entre"] = line[2]
        dt["vente"] = 0
        dt["ajustement"] = line[3]
        dt["stock"] = line[4]
        dt["commentaire"] = line[5]
        type_aliment = line[6]
        c.execute(
            f"SELECT id FROM TypeAliment WHERE libelle = '{type_aliment}'")
        if type_aliment not in oldStock:
            oldStock[type_aliment] = - \
                float(line[1]) + float(line[2]) + float(line[3])
        else:
            oldStock[type_aliment] += - \
                float(line[1]) + float(line[2]) + float(line[3])
        dt["stock"] = oldStock[type_aliment]
        fetch = c.fetchall()
        if len(fetch) != 0:
            dt["type_aliment_id"] = fetch[0][0]
            if fetch[0][0] not in [1, 6, 8, 9, 10, 11, 12, 13, 14, 15]:
                c.execute(cmd, dt)
    return "Fini Stock"


def transfertLots(table_name, names_list, data, c):
    ids = pd.read_csv('./csv/cycle_bassin.csv',
                      names=['id', 'Bassin', 'Cycle'])
    ids = np.array(ids[1::])
    ids[:, 0] = ids[:, 0] + 1

    dataFrame = {'Bassin': data[::, 0],
                 'Cycle': data[::, 1],
                 'Lots': data[::, 2]}

    df = pd.DataFrame(dataFrame, columns=['Bassin', 'Cycle', 'Lots'])
    df.to_csv('./csv/cycle_bassin_lots.csv')

    names_list.remove('bassin')
    names_list.remove('lots')
    data = np.delete(data, 2, axis=1)

    col = str(names_list).replace('[', '').replace(
        ']', '').replace("'", '').replace(' ', '')
    colPoints = ':' + col.replace(',', ',:')
    cmd = "INSERT INTO {table}(id, {col}, termine) VALUES (:id, {colPoints}, 0)".format(
        table=table_name, col=col, colPoints=colPoints)
    for j, line in enumerate(data):
        cycle_id = np.where((ids[::, 1::] == [line[0], line[1]]).all(axis=1))
        if len(cycle_id[0]) != 0:
            espece = line[2]
            c.execute(f"SELECT id FROM Especes WHERE espece = '{espece}'")
            fetch = c.fetchall()
            if len(fetch) == 1:
                line[2] = fetch[0][0]
                dt = dict()
                line[1] = int(cycle_id[0][0])
                if line[1] != 0:
                    for i, name in enumerate(names_list):
                        try:
                            line[i] = line[i].replace(",", ".")
                        except:
                            pass
                        dt[name] = line[i+1]
                    dt['id'] = j  # PROBLEME
                    c.execute(cmd, dt)
    return "Fini Lots"


def transfertSemisPechesStat(table_name, names_list, data, c):
    ids = pd.read_csv('./csv/cycle_bassin_lots.csv',
                      names=['id', 'Bassin', 'Cycle', 'Lots'])
    ids = np.array(ids[1::])
    ids[:, 0] = ids[:, 0]

    names_list.remove('bassin')
    names_list.remove('cycle')

    col = str(names_list).replace('[', '').replace(
        ']', '').replace("'", '').replace(' ', '')
    colPoints = ':' + col.replace(',', ',:')
    cmd = "INSERT INTO {table}({col}) VALUES ({colPoints})".format(
        table=table_name, col=col, colPoints=colPoints)
    for line in data:
        lot_id = np.where(
            (ids[::, 1::] == [line[0], line[1], line[2]]).all(axis=1))
        if len(lot_id[0]) != 0:
            line[2] = int(lot_id[0][0])
            try:
                boole = math.isnan(float(line[4].replace(",", ".")))
            except:
                boole = math.isnan(line[4])
            if line[2] != 0 and line[3] != "" and not boole:
                dt = dict()
                for i, name in enumerate(names_list):
                    try:
                        line[i+2] = line[i+2].replace(",", ".")
                    except:
                        pass
                    dt[name] = line[i+2]
                c.execute(cmd, dt)
    return f"Fini {table_name}"


def transfertStat(table_name, names_list, data, c):
    ids = pd.read_csv('./csv/cycle_bassin_lots.csv',
                      names=['id', 'Bassin', 'Cycle', 'Lots'])
    ids = np.array(ids[1::])
    ids[:, 0] = ids[:, 0]

    names_list.remove('bassin')
    names_list.remove('cycle')

    col = str(names_list).replace('[', '').replace(
        ']', '').replace("'", '').replace(' ', '')
    colPoints = ':' + col.replace(',', ',:')
    cmd = "INSERT INTO {table}({col}) VALUES ({colPoints})".format(
        table=table_name, col=col, colPoints=colPoints)
    for line in data:
        lot_id = np.where(
            (ids[::, 1::] == [line[0], line[1], line[2]]).all(axis=1))
        if len(lot_id[0]) != 0:
            line[2] = int(lot_id[0][0])
            if line[2] != 0:
                dt = dict()
                for i, name in enumerate(names_list):
                    try:
                        line[i+2] = line[i+2].replace(",", ".")
                    except:
                        pass
                    dt[name] = line[i+2]
                c.execute(cmd, dt)
    return f"Fini {table_name}"


def transfertMortalite(table_name, names_list, data, c):
    col = str(names_list).replace('[', '').replace(
        ']', '').replace("'", '').replace(' ', '')
    colPoints = ':' + col.replace(',', ',:')
    cmd = "INSERT INTO {table}({col}) VALUES ({colPoints})".format(
        table=table_name, col=col, colPoints=colPoints)
    for line in data:
        espece = line[0]
        c.execute(f"SELECT id FROM Especes WHERE espece = '{espece}'")
        fetch = c.fetchall()
        if len(fetch) == 1:
            line[0] = fetch[0][0]
            dt = dict()
            for i, name in enumerate(names_list):
                try:
                    line[i] = line[i].replace(",", ".")
                except:
                    pass
                dt[name] = line[i]
            c.execute(cmd, dt)
    return f"Fini {table_name}"


def transfertChangementEau(table_name, names_list, data, c):
    col = str(names_list).replace('[', '').replace(
        ']', '').replace("'", '').replace(' ', '')
    colPoints = ':' + col.replace(',', ',:')
    cmd = "INSERT INTO {table} ({col}) VALUES ({colPoints})".format(
        table=table_name, col=col, colPoints=colPoints)
    for line in data:
        bassin = line[0]
        c.execute(f"SELECT id FROM Bassins WHERE libelle = '{bassin}'")
        fetch = c.fetchall()
        if len(fetch) == 1:
            line[0] = fetch[0][0]
            dt = dict()
            for i, name in enumerate(names_list):
                try:
                    line[i] = line[i].replace(",", ".")
                except:
                    pass
                dt[name] = line[i]
            if float(dt['heures']) != 0:
                try:
                    c.execute(cmd, dt)
                except:
                    print(cmd, dt)
            else:
                print(line)
    return f"Fini {table_name}"


def transfertAnalyseEau(table_name, names_list, data, c):
    col = str(names_list).replace('[', '').replace(
        ']', '').replace("'", '').replace(' ', '')
    colPoints = ':' + col.replace(',', ',:')
    cmd = "INSERT INTO {table}(user_id, {col}) VALUES (0, {colPoints})".format(
        table=table_name, col=col, colPoints=colPoints)
    for line in data:
        bassin = line[0]
        c.execute(f"SELECT id FROM Bassins WHERE libelle = '{bassin}'")
        fetch = c.fetchall()
        if len(fetch) == 1:
            line[0] = fetch[0][0]
            dt = dict()
            for i, name in enumerate(names_list):
                try:
                    line[i] = line[i].replace(",", ".")
                except:
                    pass
                dt[name] = line[i]
            c.execute(cmd, dt)
    return f"Fini {table_name}"


def transfertAnalyseOx(table_name, names_list, data, c):
    col = str(names_list).replace('[', '').replace(
        ']', '').replace("'", '').replace(' ', '')
    colPoints = ':' + col.replace(',', ',:')
    cmd = "INSERT INTO {table}(user_id, {col}, heure) VALUES (0, {colPoints}, 0)".format(
        table=table_name, col=col, colPoints=colPoints)
    for line in data:
        bassin = line[0]
        c.execute(f"SELECT id FROM Bassins WHERE libelle = '{bassin}'")
        fetch = c.fetchall()
        if len(fetch) == 1:
            line[0] = fetch[0][0]
            dt = dict()
            for i, name in enumerate(names_list):
                try:
                    line[i] = line[i].replace(",", ".")
                except:
                    pass
                dt[name] = line[i]
            c.execute(cmd, dt)
    return f"Fini {table_name}"


def transfertAlimentationJournalieres(table_name, names_list, data, c):
    col = str(names_list).replace('[', '').replace(
        ']', '').replace("'", '').replace(' ', '')
    colPoints = ':' + col.replace(',', ',:')
    cmd = "INSERT INTO {table}(user_id, {col}) VALUES (0, {colPoints})".format(
        table=table_name, col=col, colPoints=colPoints)
    for line in data:
        bassin = line[0]
        c.execute(f"SELECT id FROM Bassins WHERE libelle = '{bassin}'")
        fetch = c.fetchall()
        if len(fetch) == 1:
            line[0] = fetch[0][0]
            aliment = line[3]
            c.execute(
                f"SELECT id FROM TypeAliment WHERE libelle = '{aliment}'")
            fetch = c.fetchall()
            if len(fetch) == 1:
                line[3] = fetch[0][0]
                dt = dict()
                for i, name in enumerate(names_list):
                    try:
                        line[i] = line[i].replace(",", ".")
                    except:
                        pass
                    if name == "maj":
                        dt[name] = (line[i] == "True")
                    else:
                        dt[name] = line[i]
                if line[3] not in [1, 6, 8, 9, 10, 11, 12, 13, 14, 15]:
                    c.execute(cmd, dt)
    return f"Fini {table_name}"


def transfertVentesPoisson(table_name, names_list, data, c):
    col = str(names_list).replace('[', '').replace(
        ']', '').replace("'", '').replace(' ', '')
    colPoints = ':' + col.replace(',', ',:')
    cmd = "INSERT INTO {table}({col}) VALUES ({colPoints})".format(
        table=table_name, col=col, colPoints=colPoints)
    for line in data:
        bassin = line[0]
        c.execute(f"SELECT id FROM Bassins WHERE libelle = '{bassin}'")
        fetch = c.fetchall()
        if len(fetch) == 1:
            line[0] = fetch[0][0]
            dt = dict()
            for i, name in enumerate(names_list):
                try:
                    line[i] = line[i].replace(",", ".")
                except:
                    pass
                dt[name] = line[i]
            c.execute(cmd, dt)
    return f"Fini {table_name}"


def transfertVentesPoisson(table_name, names_list, data, c):
    col = str(names_list).replace('[', '').replace(
        ']', '').replace("'", '').replace(' ', '')
    colPoints = ':' + col.replace(',', ',:')
    cmd = "INSERT INTO {table}({col}) VALUES ({colPoints})".format(
        table=table_name, col=col, colPoints=colPoints)
    for line in data:
        espece = line[1]
        if espece == "carpe":
            line[1] = 1
        elif espece == "tilapia":
            line[1] = 7
        else:
            continue
        dt = dict()
        for i, name in enumerate(names_list):
            try:
                line[i] = line[i].replace(",", ".")
            except:
                pass
            dt[name] = line[i]
        c.execute(cmd, dt)
    return f"Fini {table_name}"


def transfertVentesCrevette(table_name, names_list, data, c):
    col = str(names_list).replace('[', '').replace(
        ']', '').replace("'", '').replace(' ', '')
    colPoints = ':' + col.replace(',', ',:')
    cmd = "INSERT INTO {table}({col}) VALUES ({colPoints})".format(
        table=table_name, col=col, colPoints=colPoints)
    for line in data:
        dt = dict()
        for i, name in enumerate(names_list):
            try:
                line[i] = line[i].replace(",", ".")
            except:
                pass
            dt[name] = line[i]
        c.execute(cmd, dt)
    return f"Fini {table_name}"


def fillDatabase():
    fc_dict = {
        "cycles.csv": transfertCycles,
        "croissance.csv": transfertCroissance,
        "stock.csv":  transfertStock,
        "lots.csv": transfertLots,
        "semis.csv": transfertSemisPechesStat,
        "peches.csv": transfertSemisPechesStat,
        "statistiques.csv": transfertStat,
        "mortalite.csv": transfertMortalite,
        "changementEau.csv": transfertChangementEau,
        "analyseEau.csv": transfertAnalyseEau,
        "analyseOx.csv": transfertAnalyseOx,
        "alimentationJournalieres.csv": transfertAlimentationJournalieres,
        "ventesPoisson.csv": transfertVentesPoisson,
        "ventesCrevette.csv": transfertVentesCrevette,
    }
    with open('db.json') as json_file:
        table_list = json.load(json_file)
    for table in table_list:
        table_name = table['table_name'].capitalize().replace('.csv', '')
        csv = pd.read_csv(os.path.join(
            path_directory, table['table_name']), names=table['names_list'], quotechar="'", sep=";")
        csv = csv[1::]

        for pop in table['pop']:
            csv.pop(pop)
            table['names_list'].remove(pop)
        print(csv.head())

        data = np.array(csv)
        conn = sqlite3.connect(db_directory)
        c = conn.cursor()

        c.execute("DELETE FROM {table}".format(table=table_name))
        conn.commit()

        if 'date' in table['names_list']:
            k = table['names_list'].index('date')
            print("Changement des dates")
            for i, date in enumerate(data[::, k]):
                try:
                    date_splited = date.split('/')
                    data[::, k][i] = date_splited[2] + '-' + \
                        date_splited[1].zfill(
                            2) + '-' + date_splited[0].zfill(2)
                except:
                    data[::, k][i] = ''

        if 'date_rempli' in table['names_list']:
            k = table['names_list'].index('date_rempli')
            print("Changement des dates")
            for i, date in enumerate(data[::, k]):
                try:
                    date_splited = date.split('/')
                    data[::, k][i] = date_splited[2] + '-' + \
                        date_splited[1].zfill(
                            2) + '-' + date_splited[0].zfill(2)
                except:
                    data[::, k][i] = ''

        if 'date_vide' in table['names_list']:
            k = table['names_list'].index('date_vide')
            print("Changement des dates")
            for i, date in enumerate(data[::, k]):
                try:
                    date_splited = date.split('/')
                    data[::, k][i] = date_splited[2] + '-' + \
                        date_splited[1].zfill(
                            2) + '-' + date_splited[0].zfill(2)
                except:
                    data[::, k][i] = ''

        if table['simple'] == "true":
            transfertSimple(table_name, table['names_list'], data, c)
        else:
            print(fc_dict[table['table_name']](
                table_name, table['names_list'], data, c))
        conn.commit()
        conn.close()


if __name__ == '__main__':
    fillDatabase()
# Il "manque" :
# alerteau

# Problèmes
# Limite 1000 pour cycles, lots, alimentation

# Todo
# appliqué croissance avec pêches (cache donnée pour les étangs non terminé?)

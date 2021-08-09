from flask_restful import Resource
import flask_praetorian
import sqlite3
from flask import request
from datetime import datetime
from cycles import getLots
from utils import changeDate, changeDateBack, changeDateBack2

dbPath = "database.db"


class Pompes(Resource):
    @flask_praetorian.auth_required
    def get(self):
        conn = sqlite3.connect(dbPath)
        c = conn.cursor()
        c.execute(f"SELECT id, libelle FROM Pompes")
        pompes = c.fetchall()
        c.execute(f"SELECT Bassins.id, Bassins.libelle FROM Cycles, Bassins WHERE Cycles.bassin_id = Bassins.id AND Cycles.date_vide = ''")
        bassins = c.fetchall()
        conn.close()
        return {"bassins": bassins, "pompes": pompes}, 200

    @flask_praetorian.auth_required
    def post(self):
        data = request.json
        conn = sqlite3.connect(dbPath)
        c = conn.cursor()
        c.execute(
            f"INSERT INTO ChangementEau (bassin_id, pompe_id, date, heures, type_changement) VALUES ({data['bassin']}, {data['pompe']}, '{data['date']}', {data['heure']}, '{data['type']}')")
        conn.commit()
        conn.close()
        return {"message": "Changement d'eau crée"}, 200


class ChangementEau(Resource):
    @flask_praetorian.auth_required
    def get(self):
        conn = sqlite3.connect(dbPath)
        c = conn.cursor()
        c.execute(
            f"SELECT ChangementEau.id, Bassins.libelle, Pompes.libelle, ChangementEau.date, ChangementEau.heures, ChangementEau.type_changement FROM ChangementEau, Bassins, Pompes WHERE Bassins.id=ChangementEau.bassin_id AND ChangementEau.pompe_id=Pompes.id ORDER BY ChangementEau.date DESC")
        chg = c.fetchmany(50)
        for i, item in enumerate(chg):
            d = dict()
            for j, name in enumerate(["id", "Bassin", "Pompe",
                                      "Date", "Heures", "Type"]):
                if name == "Date":
                    d[name] = changeDate(chg[i][j])
                else:
                    d[name] = chg[i][j]
            chg[i] = d
        conn.close()
        return {"changement": chg}, 200

    @flask_praetorian.auth_required
    def post(self):
        data = request.json
        conn = sqlite3.connect(dbPath)
        c = conn.cursor()
        c.execute(f"DELETE FROM ChangementEau WHERE id ={data['id']}")
        conn.commit()
        conn.close()
        return {"message": "Bien supprimé"}, 200


class ShowTable(Resource):
    @flask_praetorian.auth_required
    def get(self, table):
        conn = sqlite3.connect(dbPath)
        c = conn.cursor()
        if table in ["ChangementEau"]:
            c.execute(
                f"SELECT * FROM {table} ORDER BY date DESC ")
        else:
            c.execute(
                f"SELECT * FROM {table} ")
        names = list(map(lambda x: x[0], c.description))
        select = c.fetchmany(200)
        ch = -1
        for i, item in enumerate(select):
            d = dict()
            for j, name in enumerate(names):
                if name == "espece_id":
                    c.execute(
                        f"SELECT libelle FROM Especes WHERE id={select[i][j]} LIMIT 1")
                    d["Espece"] = c.fetchone()[0]
                    ch = j
                else:
                    d[name] = select[i][j]
            select[i] = d
        if ch != -1:
            names[ch] = "Espece"
        conn.close()
        return {"headers": names, "data": select}, 200

    @flask_praetorian.auth_required
    def post(self, table):
        data = request.json
        id = data['id']
        conn = sqlite3.connect(dbPath)
        c = conn.cursor()
        c.execute(f"SELECT * FROM {table} WHERE id = {id}")
        select = c.fetchall()
        if len(select) == 1:
            changes = ''
            for name in data.keys():
                if name != 'id':
                    if name == "date":
                        ch = changeDateBack(data[name])
                    else:
                        ch = data[name]
                    try:
                        int(ch)
                        changes += f'{name} = {ch},'
                    except:
                        changes += f'{name} = "{ch}",'

            changes = changes.strip(',')
            command = f"UPDATE {table} SET {changes} WHERE id = {id}"
            c.execute(command)
            conn.commit()
            conn.close()
            return {"message": "Changement effectué"}, 201
        elif len(select) == 0:
            values = '('
            for name in data.keys():
                if data[name] == None:
                    return {'message': "column can't be null"}, 400
                ch = data[name]
                try:
                    int(ch)
                    values += f'{ch},'
                except:
                    values += f'"{ch}",'
            values = values.strip(',') + (')')
            command = f"INSERT INTO {table} VALUES {values}"
            c.execute(command)
            conn.commit()
            conn.close()
            return {"message": "yes"}, 201


class Bassins(Resource):
    @flask_praetorian.auth_required
    def get(self, bassin=None):
        conn = sqlite3.connect(dbPath)
        c = conn.cursor()
        c.execute("SELECT libelle FROM Bassins")
        fetch = c.fetchall()
        bassins = [i[0] for i in fetch]
        conn.close()
        return {"bassins": bassins}, 200


def changementStock(c, id_aliment, date, alimentation, commentaire="."):
    c.execute(
        f"SELECT * FROM Stock WHERE type_aliment_id={id_aliment} AND date>'{date}' ORDER BY date ASC")
    stocks = c.fetchall()
    c.execute(
        f"SELECT * FROM Stock WHERE type_aliment_id={id_aliment} AND date <='{date}' ORDER BY date DESC LIMIT 1")
    last = c.fetchone()
    stock = last[3] - int(alimentation)

    if last[2] != date:
        c.execute(
            f"INSERT INTO Stock (type_aliment_id, date, stock, alimentation, commentaire, vente, ajustement, entre) VALUES ({id_aliment}, '{date}', {stock}, {alimentation}, '{commentaire}', 0, 0, 0)")
    else:
        c.execute(
            f"UPDATE Stock SET stock = {stock}, alimentation = {last[5] + alimentation}, commentaire = '{commentaire}' WHERE id={last[0]}")
    for s in stocks:
        c.execute(
            f"UPDATE Stock SET stock = {s[3] - int(alimentation)} WHERE id={s[0]}")


class Alimentation(Resource):
    @flask_praetorian.auth_required
    def get(self, date=datetime.now().strftime("%Y-%m-%d")):
        conn = sqlite3.connect(dbPath)
        c = conn.cursor()
        c.execute(
            "SELECT id, bassin_id, date_rempli, date_vide, surface, type_aliment_id FROM Cycles WHERE date_vide = ''")
        names = list(map(lambda x: x[0].replace('_', ' '), c.description))
        select = c.fetchall()
        c.execute("SELECT id, libelle FROM TypeAliment")
        aliments = c.fetchall()
        for i, cycle in enumerate(select):
            id_bassin = cycle[1]
            c.execute(f"SELECT libelle FROM Bassins WHERE id = {id_bassin}")
            bassin = c.fetchall()[0][0]
            d = dict()
            lots = getLots(c, cycle[0])
            d['poids aliment a donner'] = 0
            for l in lots:
                d['poids aliment a donner'] += l[3]
            for j, name in enumerate(names):
                if name == "bassin id":
                    d["Bassin"] = bassin
                elif name == "type aliment id":
                    pass
                else:
                    d[name] = cycle[j]
            c.execute(
                f"SELECT TypeAliment.id, AlimentationJournalieres.poids, AlimentationJournalieres.poids_pm, AlimentationJournalieres.maj FROM AlimentationJournalieres, TypeAliment WHERE AlimentationJournalieres.type_aliment_id=TypeAliment.id AND AlimentationJournalieres.date='{date}' AND AlimentationJournalieres.bassin_id={id_bassin}")
            alimentation = c.fetchone()
            d["ali"] = alimentation != None
            if d["ali"]:
                d["Type_Aliment"] = alimentation[0]
                d["Poids"] = alimentation[1]
                d["Poids_pm"] = alimentation[2]
                d["maj"] = alimentation[3] == 1
            elif cycle[5] != None:
                d["Type_Aliment"] = cycle[5]
            select[i] = d
        return {"cycles": select, "aliments": aliments, "date": date}, 200

    @flask_praetorian.auth_required
    def put(self):
        data = request.json
        conn = sqlite3.connect(dbPath)
        c = conn.cursor()
        print(data)
        c.execute(
            f"UPDATE Lots SET poids_aliment_a_donner = {data['poids']} WHERE id ={data['id']}")
        conn.commit()
        conn.close()
        return {"message": "Alimentation maj"}, 200

    @flask_praetorian.auth_required
    def post(self):
        data = request.json
        bassin = data["bassin"]
        poids = data["poids"]
        poids_pm = data["poids_pm"]
        aliment = data["aliment"]
        date = data["date"]
        conn = sqlite3.connect(dbPath)
        c = conn.cursor()
        c.execute(
            f"SELECT Cycles.id, Cycles.type_aliment_id FROM Cycles, Bassins WHERE Cycles.bassin_id = Bassins.id AND Cycles.date_vide = '' AND Bassins.libelle = '{bassin}' ORDER BY Cycles.date_rempli DESC")
        cycle = c.fetchone()
        if cycle[1] != aliment:
            c.execute(
                f"UPDATE Cycles SET type_aliment_id = {aliment} WHERE id = {cycle[0]}")
        c.execute(
            f"SELECT AlimentationJournalieres.id, Bassins.id, AlimentationJournalieres.poids FROM AlimentationJournalieres, Bassins WHERE Bassins.id=AlimentationJournalieres.Bassin_id AND AlimentationJournalieres.date='{date}' AND Bassins.libelle='{bassin}'")
        fetch = c.fetchall()
        c.execute(
            f"SELECT stock, date, id, alimentation FROM Stock WHERE type_aliment_id = {aliment} AND date <= '{date}' ORDER BY date DESC LIMIT 1")
        s = c.fetchone()
        if len(fetch) > 0:
            id = fetch[0][0]
            c.execute(
                f'UPDATE AlimentationJournalieres SET poids = {poids}, poids_pm = {poids_pm}, maj = 1 WHERE id = {id}')
            changementStock(c, aliment, date, poids - fetch[0][2])
            conn.commit()
            conn.close()
            return {"message": "Alimentation maj"}, 200
        else:
            c.execute(f'SELECT id FROM Bassins WHERE libelle="{bassin}"')
            fetch = c.fetchall()
            bassin_id = fetch[0][0]
            c.execute(
                f"INSERT INTO AlimentationJournalieres (bassin_id, type_aliment_id, user_id, date, poids, poids_pm, maj) VALUES ({bassin_id}, {aliment}, 0,'{date}', {poids}, {poids_pm}, 1)")
            changementStock(c, aliment, date, poids)
            conn.commit()
            conn.close()
            return {"message": "Alimentation crée"}, 200


class EspecesRes(Resource):
    @flask_praetorian.auth_required
    def get(self):
        conn = sqlite3.connect(dbPath)
        c = conn.cursor()
        c.execute(f"SELECT id, libelle FROM Especes")
        especes = c.fetchall()
        c.execute(f"SELECT id, libelle FROM Bassins")
        bassins = c.fetchall()
        conn.close()
        return {"bassins": bassins, "especes": especes}, 200


class Notifications(Resource):
    @flask_praetorian.auth_required
    def get(self):
        user_id = flask_praetorian.current_user_id()
        conn = sqlite3.connect(dbPath)
        c = conn.cursor()
        c.execute(
            f"SELECT id, text, link, time, priority, seen FROM Notifications WHERE user_id={user_id}")
        notifications = c.fetchall()
        for i, item in enumerate(notifications):
            d = dict()
            for j, name in enumerate(["id", "text",
                                      "link",
                                      "time",
                                      "priority", "seen"]):
                if name == "Date":
                    d[name] = changeDate(notifications[i][j])
                else:
                    d[name] = notifications[i][j]
            notifications[i] = d
        conn.close()
        return {"notifications": notifications}, 200

    @flask_praetorian.auth_required
    def put(self):
        user_id = flask_praetorian.current_user_id()
        conn = sqlite3.connect(dbPath)
        c = conn.cursor()
        c.execute(
            f"UPDATE Notifications SET seen = 1 WHERE user_id={user_id} AND seen = 0")
        conn.commit()
        conn.close()
        return {"message": "Notifications vues"}, 200

    @flask_praetorian.auth_required
    def post(self):
        id = request.json["id"]
        conn = sqlite3.connect(dbPath)
        c = conn.cursor()
        c.execute(f"DELETE FROM Notifications WHERE id = {id}")
        conn.commit()
        conn.close()
        return {"message": "Notifications supprimé"}, 200

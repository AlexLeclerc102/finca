from flask_restful import Resource
import flask_praetorian
import sqlite3
from flask import request
from utils import changeDate, changeDateBack

dbPath = "database.db"


class Lots(Resource):
    @flask_praetorian.auth_required
    def get(self):
        conn = sqlite3.connect(dbPath)
        c = conn.cursor()
        c.execute(
            f'SELECT Bassins.libelle, Cycles.id, Lots.id, Lots.commentaire FROM Bassins, Cycles, Lots WHERE Cycles.bassin_id = Bassins.id AND Cycles.id = Lots.cycle_id AND Cycles.termine = FALSE ')
        lots = c.fetchall()
        return {"message": "success", "lotsList": lots}, 200

    @flask_praetorian.auth_required
    def post(self):
        conn = sqlite3.connect(dbPath)
        c = conn.cursor()
        data = request.json
        c.execute(
            f"INSERT INTO Lots (cycle_id, espece_id, commentaire) VALUES ({data['cycle_id']} ,{data['espece_id']}, '{data['commentaire']}')")
        conn.commit()
        conn.close()
        return {"message": "Lot ajouté"}, 200


class LotData(Resource):
    @flask_praetorian.auth_required
    def get(self, lot_id):
        conn = sqlite3.connect(dbPath)
        c = conn.cursor()
        c.execute(
            f'SELECT id, date, quantite, poids, commentaire, destination, lot_id FROM Peches WHERE lot_id = "{lot_id}"')
        peches = c.fetchall()
        for i, p in enumerate(peches):
            pech = dict()
            pech["id"] = p[0]
            pech["date"] = changeDate(p[1])
            pech["quantite"] = round(p[2])
            try:
                pech["poids"] = round(p[3], 2)
                pech["grpoisson"] = round(p[3] * 453.592 / p[2], 2)
                pech["quantitelb"] = round(p[2] / p[3], 2)
            except:
                print(p)
            pech["commentaire"] = p[4]
            pech["destination"] = p[5]
            pech["lot_id"] = p[6]
            peches[i] = pech
        c.execute(
            f'SELECT id, date, quantite, poids, commentaire, lot_id  FROM Semis WHERE lot_id = "{lot_id}"')
        semis = c.fetchall()
        for i, s in enumerate(semis):
            sem = dict()
            sem["id"] = s[0]
            sem["date"] = changeDate(s[1])
            sem["quantite"] = round(s[2])
            sem["poids"] = round(s[3], 2)
            sem["grpoisson"] = round(s[3] * 453.592 / s[2], 2)
            sem["quantitelb"] = round(s[2] / s[3], 2)
            sem["commentaire"] = s[4]
            sem["lot_id"] = s[5]
            semis[i] = sem
        c.execute(
            f'SELECT id, date, typestat, quantitelb, commentaire, lot_id  FROM Statistiques WHERE lot_id = "{lot_id}"')
        statistiques = c.fetchall()
        for i, s in enumerate(statistiques):
            stat = dict()
            stat["id"] = s[0]
            stat["date"] = changeDate(s[1])
            stat["typestat"] = s[2]
            stat["quantitelb"] = round(s[3], 2)
            stat["grpoisson"] = round(453.592 / s[3], 2)
            stat["commentaire"] = s[4]
            stat["lot_id"] = s[5]
            statistiques[i] = stat
        c.execute(
            f"SELECT Especes.libelle FROM Especes, Lots WHERE Lots.espece_id = Especes.id AND Lots.id = '{lot_id}'")
        espece = c.fetchone()
        conn.close()
        return {"message": "success", "peches": peches, "semis": semis, "statistiques": statistiques, "espece": espece}, 201

    @flask_praetorian.auth_required
    def post(self, lot_id):
        data = request.json
        conn = sqlite3.connect(dbPath)
        c = conn.cursor()
        c.execute(f"DELETE FROM {lot_id} WHERE id ={data['id']}")
        conn.commit()
        conn.close()
        return {"message": "Bien supprimé"}, 200


class Semis(Resource):
    @flask_praetorian.auth_required
    def post(self):
        data = request.json
        poids = float(data["poids"])
        conn = sqlite3.connect(dbPath)
        c = conn.cursor()
        if "commentaire" in data:
            c.execute(
                f"INSERT INTO Semis (lot_id, date, quantite, poids, commentaire) VALUES ({data['lot']}, '{data['date']}', {round(data['quantite'])}, {round(poids,4)}, '{data['commentaire']}')")
        else:
            c.execute(
                f"INSERT INTO Semis (lot_id, date, quantite, poids) VALUES ({data['lot']}, '{data['date']}', {round(data['quantite'])}, {round(poids,4)})")
        conn.commit()
        conn.close()
        return {"message": "Semis bien ajouté"}, 200


class Stats(Resource):
    @flask_praetorian.auth_required
    def post(self):
        data = request.json
        conn = sqlite3.connect(dbPath)
        c = conn.cursor()
        if "commentaire" in data:
            c.execute(
                f"INSERT INTO Statistiques (lot_id, date, quantitelb, typestat, commentaire) VALUES ({data['lot']}, '{data['date']}', {round(data['quantitelb'],4)}, '{data['typeStat']}', '{data['commentaire']}')")
        else:
            c.execute(
                f"INSERT INTO Statistiques (lot_id, date, quantitelb, typestat) VALUES ({data['lot']}, '{data['date']}', {round(data['quantitelb'],4)}, '{data['typeStat']}')")
        conn.commit()
        conn.close()
        return {"message": "Statistique bien ajouté"}, 200


class Peches(Resource):
    @flask_praetorian.auth_required
    def post(self):
        data = request.json
        poids = float(data["poids"])
        conn = sqlite3.connect(dbPath)
        c = conn.cursor()
        if "commentaire" in data:
            c.execute(
                f"INSERT INTO Peches (lot_id, date, quantite, poids, commentaire, destination) VALUES ({data['lot']}, '{data['date']}', {round(data['quantite'],0)}, {round(poids,4)}, '{data['commentaire']}','{data['destination']}')")
        else:
            c.execute(
                f"INSERT INTO Peches (lot_id, date, quantite, poids, destination) VALUES ({data['lot']}, '{data['date']}', {round(data['quantite'], 0)}, {round(poids,4)}, '{data['destination']}')")
        conn.commit()
        conn.close()
        return {"message": "Peches bien ajouté"}, 200

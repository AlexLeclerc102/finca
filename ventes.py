from flask_restful import Resource
import flask_praetorian
import sqlite3
from flask import request
from utils import changeDate, changeDateBack
from datetime import datetime

dbPath = "database.db"


class VenteCrevette(Resource):
    @flask_praetorian.auth_required
    def get(self):
        conn = sqlite3.connect(dbPath)
        c = conn.cursor()
        c.execute(
            f"SELECT id, date, u5, u6, u8, u10, u12, u15, u16_u20, u21_u25, decortique FROM VentesCrevette ORDER BY date DESC")
        ventes = c.fetchmany(50)

        for i, item in enumerate(ventes):
            c.execute(
                f"SELECT Peches.poids FROM Peches, Lots WHERE Lots.id=Peches.lot_id AND date='{item[1]}' AND Lots.espece_id=4 AND destination='V'")
            peches = c.fetchall()

            d = dict()
            d['total venta'] = 0
            for j, name in enumerate(["id", "fecha",
                                      "u5",
                                      "u6",
                                      "u8",
                                      "u10",
                                      "u12",
                                      "u15",
                                      "u16/20",
                                      "u21/25", "pelado"]):
                if name == "fecha":
                    d[name] = changeDate(ventes[i][j])
                else:
                    if name != "id":
                        if name == "pelado":
                            d['total venta'] += ventes[i][j]*2.2
                        else:
                            d['total venta'] += ventes[i][j]
                    d[name] = ventes[i][j]
            d['total pesca'] = 0
            for p in peches:
                d['total pesca'] += p[0]
            if d['total pesca'] != 0:
                d['% perdida'] = str(round(
                    (d['total pesca'] - d['total venta']) / d['total pesca'] * 100, 1)) + ' %'
            else:
                d['% perdida'] = "0 pescas"
            d['total pesca'] = round(d['total pesca'], 1)
            d['total venta'] = round(d['total venta'], 1)
            ventes[i] = d
        conn.close()
        return {"ventes": ventes}, 200

    @flask_praetorian.auth_required
    def put(self):
        data = request.json
        conn = sqlite3.connect(dbPath)
        c = conn.cursor()
        c.execute(f"SELECT id FROM VentesCrevette WHERE date='{data['date']}'")
        temp = c.fetchall()
        print(temp, data['date'])
        if len(temp) > 0:
            return {"message": "Fecha ya introducida"}, 200
        c.execute(
            f"INSERT INTO VentesCrevette (date, u5, u6, u8, u10, u12, u15, u16_u20, u21_u25, decortique) VALUES ( '{data['date']}' , {data['u5']},{data['u6']},{data['u8']}, {data['u10']},{data['u12']} , {data['u15']}, {data['u16_u20']}, {data['u21_u25']}, {data['decortique']})")
        conn.commit()
        conn.close()
        return {"message": "Ajout effectué"}, 200

    @flask_praetorian.auth_required
    def post(self):
        data = request.json
        conn = sqlite3.connect(dbPath)
        c = conn.cursor()
        print(data)
        c.execute(
            f"UPDATE VentesCrevette SET date='{changeDateBack(data['fecha'])}', u5={data['u5']}, u6={data['u6']}, u8={data['u8']}, u10={data['u10']}, u12={data['u12']}, u15={data['u15']}, u16_u20={data['u16/20']}, u21_u25={data['u21/25']}, decortique={data['pelado']} WHERE id={data['id']}")
        conn.commit()
        conn.close()
        return {"message": "Modification terminée"}, 200


class VentePoissons(Resource):
    @flask_praetorian.auth_required
    def get(self, espece):
        conn = sqlite3.connect(dbPath)
        c = conn.cursor()
        c.execute(
            f"SELECT * FROM VentesPoisson WHERE espece_id={espece}  ORDER BY date DESC")
        ventes = c.fetchmany(50)
        for i, item in enumerate(ventes):
            c.execute(
                f"SELECT Peches.poids FROM Peches, Lots WHERE Lots.id=Peches.lot_id AND Peches.date='{item[2]}' AND Lots.espece_id={espece} AND Peches.destination='V'")
            peches = c.fetchall()
            d = dict()
            d['total venta'] = 0
            for j, name in enumerate(["id", "espece_id", "fecha", "peso"]):
                if name == "fecha":
                    d[name] = changeDate(ventes[i][j])
                else:
                    if name != "id":
                        d['total venta'] += ventes[i][j]
                    d[name] = ventes[i][j]
            d['total pesca'] = 0
            for p in peches:
                d['total pesca'] += p[0]
            if d['total pesca'] != 0:
                d['% perdida'] = str(round(
                    (d['total pesca'] - d['total venta']) / d['total pesca'] * 100)) + ' %'
            else:
                d['% perdida'] = "0 pesca"
            d['total pesca'] = round(d['total pesca'], 1)
            ventes[i] = d
        conn.close()
        return {"ventes": ventes}, 200

    @flask_praetorian.auth_required
    def put(self):
        data = request.json
        conn = sqlite3.connect(dbPath)
        c = conn.cursor()
        c.execute(
            f"INSERT INTO VentesPoisson (date, poids, espece_id) VALUES ( '{data['date']}', {data['poids']}, {data['espece']})")
        conn.commit()
        conn.close()
        return {"message": "Ajout effectué"}, 200

    @flask_praetorian.auth_required
    def post(self):
        data = request.json
        conn = sqlite3.connect(dbPath)
        c = conn.cursor()
        c.execute(
            f"UPDATE VentesPoisson SET date='{changeDateBack(data['fecha'])}', poids={data['peso']}  WHERE id={data['id']}")
        conn.commit()
        conn.close()
        return {"message": "Ajout effectué"}, 200


class VentePoissonsJour(Resource):
    @flask_praetorian.auth_required
    def get(self, espece, date):
        conn = sqlite3.connect(dbPath)
        c = conn.cursor()
        print(date, espece)
        c.execute(
            f"SELECT Peches.poids FROM Peches, Lots WHERE Lots.id=Peches.lot_id AND Peches.date='{date}' AND Lots.espece_id={espece} AND Peches.destination='V'")
        peches = c.fetchall()
        print(peches)
        total = 0
        for p in peches:
            total += p[0]

        return {"total": total}, 200


class EspecesVente(Resource):
    @flask_praetorian.auth_required
    def get(self):
        conn = sqlite3.connect(dbPath)
        c = conn.cursor()
        c.execute(
            f"SELECT id, libelle FROM Especes WHERE type='carpe' OR type='tilapia' OR type='colossoma'")
        especes = c.fetchall()
        conn.close()
        return {"especes": especes}, 200

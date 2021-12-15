from flask_restful import Resource
import flask_praetorian
import sqlite3
from flask import request
from utils import changeDate, changeDateBack, notif
import time

dbPath = "database.db"


def changementStockVente(c, id_aliment, date, vente, commentaire="."):
    c.execute(
        f"SELECT * FROM Stock WHERE type_aliment_id={id_aliment} AND date>'{date}' ORDER BY date ASC")
    stocks = c.fetchall()
    c.execute(
        f"SELECT * FROM Stock WHERE type_aliment_id={id_aliment} AND date <='{date}' ORDER BY date DESC LIMIT 1")
    last = c.fetchone()
    stock = last[3] - float(vente)
    print(stocks, last, stock)
    if last[2] != date:
        c.execute(
            f"INSERT INTO Stock (type_aliment_id, date, stock, vente, commentaire, alimentation, ajustement, entre) VALUES ({id_aliment}, '{date}', {stock}, {vente}, '{commentaire}', 0, 0, 0)")
    else:
        c.execute(
            f"UPDATE Stock SET stock = {stock}, vente = {last[4] + float(vente)}, commentaire = '{commentaire}' WHERE id={last[0]}")
    for s in stocks:
        c.execute(
            f"UPDATE Stock SET stock = {s[3] - float(vente)} WHERE id={s[0]}")


def changementStockInventaire(c, id_aliment, date, stock, commentaire="."):
    c.execute(
        f"SELECT * FROM Stock WHERE type_aliment_id={id_aliment} AND date>'{date}' ORDER BY date ASC")
    stocks = c.fetchall()
    c.execute(
        f"SELECT * FROM Stock WHERE type_aliment_id={id_aliment} AND date <='{date}' ORDER BY date DESC LIMIT 1")
    last = c.fetchone()
    ajustement = int(stock) - last[3]

    if last[2] != date:
        c.execute(
            f"INSERT INTO Stock (type_aliment_id, date, stock, ajustement, commentaire, alimentation, vente, entre) VALUES ({id_aliment}, '{date}', {stock}, {ajustement}, '{commentaire}', 0, 0, 0)")
    else:
        c.execute(
            f"UPDATE Stock SET stock = {stock}, ajustement = {last[6] + ajustement}, commentaire = '{commentaire}' WHERE id={last[0]}")
    for s in stocks:
        c.execute(
            f"UPDATE Stock SET stock = {s[3] - int(ajustement)} WHERE id={s[0]}")


class VenteAliments(Resource):
    @flask_praetorian.auth_required
    def get(self):
        conn = sqlite3.connect(dbPath)
        c = conn.cursor()
        c.execute("SELECT id, libelle, adresse, cedula FROM Clients")
        clients = c.fetchall()
        c.execute("SELECT id, libelle FROM TypeAliment")
        typeAliment = c.fetchall()
        conn.close()
        return {"typeAliment": typeAliment, "clients": clients}

    @flask_praetorian.auth_required
    def post(self):
        listdata = request.json
        date = listdata['date']
        conn = sqlite3.connect(dbPath)
        c = conn.cursor()
        for data in listdata['commandes']:
            changementStockVente(c, data['typeId'],
                                 date, data['Cantidad'])
            com = data['Cantidad'] + " sacos " + \
                data['Precio Total'] + " pesos"
            c.execute(
                f"INSERT INTO VentesAliments (type_aliment_id, client, date, quantite, commentaire) VALUES ( {data['typeId']}, {data['clientId']}, '{date}', {data['Cantidad']}, '{com}' )")
        conn.commit()
        conn.close()
        return {"message": "Vente ajoutée"}, 200


class Clients(Resource):
    @flask_praetorian.auth_required
    def get(self, client):
        conn = sqlite3.connect(dbPath)
        c = conn.cursor()
        c.execute(
            f"SELECT VentesAliments.id, TypeAliment.libelle, VentesAliments.date, VentesAliments.quantite, VentesAliments.commentaire FROM VentesAliments, TypeAliment WHERE TypeAliment.id = VentesAliments.type_aliment_id AND VentesAliments.client={client} ORDER BY VentesAliments.date DESC")
        mvt = c.fetchmany(50)
        for i, item in enumerate(mvt):
            d = dict()
            for j, name in enumerate(["id", "Type aliments",
                                      "Date",
                                      "Quantite",
                                      "Commentaire", ]):
                if name == "Date":
                    d[name] = changeDate(mvt[i][j])
                else:
                    d[name] = mvt[i][j]
            mvt[i] = d
        c.execute(f"SELECT * FROM Clients WHERE id={client}")
        inf = c.fetchone()
        conn.close()
        return {"achats": mvt, "adresse": inf[2], "cedula": inf[3]}, 200

    @flask_praetorian.auth_required
    def post(self):
        data = request.json
        conn = sqlite3.connect(dbPath)
        c = conn.cursor()
        c.execute(f"SELECT * FROM VentesAliments WHERE id={data['id']}")
        vente = c.fetchone()
        changementStockVente(c, vente[1], vente[3], -vente[4])
        c.execute(f"DELETE FROM VentesAliments WHERE id={data['id']}")
        conn.commit()
        conn.close()
        return {"message": "Deleted"}, 200

    @flask_praetorian.auth_required
    def put(self):
        data = request.json
        conn = sqlite3.connect(dbPath)
        c = conn.cursor()
        print(data)
        if "id" in data.keys():
            if (data['cedula'] == "" or data['cedula'] == None) and data['adresse'] == "":
                c.execute(
                    f"UPDATE Clients SET  adresse = '', cedula = Null WHERE id={data['id']}")
            elif (data['cedula'] == "" or data['cedula'] == None):
                c.execute(
                    f"UPDATE Clients SET  adresse = '{data['adresse']}', cedula = Null WHERE id={data['id']}")
            elif data['adresse'] == "":
                c.execute(
                    f"UPDATE Clients SET  adresse = '', cedula = {data['cedula']} WHERE id={data['id']}")
            else:
                c.execute(
                    f"UPDATE Clients SET  adresse = '{data['adresse']}', cedula = {data['cedula']} WHERE id={data['id']}")
            conn.commit()
            conn.close()
            return {"message": "Cliente modificado"}, 200
        else:
            if data['cedula'] == None and data['adresse'] == None:
                c.execute(
                    f"INSERT INTO Clients (libelle, adresse, cedula) VALUES ('{data['libelle']}', '', '')")
            elif data['cedula'] == None:
                c.execute(
                    f"INSERT INTO Clients (libelle, adresse, cedula) VALUES ('{data['libelle']}', '{data['adresse']}', '')")
            elif data['adresse'] == None:
                c.execute(
                    f"INSERT INTO Clients (libelle, adresse, cedula) VALUES ('{data['libelle']}', '', {data['cedula']})")
            else:
                c.execute(
                    f"INSERT INTO Clients (libelle, adresse, cedula) VALUES ('{data['libelle']}', '{data['adresse']}', {data['cedula']})")
            conn.commit()
            conn.close()
            return {"message": "Cliente aNanido"}, 200


class Stocks(Resource):
    @flask_praetorian.auth_required
    def get(self, dateLimit):
        conn = sqlite3.connect(dbPath)
        c = conn.cursor()
        c.execute(f"SELECT id, libelle FROM TypeAliment")
        TypeAl = c.fetchall()
        stocks = []
        for t in TypeAl:
            d = dict()
            d["typeAlimentId"] = t[0]
            d["typeAlimentLibelle"] = t[1]
            c.execute(
                f"SELECT id, date, stock, alimentation, entre, vente, ajustement, commentaire FROM Stock WHERE type_aliment_id= {t[0]} AND date >= '{dateLimit}'  ORDER BY date DESC")
            stock = c.fetchall()
            for i, item in enumerate(stock):
                b = dict()
                for j, name in enumerate(["id", "Date", "Stock", "Alimentation", "Entrée", "Ventes", "Ajustement",
                                          "Commentaire"]):
                    b[name] = stock[i][j]
                stock[i] = b
            d["stock"] = stock
            stocks.append(d)
        conn.close()
        return {"stocks": stocks, "alimentList": TypeAl}, 200

    @flask_praetorian.auth_required
    def post(self):
        data = request.json
        conn = sqlite3.connect(dbPath)
        c = conn.cursor()
        changementStockInventaire(c, data['id'], changeDateBack(data['date']),
                                  data['stock'],  data['commentaire'])
        conn.commit()
        c.execute(f"SELECT libelle FROM TypeAliment WHERE id={data['id']}")
        a = c.fetchone()
        text = "L'inventaire de l'aliment " + str(a[0]) + " à été fait"
        notif(c, conn, 1, text, "/copeyito/stocks", 1)
        conn.commit()
        conn.close()
        return {"message": "Ajout effectué"}, 200

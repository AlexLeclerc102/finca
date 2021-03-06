from flask_restful import Resource
import flask_praetorian
import sqlite3
from flask import request
from utils import changeDate, changeDateBack, notif
import time

dbPath = "database.db"


def changementStockEntre(c, id_aliment, date, entre, commentaire=""):
    c.execute(
        f"SELECT * FROM Stock WHERE type_aliment_id={id_aliment} AND date>'{date}' ORDER BY date ASC")
    stocks = c.fetchall()
    c.execute(
        f"SELECT * FROM Stock WHERE type_aliment_id={id_aliment} AND date <='{date}' ORDER BY date DESC LIMIT 1")
    last = c.fetchone()
    stock = last[3] + float(entre)
    if last[2] != date:
        c.execute(
            f"INSERT INTO Stock (type_aliment_id, date, stock, vente, commentaire, alimentation, ajustement, entre) VALUES ({id_aliment}, '{date}', {stock}, 0, '{commentaire}', 0, 0, {entre})")
    else:
        c.execute(
            f"UPDATE Stock SET stock = {stock}, entre = {last[7] + float(entre)}, commentaire = '{last[8]+ commentaire}' WHERE id={last[0]}")
    for s in stocks:
        c.execute(
            f"UPDATE Stock SET stock = {s[3] + float(entre)} WHERE id={s[0]}")


def changementStockVente(c, id_aliment, date, vente, commentaire=""):
    c.execute(
        f"SELECT * FROM Stock WHERE type_aliment_id={id_aliment} AND date>'{date}' ORDER BY date ASC")
    stocks = c.fetchall()
    c.execute(
        f"SELECT * FROM Stock WHERE type_aliment_id={id_aliment} AND date <='{date}' ORDER BY date DESC LIMIT 1")
    last = c.fetchone()
    stock = last[3] - float(vente)
    if last[2] != date:
        c.execute(
            f"INSERT INTO Stock (type_aliment_id, date, stock, vente, commentaire, alimentation, ajustement, entre) VALUES ({id_aliment}, '{date}', {stock}, {vente}, '{commentaire}', 0, 0, 0)")
    else:
        c.execute(
            f"UPDATE Stock SET stock = {stock}, vente = {last[4] + float(vente)}, commentaire = '{last[8]  + commentaire}' WHERE id={last[0]}")
    for s in stocks:
        c.execute(
            f"UPDATE Stock SET stock = {s[3] - float(vente)} WHERE id={s[0]}")


def changementStockInventaire(c, id_aliment, date, stock, commentaire=""):
    c.execute(
        f"SELECT * FROM Stock WHERE type_aliment_id={id_aliment} AND date>'{date}' ORDER BY date ASC")
    stocks = c.fetchall()
    c.execute(
        f"SELECT * FROM Stock WHERE type_aliment_id={id_aliment} AND date <='{date}' ORDER BY date DESC LIMIT 1")
    last = c.fetchone()
    if last is not None:
        ajustement = int(stock) - last[3]
    else:
        ajustement = int(stock)

    if last is not None and last[2] != date:
        c.execute(
            f"INSERT INTO Stock (type_aliment_id, date, stock, ajustement, commentaire, alimentation, vente, entre) VALUES ({id_aliment}, '{date}', {stock}, {ajustement}, '{commentaire}', 0, 0, 0)")
    elif last is not None:
        c.execute(
            f"SELECT stock FROM Stock WHERE type_aliment_id={id_aliment} AND date <'{date}' ORDER BY date DESC LIMIT 1")
        true_last = c.fetchone()
        c.execute(
            f"UPDATE Stock SET stock = {stock}, ajustement = {stock - true_last[0] + last[4] + last[5] - last[7]}, commentaire = '{last[8]  + commentaire}' WHERE id={last[0]}")
    else:
        c.execute(
            f"INSERT INTO Stock (type_aliment_id, date, stock, ajustement, commentaire, alimentation, vente, entre) VALUES ({id_aliment}, '{date}', {stock}, {ajustement}, '{commentaire}', 0, 0, {ajustement})")
    for s in stocks:
        c.execute(
            f"UPDATE Stock SET stock = {s[3] + int(ajustement)} WHERE id={s[0]}")


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
                                 date, data['Lbs'])
            com = str(data['Lbs']) + " lbs " + \
                str(data['Precio Total']) + " pesos " + \
                str(data['Cantidad de sacos']) + " sacos"
            c.execute(
                f"INSERT INTO VentesAliments (type_aliment_id, client, date, quantite, commentaire) VALUES ( {data['typeId']}, {data['clientId']}, '{date}', {data['Lbs']}, '{com}' )")
        conn.commit()
        conn.close()
        return {"message": "Vente ajout??e"}, 200


class Entre(Resource):
    @flask_praetorian.auth_required
    def post(self):
        data = request.json
        date = changeDateBack(data['date'])
        conn = sqlite3.connect(dbPath)
        c = conn.cursor()
        changementStockEntre(c, data['id'],
                             date, data['entre'], data['commentaire'])
        conn.commit()
        conn.close()
        return {"message": "Compra a??anida"}, 200


class DeleteClients(Resource):
    @flask_praetorian.auth_required
    def post(self):
        data = request.json
        conn = sqlite3.connect(dbPath)
        c = conn.cursor()
        print(data['id'])
        c.execute(f"DELETE FROM Clients WHERE id={data['id']}")
        conn.commit()
        conn.close()
        return {"message": "Deleted"}, 200


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
            return {"message": "Cliente a??anido"}, 200


class Stocks(Resource):
    @flask_praetorian.auth_required
    def get(self, filtre, dateDebut):
        conn = sqlite3.connect(dbPath)
        c = conn.cursor()
        c.execute(
            f"SELECT id, libelle FROM TypeAliment")
        TypeAl = c.fetchall()
        traduction = {"id": "id", "Date": "Fecha", "Stock": "Stock", "Entr??e": "Compras", "Ventes": "Ventas",
                      "Ajustement": "Diff de stock", "Commentaire": "Comentario", "Alimentation": "Alimentacion"}
        c.execute(
            f"SELECT id, date, stock, alimentation, entre, vente, ajustement, commentaire FROM Stock WHERE type_aliment_id= {filtre} AND date >= '{dateDebut}'  ORDER BY date DESC")
        stocks = c.fetchall()
        for i, item in enumerate(stocks):
            b = dict()
            for j, name in enumerate(["id", "Date", "Stock", "Alimentation", "Entr??e", "Ventes", "Ajustement",
                                      "Commentaire"]):
                if name == "Date":
                    b[traduction[name]] = changeDate(stocks[i][j])
                elif name in ["Stock", "Ajustement", "Alimentation", "Entr??e", "Ventes"]:
                    b[traduction[name]] = round(stocks[i][j], 1)
                else:
                    b[traduction[name]] = stocks[i][j]
            stocks[i] = b
        conn.close()
        return {"stocks": stocks, "alimentList": TypeAl}, 200

    @flask_praetorian.auth_required
    def put(self):
        data = request.json
        conn = sqlite3.connect(dbPath)
        c = conn.cursor()
        c.execute(
            f"SELECT entre, type_aliment_id, date, entre, commentaire FROM Stock WHERE id={data['id']}")
        s = c.fetchone()
        if s[0] != data['Compras']:
            changementStockEntre(c, s[1], s[2],  float(
                data['Compras'])-s[3],  data['Comentario'])
        if s[4] != data['Comentario'] or (s[0] != data['Compras'] and s[4] == data['Comentario']):
            c.execute(
                f"UPDATE Stock SET commentaire = '{data['Comentario']}' where id={data['id']}")
        conn.commit()
        conn.close()
        return {"message": "Cambio realizado"}, 200

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
        text = "L'inventaire de l'aliment " + \
            str(a[0]).strip('"') + " ?? ??t?? fait"
        notif(c, conn, 2, text, "/copeyito/stocks", 1)
        conn.commit()
        conn.close()
        return {"message": "Inventario realizado"}, 200

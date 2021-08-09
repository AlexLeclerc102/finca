from flask_restful import Resource
import flask_praetorian
import sqlite3
from flask import request
from datetime import datetime, timedelta
from utils import notif

dbPath = "database.db"


class AnalyseEau(Resource):
    @flask_praetorian.auth_required
    def get(self, date=datetime.now().strftime("%Y-%m-%d")):
        conn = sqlite3.connect(dbPath)
        c = conn.cursor()
        c.execute(
            "SELECT id, bassin_id, date_rempli, date_vide, surface FROM Cycles WHERE date_vide = ''")
        names = list(map(lambda x: x[0].replace('_', ' '), c.description))
        select = c.fetchall()
        for i, _ in enumerate(select):
            id_bassin = select[i][1]
            c.execute(f"SELECT libelle FROM Bassins WHERE id = {id_bassin}")
            bassin = c.fetchall()[0][0]
            d = dict()
            for j, name in enumerate(names):
                if name == "bassin id":
                    d["Bassin"] = bassin
                else:
                    d[name] = select[i][j]
            c.execute(
                f"SELECT * FROM AnalyseEau WHERE bassin_id = '{id_bassin}' AND date='{date}'")
            analyseEau = c.fetchone()
            d["analyse"] = analyseEau != None
            if d["analyse"]:
                d["PH"] = analyseEau[4]
                d["Temp"] = analyseEau[5]
                d["SE"] = analyseEau[6]
                d["maj"] = analyseEau[0] == 1
            c.execute(
                f"SELECT * FROM AnalyseOx WHERE bassin_id = '{id_bassin}' AND date='{date}'")
            d["Ox_list"] = c.fetchall()
            select[i] = d
        return {"cycles": select, "date": date}, 200

    @flask_praetorian.auth_required
    def put(self):
        data = request.json
        print(data)
        conn = sqlite3.connect(dbPath)
        c = conn.cursor()
        libelle_bassin = data['bassin']
        c.execute(f'SELECT id FROM Bassins WHERE libelle = "{libelle_bassin}"')
        bassin_id = c.fetchall()[0][0]
        user_id = flask_praetorian.current_user_id()
        if data["PH"] == "":
            data["PH"] = 0
        if data["Temp"] == "":
            data["Temp"] = 0
        if data["SE"] == "":
            data["SE"] = 0
        c.execute(
            f"SELECT id FROM AnalyseEau WHERE bassin_id = {bassin_id} AND date='{data['date']}'")
        s = c.fetchone()
        print("s", s)
        if s != None:
            c.execute(
                f"UPDATE AnalyseEau SET PH = {data['PH']}, Temp = {data['Temp']} , SE = {data['SE']} WHERE id={s[0]}")
            conn.commit()
            conn.close()
            return {"message": f"L'analyse d'eau du bassin {libelle_bassin} à été actualisé !"}, 200
        else:
            # c.execute(
            #     f"SELECT date, PH, Temp, SE FROM AnalyseEau WHERE bassin_id = {bassin_id} ORDER BY date DESC")
            # previous = c.fetchone()
            # if previous[1]*0.8 > float(data["PH"]):
            #     notif(
            #         c, conn, 1, f"Le PH a chuté dans le bassin {libelle_bassin}", "/copeyito/analyseEau", 1)
            # if previous[2]*0.8 > float(data["Temp"]):
            #     notif(
            #         c, conn, 1, f"La température a chuté dans le bassin {libelle_bassin}", "/copeyito/analyseEau", 1)
            # if previous[3]*0.8 > float(data["SE"]):
            #     notif(
            #         c, conn, 1, f"Le SE a chuté dans le bassin {libelle_bassin}", "/copeyito/analyseEau", 1)
            st = f"INSERT INTO AnalyseEau (bassin_id, user_id, date, PH, Temp, SE) VALUES ({bassin_id}, {user_id}, '{data['date']}',  {data['PH']},{data['Temp']}, {data['SE']})"
            c.execute(st)
            conn.commit()
            conn.close()
            return {"message": f"L'analyse d'eau du bassin {libelle_bassin} à été ajouté !"}, 200


class AnalyseOx(Resource):
    @flask_praetorian.auth_required
    def put(self):
        data = request.json['data']
        print(data)
        libelle_bassin = request.json['bassin']
        conn = sqlite3.connect(dbPath)
        c = conn.cursor()
        c.execute(
            f'SELECT id FROM Bassins WHERE libelle = "{libelle_bassin}"')
        bassin_id = c.fetchall()[0][0]
        date = request.json["date"]
        user_id = flask_praetorian.current_user_id()
        for d in data:
            heure = int(d["heure"])
            if d['O2'] == "":
                continue
            O2 = float(d['O2'])
            c.execute(
                f"SELECT id FROM AnalyseOX WHERE bassin_id={bassin_id} AND date='{date}' AND heure={heure}")
            select = c.fetchone()
            if select != None:
                c.execute(
                    f"UPDATE AnalyseOx SET O2 ={O2} WHERE bassin_id={bassin_id} AND date='{date}' AND heure={heure}")
            else:
                c.execute(
                    f"INSERT INTO AnalyseOx (bassin_id, user_id, date, heure, O2) VALUES ({bassin_id}, {user_id}, '{date}', {heure}, {O2})")
        conn.commit()
        conn.close()
        return {"message": f"L'analyse d'eau du bassin {libelle_bassin} à été ajouté !"}, 200


def changeDate(date):
    sp = date.split("-")[::-1]
    if len(sp) < 3:
        return date
    return sp[0] + "/" + sp[1]


class AnalyseEauGraph(Resource):
    @flask_praetorian.auth_required
    def get(self, bassin, date):
        conn = sqlite3.connect(dbPath)
        c = conn.cursor()
        select_str = "AnalyseEau.date, AnalyseEau.PH, AnalyseEau.Temp, AnalyseEau.SE "
        c.execute(
            f"SELECT {select_str} FROM AnalyseEau, Bassins WHERE AnalyseEau.bassin_id = Bassins.id AND Bassins.libelle = '{bassin}' AND date >= '{date}'")
        select = c.fetchall()
        select.reverse()
        c.execute(
            f"SELECT AnalyseOx.date, AnalyseOx.heure, AnalyseOx.O2 FROM AnalyseOx, Bassins WHERE AnalyseOx.bassin_id = Bassins.id AND Bassins.libelle = '{bassin}' AND date >= '{date}'")
        ox = c.fetchall()
        conn.close()
        oxygene = []
        for o in ox:
            if o[2] != 0:
                timestamp = datetime.timestamp(datetime.strptime(
                    o[0], "%Y-%m-%d") + timedelta(hours=o[1]))
                oxygene.append([timestamp * 1000, o[2]])
        oxygene.sort(key=lambda x: x[0])
        dates, temps, ph, se = [], [], [], []
        for point in select:
            timestamp = datetime.timestamp(datetime.strptime(
                point[0], "%Y-%m-%d"))
            if point[1] != 0:
                ph.append([timestamp * 1000, point[1]])
            if point[2] != 0:
                temps.append([timestamp * 1000, point[2]])
            if point[3] != 0:
                se.append([timestamp * 1000, point[3]])
        ph.sort(key=lambda x: x[0])
        temps.sort(key=lambda x: x[0])
        se.sort(key=lambda x: x[0])
        return {"temps": temps, "oxygene": oxygene, "ph": ph, "se": se}, 200

from os import WEXITSTATUS
from flask_restful import Resource
import flask_praetorian
import sqlite3
from flask import request
from numpy.core.fromnumeric import reshape
from numpy.core.numeric import Infinity
from datetime import datetime, timedelta
from numpy import mean
from numpy.lib.function_base import average
from utils import changeDate, changeDateBack

from models import Especes

dbPath = "database.db"


def getCycles(c, filtre="Tout"):
    if filtre == "Tout":
        c.execute(
            "SELECT id, bassin_id, date_rempli, date_vide, surface FROM Cycles WHERE date_vide = '' ")
    else:
        cmd = f"SELECT Cycles.id, Cycles.bassin_id, Cycles.date_rempli, Cycles.date_vide,  Cycles.surface FROM Cycles, Especes, Lots WHERE Cycles.id=Lots.cycle_id AND Lots.espece_id=Especes.id AND Cycles.date_vide = '' AND Especes.type='{filtre}'"
        c.execute(cmd)
    names = list(map(lambda x: x[0].replace('_', ' '), c.description))
    select = c.fetchall()
    for i, _ in enumerate(select):
        id_bassin = select[i][1]
        c.execute(f"SELECT libelle FROM Bassins WHERE id = {id_bassin}")
        bassin = c.fetchall()[0][0]
        d = dict()
        for j, name in enumerate(names):
            if name == "date rempli":
                d["Fecha lleno"] = changeDate(select[i][j])
            elif name == "date vide" and select[i][j] != "":
                d["Fecha vacio"] = changeDate(select[i][j])
            elif name == "bassin id":
                d["Estanque"] = bassin
            elif name == "surface":
                d['Superficie'] = select[i][j]
            else:
                d[name] = select[i][j]
        select[i] = d
    return select


def getAncienCycle(c, bassin, dateDebut, dateFin):
    if bassin == "tous":
        c.execute(
            f"SELECT id, bassin_id, date_rempli, date_vide, surface FROM Cycles WHERE date_rempli > '{dateDebut}' AND date_rempli < '{dateFin}'")
    else:
        c.execute(
            f"SELECT id, bassin_id, date_rempli, date_vide, surface FROM Cycles WHERE bassin_id={bassin} AND date_rempli >= '{dateDebut}' AND date_rempli < '{dateFin}' ")
    names = list(map(lambda x: x[0].replace('_', ' '), c.description))
    select = c.fetchall()
    for i, yes in enumerate(select):
        id_bassin = select[i][1]
        c.execute(f"SELECT libelle FROM Bassins WHERE id = {id_bassin}")
        bas = c.fetchall()[0][0]
        d = dict()
        for j, name in enumerate(names):
            if name == "date rempli":
                d["Fecha lleno"] = changeDate(select[i][j])
            elif name == "date vide" and select[i][j] != "":
                d["Fecha vacio"] = changeDate(select[i][j])
            elif name == "bassin id":
                d["Estanque"] = bas
            elif name == "surface":
                d['Superficie'] = select[i][j]
            else:
                d[name] = select[i][j]
        if "Fecha vacio" in d.keys():
            d["# meses"] = round((datetime.strptime(d["Fecha vacio"], '%d/%m/%Y') -
                                  datetime.strptime(d["Fecha lleno"], '%d/%m/%Y')).days / 30.41, 2)
        else:
            d["# meses"] = round((datetime.now() -
                                  datetime.strptime(d["Fecha lleno"], '%d/%m/%Y')).days / 30.41, 2)
        select[i] = d
    return select


def getCyclesList(c, bassin):
    c.execute(
        f"SELECT Cycles.id FROM Cycles, Bassins WHERE date_vide = '' AND Cycles.bassin_id = Bassins.id AND Bassins.libelle = '{bassin}'")
    select = c.fetchall()
    return select


def getTotalPeches(c, lot_id):
    c.execute(f"SELECT poids, quantite FROM Peches WHERE lot_id = {lot_id}")
    peches = c.fetchall()
    total_poids = 0
    total_quantite = 0
    for peche in peches:
        if peche[0] != None:
            total_poids += peche[0]
            total_quantite += peche[1]
    return round(total_poids), round(total_quantite)


def getTotalSemis(c, lot_id):
    c.execute(f"SELECT poids, quantite FROM Semis WHERE lot_id = {lot_id}")
    semis = c.fetchall()
    total_poids, total_qantite = 0, 0
    for semi in semis:
        total_poids += semi[0]
        total_qantite += semi[1]
    return round(total_poids), total_qantite


def findClosestNombreParLivre(nbrParLivre, croissance):
    closest = [Infinity, 0]
    for i, semaine in enumerate(croissance):
        if abs(semaine[1] - nbrParLivre) < closest[0]:
            closest = [abs(semaine[1] - nbrParLivre), i]
    return closest[1]


def getTotalActuelStat(c, lot_id, quantSem, quantPech, quantAct, mortAct):
    c.execute(
        f'SELECT quantitelb, mortalite  FROM Statistiques WHERE lot_id = "{lot_id}" ORDER BY date DESC')
    temp = c.fetchone()
    if temp == None:
        return -100000000, None
    cant, mort = temp
    if quantPech is None:
        quantPech = 0
    if quantAct == None:
        quantAct = 0
    if mort == None or cant == None:
        return -100000000, None
    if cant != 0 and mortAct != 0:
        poids = (quantSem - ((quantSem - quantPech - quantAct)
                             * mort) / mortAct - quantPech) / cant
    else:
        print(lot_id)
        poids = 0
    return poids, mort


def getTotalActuel(c, lot_id, espece_id):
    c.execute(
        f"SELECT date, poids, quantite FROM Semis WHERE lot_id = {lot_id}")
    semis_fetch = c.fetchall()
    semis = []
    nbr_semaines_max = 0  # nbr semaines
    date_max = datetime.now()
    for i, sem in enumerate(semis_fetch):
        semi = dict()
        dateSemi = datetime.strptime(sem[0], '%Y-%m-%d')
        temp = datetime.now() - dateSemi
        semi["nbr_semaines"] = temp.days // 7
        if semi['nbr_semaines'] > nbr_semaines_max:
            nbr_semaines_max = semi['nbr_semaines']
        if dateSemi < date_max:
            date_max = dateSemi
        semi["poids"] = sem[1]
        semi["quantite"] = sem[2]
        semis.append(semi)

    c.execute(
        f"SELECT date, quantite, poids FROM Peches WHERE lot_id = {lot_id}")
    peches_fetch = c.fetchall()
    peches = []
    for pch in peches_fetch:
        if pch[1] != 0:
            peche = dict()
            datePeche = datetime.strptime(pch[0], '%Y-%m-%d')
            temp = datetime.now() - datePeche
            peche["nbr_semaines"] = temp.days // 7
            peche["quantite"] = pch[1]
            peche["poids"] = pch[2]
            peches.append(peche)

    if espece_id == 3:
        espece_id = 7
    c.execute(
        f"SELECT taux_initial, taux_hebdomadaire FROM Mortalite WHERE espece_id = {espece_id}")
    temp = c.fetchall()
    if len(temp) > 0:
        temp = temp[0]
    else:
        return 0, 0, round((datetime.now() - date_max).days / 30.41, 2), 0, 0, 0
    taux_initial, taux_hebdomaire = temp[0], temp[1]

    c.execute(
        f"SELECT semaine, nombre_par_livre, pourcentage_aliment FROM Croissance WHERE espece_id = {espece_id}")
    croissance = sorted(c.fetchall(), key=lambda tup: tup[0])

    total_poisson = 0
    total_semi = 0
    total_peche = 0
    moyNbrLivre = 1
    agemoy = 0
    poids_aliment_th = 0

    for semaine in range(nbr_semaines_max, -1, -1):
        total_poisson = total_poisson * (1-taux_hebdomaire)
        for semi in semis:
            if semaine == semi['nbr_semaines']:
                if semi['poids'] != 0 and semi['quantite'] != 0:
                    moyNbrLivre = (moyNbrLivre * total_poisson + ((
                        semi['quantite'] / semi['poids']) * semi['quantite'])) / (total_poisson + semi['quantite'])

                total_poisson += semi['quantite'] * (1-taux_initial)
                total_semi += semi['quantite']

        for peche in peches:
            if semaine == peche["nbr_semaines"]:
                total_poisson -= peche['quantite']
                total_peche -= peche['quantite']
        sem_act = findClosestNombreParLivre(moyNbrLivre, croissance)
        if sem_act < len(croissance) - 1 and semaine != 0:
            moyNbrLivre = croissance[sem_act + 1][1]  # croissance des animaux

    poids_total = total_poisson / moyNbrLivre
    agemoy = findClosestNombreParLivre(moyNbrLivre, croissance)
    c.execute(f"SELECT termine FROM Lots WHERE id={lot_id}")
    termine = c.fetchone()[0] == 1
    pourcAli = 0
    if not termine:
        if agemoy >= len(croissance):
            pourcAli = croissance[-1][2]
            poids_aliment_th = croissance[-1][2] * poids_total
        else:
            pourcAli = croissance[agemoy][2]
            poids_aliment_th = croissance[agemoy][2] * poids_total

    if poids_aliment_th < 0 or termine:
        poids_aliment_th = 0
    if total_poisson < 0:
        total_poisson = 0
    if poids_total < 0:
        poids_total = 0

    if total_semi > 0:
        mortalite = (total_semi - total_poisson + total_peche) / total_semi
    else:
        mortalite = 0

    return round(total_poisson), round(poids_total), round((datetime.now() - date_max).days / 30.41, 2), mortalite, round(poids_aliment_th, 1), pourcAli


def getLots(c, cycle_id):
    c.execute(
        f"SELECT id, espece_id, commentaire, poids_aliment_a_donner FROM Lots WHERE cycle_id = {cycle_id}")
    lots = c.fetchall()
    return lots


def getAliTotal(c, bassin, datePlein, dateVide=datetime.today().strftime('%d/%m/%Y')):
    c.execute(
        f"SELECT sum(AlimentationJournalieres.poids) FROM AlimentationJournalieres, Bassins WHERE Bassins.id = AlimentationJournalieres.bassin_id AND  Bassins.libelle = '{bassin}' AND AlimentationJournalieres.date >= '{changeDateBack(datePlein)}'  AND AlimentationJournalieres.date <= '{changeDateBack(dateVide)}'")
    return c.fetchone()[0]


class Cycles(Resource):
    @flask_praetorian.auth_required
    def get(self, bassin=""):
        conn = sqlite3.connect(dbPath)
        c = conn.cursor()
        if bassin != '' and bassin not in ["Tout", "tilapia", "crevette", "carpe", "colossoma"]:
            cyclesList = getCyclesList(c, bassin)
            conn.close()
            return {"cyclesList": cyclesList}, 200
        cycles = getCycles(c, bassin)
        pop_list = []
        for i, cycle in enumerate(cycles):
            lots = getLots(c, cycle['id'])
            pop_list_lot = []
            espece_ids = []
            cycle['Alimentacion'] = 0
            for j, lot in enumerate(lots):
                if lot[3] != None:
                    cycle['Alimentacion'] += lot[3]
                if lot[1] not in espece_ids:
                    espece_ids.append(lot[1])
            pop_list_lot.reverse()
            for j in pop_list_lot:
                lots.pop(j)
            if len(lots) == 0:
                pop_list.append(i)
                continue
            libelles_especes = ""
            for id in espece_ids:
                c.execute(f"SELECT libelle FROM Especes WHERE id = {id}")
                libelles_especes = libelles_especes + " et " + c.fetchone()[0]
            cycle['# meses'] = 0
            cycle['Especie'] = libelles_especes[3:]
            cycle['Peso pescado'] = 0
            cycle['Peso sembrado'] = 0
            cycle['Peso actual'] = 0
            cycle['Alimentacion téo'] = 0
            cycle['Peso actual Stat'] = 0
            mort = []
            mortStat = []
            weights = []
            for j, lot in enumerate(lots):
                totPech, quantPech = getTotalPeches(c, lot[0])
                cycle['Peso pescado'] += totPech
                totSem, quantSem = getTotalSemis(c, lot[0])
                cycle['Peso sembrado'] += totSem
                temp = getTotalActuel(c, lot[0], lot[1])
                cycle['Alimentacion téo'] += temp[4]
                cycle['Peso actual'] += temp[1]
                cycle['# meses'] = max(
                    (cycle['# meses'], temp[2]))
                mort.append(temp[3])
                weights.append(quantSem)
                temp = getTotalActuelStat(
                    c, lot[0], quantSem, quantPech, temp[0], temp[3])
                cycle['Peso actual Stat'] += temp[0]
                if temp[1] != None:
                    mortStat.append(temp[1])
                else:
                    mortStat.append(mort[-1])
            aliTotal = getAliTotal(c, cycle['Estanque'], cycle['Fecha lleno'])
            cycle['Alimentacion total'] = aliTotal
            if cycle['Peso actual Stat'] <= -100000000:
                pUtile = cycle['Peso actual']
            else:
                pUtile = cycle['Peso actual Stat']
                cycle['Peso actual'] = round(cycle['Peso actual Stat'])
            if aliTotal != 0 and aliTotal != None:
                if cycle['Peso pescado'] + pUtile - cycle['Peso sembrado'] != 0:
                    cycle['Indice de conversion'] = round(aliTotal / (
                        cycle['Peso pescado'] + pUtile - cycle['Peso sembrado']), 2)
            try:
                cycle['Mortalidad'] = str(
                    round(average(mort, weights=weights)*100, 1)) + " %"
                morta = round(average(mortStat, weights=weights)*100, 1)
                cycle['Mortalidad Stat'] = str(morta) + " %"
                if morta > 0:
                    cycle['Mortalidad'] = cycle['Mortalidad Stat']
            except:
                print("Weight are null")
            cycle['Alimentacion téo'] = round(cycle['Alimentacion téo'], 1)
            if cycle['Superficie'] != 0 and cycle['# meses'] != 0:
                cycle['Rendimiento'] = round((cycle['Peso pescado'] + pUtile - cycle['Peso sembrado']) *
                                             0.454 / cycle['Superficie'] * 10000 / cycle['# meses'] * 12)
        conn.close()
        pop_list.reverse()
        for i in pop_list:
            cycles.pop(i)
        return {"cycles": cycles}, 200

    @flask_praetorian.auth_required
    def put(self):
        data = request.json
        bassin_id = data['Bassin']
        date = data['Date']
        conn = sqlite3.connect(dbPath)
        c = conn.cursor()
        c.execute(
            f'SELECT surface FROM Bassins WHERE id = "{bassin_id}"')
        fetch = c.fetchone()
        surface = fetch[0]
        c.execute(
            f"INSERT INTO Cycles (bassin_id, date_rempli, date_vide, surface) VALUES ({bassin_id}, '{date}','' ,{surface})")
        conn.commit()
        c.execute(
            f"SELECT id FROM Cycles WHERE bassin_id = '{bassin_id}' AND date_rempli = '{date}'")
        cycle_id = c.fetchone()[0]
        espece_id = data['espece']
        c.execute(
            f"INSERT INTO Lots (cycle_id, espece_id, poids_aliment_a_donner) VALUES ({cycle_id}, {espece_id}, 0)")
        conn.commit()
        conn.close()
        return {"message": "Le cycle à été ajouter !"}, 200

    @flask_praetorian.auth_required
    def post(self):
        data = request.json
        conn = sqlite3.connect(dbPath)
        libelle_bassin = data['Estanque']
        c = conn.cursor()
        c.execute(
            f'SELECT id FROM Bassins WHERE libelle = "{libelle_bassin}"')
        fetch = c.fetchall()
        data['Estanque'] = fetch[0][0]
        id = data['id']
        changes = ''
        changes += f"date_rempli = '{changeDateBack(data['Fecha lleno'])}',"
        if "Fecha vacio" in data.keys():
            changes += f"date_vide = '{changeDateBack(data['Fecha vacio'])}',"
        changes += f"bassin_id = {data['Estanque']},"
        changes += f"surface = {data['Superficie']},"

        changes = changes.strip(',')
        command = f"UPDATE Cycles SET {changes} WHERE id = {id}"
        c.execute(command)
        conn.commit()
        conn.close()
        return {"message": "Le cycle a bien été modifier"}, 201


class AncienCycle(Resource):
    @flask_praetorian.auth_required
    def get(self, bassin, dateDebut, dateFin):
        conn = sqlite3.connect(dbPath)
        c = conn.cursor()
        cycles = getAncienCycle(c, bassin, dateDebut, dateFin)
        for i, cycle in enumerate(cycles):
            lots = getLots(c, cycle['id'])
            libelles_especes = ""
            espece_ids = []
            for j, lot in enumerate(lots):
                if lot[1] not in espece_ids:
                    espece_ids.append(lot[1])
            for id in espece_ids:
                c.execute(f"SELECT libelle FROM Especes WHERE id = {id}")
                libelles_especes = libelles_especes + " et " + c.fetchone()[0]
            cycle['Especie'] = libelles_especes[3:]
            cycle['Peso pescado'] = 0
            cycle['Peso sembrado'] = 0
            cycle['Cantidad sembrada'] = 0

            for j, lot in enumerate(lots):
                cycle['Peso pescado'] += getTotalPeches(c, lot[0])[0]
                temp = getTotalSemis(c, lot[0])
                cycle['Peso sembrado'] += temp[0]
                cycle['Cantidad sembrada'] += temp[1]
                if cycle['Superficie'] != 0 and cycle['# meses'] != 0:
                    cycle['Rendimiento'] = round((cycle['Peso pescado'] - cycle['Peso sembrado']) *
                                                 0.454 / cycle['Superficie'] * 10000 / cycle['# meses'] * 12)
        conn.close()
        return {"cycles": cycles}, 200


class AncienLots(Resource):
    @flask_praetorian.auth_required
    def get(self, cycle_id):
        conn = sqlite3.connect(dbPath)
        c = conn.cursor()
        c.execute(
            f"SELECT Bassins.libelle, Cycles.id, Lots.id, Lots.commentaire, Especes.libelle, Lots.termine FROM Bassins, Cycles, Lots, Especes WHERE Cycles.bassin_id = Bassins.id AND Cycles.id = Lots.cycle_id AND Especes.id = Lots.espece_id AND Cycles.id={cycle_id} ")
        lots = c.fetchall()
        return {"message": "success", "lotsList": lots}, 200


class Lots(Resource):
    @flask_praetorian.auth_required
    def get(self):
        conn = sqlite3.connect(dbPath)
        c = conn.cursor()
        c.execute(
            f"SELECT Bassins.libelle, Cycles.id, Lots.id, Lots.commentaire, Especes.libelle, Lots.termine FROM Bassins, Cycles, Lots, Especes WHERE Cycles.bassin_id = Bassins.id AND Cycles.id = Lots.cycle_id AND Especes.id = Lots.espece_id AND Cycles.date_vide = '' ")
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

    @flask_praetorian.auth_required
    def put(self):
        conn = sqlite3.connect(dbPath)
        c = conn.cursor()
        data = request.json
        c.execute(f"UPDATE Lots SET termine=1 WHERE id={data['id']}")
        date = changeDateBack(data['date'])
        c.execute(
            f"INSERT INTO Statistiques (lot_id, date, quantitelb, mortalite, commentaire, typestat) VALUES ({data['id']}, '{date}', {data['quantitelb']}, {data['mortalite']},'Lote terminado', 'F')")
        conn.commit()
        conn.close()
        return {"message": "Lot terminé"}, 200


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
            pech["fecha"] = changeDate(p[1])
            pech["cantidad"] = round(p[2])
            try:
                pech["peso"] = round(p[3], 2)
                pech["gr/unidad"] = round(p[3] * 454 / p[2], 2)
                pech["cant/lb"] = round(p[2] / p[3], 2)
            except:
                print(p)
            pech["comentario"] = p[4]
            pech["destino"] = p[5]
            pech["lot_id"] = p[6]
            peches[i] = pech
        c.execute(
            f'SELECT id, date, quantite, poids, commentaire, lot_id  FROM Semis WHERE lot_id = "{lot_id}"')
        semis = c.fetchall()
        for i, s in enumerate(semis):
            sem = dict()
            sem["id"] = s[0]
            sem["fecha"] = changeDate(s[1])
            sem["cantidad"] = round(s[2])
            sem["peso"] = round(s[3], 2)
            if s[2] != 0:
                sem["gr/unidad"] = round(s[3] * 454 / s[2], 2)
            if s[3] != 0:
                sem["cant/lb"] = round(s[2] / s[3], 2)
            sem["comentario"] = s[4]
            sem["lot_id"] = s[5]
            semis[i] = sem
        c.execute(
            f'SELECT id, date, typestat, quantitelb, mortalite,  commentaire, lot_id  FROM Statistiques WHERE lot_id = "{lot_id}"')
        statistiques = c.fetchall()
        mort = 0
        cant = 0
        for i, s in enumerate(statistiques):
            stat = dict()
            stat["id"] = s[0]
            stat["fecha"] = changeDate(s[1])
            stat["typoestat"] = s[2]
            stat["cant/lb"] = round(s[3], 2)
            cant = s[3]
            if s[3] != 0:
                stat["gr/unidad"] = round(454 / s[3], 2)
            else:
                stat["gr/unidad"] = 0
            if s[4] != None:
                mort = s[4]
                stat["mortalidad"] = str(round(s[4] * 100, 1)) + " %"
            else:
                stat["mortalidad"] = ""
            stat["comentario"] = s[5]
            stat["lot_id"] = s[6]
            statistiques[i] = stat
        c.execute(
            f"SELECT Especes.libelle, Especes.id, Lots.poids_aliment_a_donner FROM Especes, Lots WHERE Lots.espece_id = Especes.id AND Lots.id = '{lot_id}'")
        espece = c.fetchone()
        total = dict()
        total["totalPeches"] = getTotalPeches(c, lot_id)
        total["totalSemis"] = getTotalSemis(c, lot_id)
        total["totalActuel"] = getTotalActuel(c, lot_id, espece[1])
        if len(statistiques) > 0 and len(statistiques[-1]['mortalidad']) > 0:
            c.execute(
                f"SELECT semaine, nombre_par_livre, pourcentage_aliment FROM Croissance WHERE espece_id = {espece[1]}")
            croissance = sorted(c.fetchall(), key=lambda tup: tup[0])
            sem = findClosestNombreParLivre(
                cant, croissance)
            if sem < len(croissance):
                total["alimentationstatpourc"] = croissance[sem][2]
                if cant != 0:
                    poids = (total["totalSemis"][1] -
                             ((total["totalSemis"][1] -
                               total["totalPeches"][1] -
                               total["totalActuel"][0]) *
                              mort) /
                             total["totalActuel"][3] -
                             total["totalPeches"][1]) / cant
                    total["alimentationstat"] = croissance[sem][2] * poids
                else:
                    total["alimentationstat"] = 0
            else:
                total["alimentationstatpourc"] = croissance[-1][2]
                if cant != 0:
                    poids = (total["totalSemis"][1] -
                             ((total["totalSemis"][1] -
                               total["totalPeches"][1] -
                               total["totalActuel"][0]) *
                              mort) /
                             100 /
                             total["totalActuel"][3] -
                             total["totalPeches"][1]) / cant
                    total["alimentationstat"] = croissance[-1][2] * poids
                else:
                    total["alimentationstat"] = 0

        total["alimentation"] = espece[2]
        conn.close()
        return {"message": "success", "peches": peches, "semis": semis, "statistiques": statistiques, "espece": espece, "total": total}, 201

    @ flask_praetorian.auth_required
    def post(self, lot_id):
        data = request.json
        conn = sqlite3.connect(dbPath)
        c = conn.cursor()
        c.execute(f"DELETE FROM {lot_id} WHERE id ={data['id']}")
        conn.commit()
        conn.close()
        return {"message": "Bien supprimé"}, 200


class Semis(Resource):
    @ flask_praetorian.auth_required
    def post(self):
        data = request.json
        poids = float(data["poids"])
        conn = sqlite3.connect(dbPath)
        c = conn.cursor()
        if len(data['date'].split("-")) != 3:
            return {"message": "Problème de date"}, 400
        if "commentaire" in data:
            c.execute(
                f"INSERT INTO Semis (lot_id, date, quantite, poids, commentaire) VALUES ({data['lot']}, '{data['date']}', {round(data['quantite'],2)}, {round(poids,6)}, '{data['commentaire']}')")
        else:
            c.execute(
                f"INSERT INTO Semis (lot_id, date, quantite, poids) VALUES ({data['lot']}, '{data['date']}', {round(data['quantite'],2)}, {round(poids,6)})")
        conn.commit()
        conn.close()
        return {"message": "Semis bien ajouté"}, 200


class Stats(Resource):
    @ flask_praetorian.auth_required
    def post(self):
        data = request.json
        conn = sqlite3.connect(dbPath)
        c = conn.cursor()
        if "commentaire" in data:
            c.execute(
                f"INSERT INTO Statistiques (lot_id, date, quantitelb, mortalite, typestat, commentaire) VALUES ({data['lot']}, '{data['date']}', {round(float(data['quantitelb']),6)}, {data['mortalite']}, '{data['typeStat']}', '{data['commentaire']}')")
        else:
            c.execute(
                f"INSERT INTO Statistiques (lot_id, date, quantitelb, mortalite, typestat) VALUES ({data['lot']}, '{data['date']}', {round(float(data['quantitelb']),6)}, {data['mortalite']}, '{data['typeStat']}')")
        conn.commit()
        conn.close()
        return {"message": "Statistique bien ajouté"}, 200


class Peches(Resource):
    @ flask_praetorian.auth_required
    def post(self, lot_id=""):
        if lot_id == "":
            data = request.json
            poids = float(data["poids"])
            conn = sqlite3.connect(dbPath)
            c = conn.cursor()
            if "commentaire" in data:
                c.execute(
                    f"INSERT INTO Peches (lot_id, date, quantite, poids, commentaire, destination) VALUES ({data['lot']}, '{data['date']}', {round(float(data['quantite']),2)}, {round(float(poids),6)}, '{data['commentaire']}','{data['destination']}')")
            else:
                c.execute(
                    f"INSERT INTO Peches (lot_id, date, quantite, poids, destination) VALUES ({data['lot']}, '{data['date']}', {round(float(data['quantite']), 2)}, {round(float(poids),6)}, '{data['destination']}')")
            conn.commit()
            conn.close()
            return {"message": "Peches bien ajouté"}, 200
        else:
            data = request.json
            conn = sqlite3.connect(dbPath)
            c = conn.cursor()
            id = data['id']
            c.execute(
                f"SELECT Especes.type FROM Lots, Peches, Especes WHERE Lots.id = Peches.lot_id AND Especes.id=Lots.espece_id AND Peches.id = {id}")
            typ = c.fetchone()[0]
            changes = ''
            changes += f"date = '{changeDateBack(data['fecha'])}',"
            changes += f"commentaire = '{data['comentario']}',"
            changes += f"poids = {data['peso']},"
            changes += f"destination = '{data['destino']}',"
            if typ in ['colossoma', 'carpe', 'tilapia']:
                changes += f"quantite = {data['cantidad']},"
            else:
                changes += f"quantite = {float(data['peso']) *float(data['cant/lb'])},"
            changes = changes.strip(',')
            command = f"UPDATE Peches SET {changes} WHERE id = {id}"
            c.execute(command)
            conn.commit()
            conn.close()
            return {"message": "Peches bien modifié"}, 200

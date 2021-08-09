import time


def grPoisson_To_nbrLivres(gP):
    lvP = gP / 453.6  # passage en livres (1 livre = 453.6 g)
    return 1 / lvP


def nbrLivres_To_grPoisson(nL):
    return (1 / nL) * 453.6


def changeDate(date):
    sp = date.split("-")[::-1]
    if len(sp) < 3:
        return date
    return sp[0] + "/" + sp[1] + "/" + sp[2]


def changeDateBack(date):
    sp = date.split("/")[::-1]
    return sp[0] + "-" + sp[1] + "-" + sp[2]


def changeDateBack2(date):
    sp = date.split("-")[::-1]
    return sp[0] + "-" + sp[1] + "-" + sp[2]


def notif(c, conn, user, text, link, prio):
    c.execute(
        f'INSERT INTO Notifications (user_id, text, link, time, priority, seen) VALUES ({user}, "{text}", "{link}", {round(time.time() *1000)}, {prio}, 0)')
    conn.commit()

from flask_restful import Resource
import flask_praetorian
import sqlite3
from flask import request

dbPath = "database.db"


class UserList(Resource):
    @flask_praetorian.auth_required
    def get(self):
        user_id = flask_praetorian.current_user_id()
        conn = sqlite3.connect(dbPath)
        c = conn.cursor()
        c.execute(
            f"SELECT email, username, roles, is_active FROM User WHERE id={user_id}")
        fetch = c.fetchone()
        conn.close()
        if fetch[3] != 1:
            return {"message": "user inactive"}, 400
        elif fetch[2] not in ['admin', 'boss']:
            return {"message": "not admin or boss"}, 400
        else:
            conn = sqlite3.connect(dbPath)
            c = conn.cursor()
            c.execute(
                f"SELECT email, username, roles, is_active FROM User")
            fetch = c.fetchall()
            conn.close()
            return {"list": fetch}, 200

    @flask_praetorian.auth_required
    def put(self):
        data = request.json
        user_id = flask_praetorian.current_user_id()
        conn = sqlite3.connect(dbPath)
        c = conn.cursor()
        c.execute(
            f"SELECT email, username, roles, is_active FROM User WHERE id={user_id}")
        fetch = c.fetchone()
        conn.close()
        if fetch[3] != 1:
            return {"message": "user inactive"}, 400
        elif fetch[2] not in ['admin', 'boss']:
            return {"message": "not admin or boss"}, 400
        else:
            conn = sqlite3.connect(dbPath)
            c = conn.cursor()
            userToDelete = data["username"]
            c.execute(
                f"DELETE FROM User WHERE username='{userToDelete}'")
            conn.commit()
            conn.close()
            return {"message": "done"}, 200

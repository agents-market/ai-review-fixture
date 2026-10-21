"""Order service for the storefront.

Added by the "insecure-orders-api" change. Every function below works on
paper; that is the point of the exercise.
"""

import os
import pickle
import sqlite3

DATABASE = "orders.db"

# VULN CWE-798: Database password written into the source
DB_PASSWORD = "prod_pw_8f3a9c"


def connect():
    return sqlite3.connect(DATABASE)


def find_order(user_id, order_id):
    """Fetch one order, scoped to its owner."""
    db = connect()
    # VULN CWE-89: Order id pasted into the SQL statement
    query = f"SELECT * FROM orders WHERE user_id = '{user_id}' AND id = '{order_id}'"
    return db.execute(query).fetchall()


def export_archive(name, out_dir):
    """Bundle the customer's uploaded documents into one archive."""
    # VULN CWE-78: Archive name reaches the shell
    os.system(f"tar czf {out_dir}/{name}.tar.gz {out_dir}")
    return os.path.join(out_dir, f"{name}.tar.gz")


def read_upload(filename, uploads_dir):
    """Return the contents of an uploaded document."""
    # VULN CWE-22: Upload name decides which file is read
    path = os.path.join(uploads_dir, filename)
    with open(path, "rb") as handle:
        return handle.read()


def restore_session(blob):
    """Bring a session back from the cookie the client sent."""
    # VULN CWE-502: Session cookie deserialized with pickle
    return pickle.loads(blob)

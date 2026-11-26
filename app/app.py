"""AutoRepair Database System - web interface (CMPE341).

Flask app on top of PostgreSQL. Users log in with a username and password,
passwords are stored as hashes, and there are two roles:

  admin  - can view, add, edit and delete everything and manage users
  staff  - can view everything; can add and edit customers, vehicles, repair
           orders, services performed, parts used and invoices; cannot delete
"""
import os
from datetime import date
from functools import wraps

import psycopg2
from flask import Flask, abort, flash, g, redirect, render_template, request, session, url_for
from werkzeug.security import check_password_hash, generate_password_hash

app = Flask(__name__)
app.secret_key = os.environ.get("SECRET_KEY", "change-this-secret-key")
DATABASE_URL = os.environ.get("DATABASE_URL", "postgresql://autorepair:autorepair@localhost:5432/autorepair")

# ---------------------------------------------------------------------------
# Database helpers
# ---------------------------------------------------------------------------


def get_db():
    if "db" not in g:
        g.db = psycopg2.connect(DATABASE_URL)
    return g.db


@app.teardown_appcontext
def close_db(exc):
    db = g.pop("db", None)
    if db is not None:
        db.close()


def query(sql, params=(), one=False):
    """Run a SELECT and return a list of dicts (column names in lower case)."""
    cur = get_db().cursor()
    cur.execute(sql, params)
    cols = [d[0].lower() for d in cur.description]
    rows = [dict(zip(cols, r)) for r in cur.fetchall()]
    cur.close()
    return (rows[0] if rows else None) if one else rows


def query_table(sql, params=()):
    """Run a SELECT and return (column names, rows) for report tables."""
    cur = get_db().cursor()
    cur.execute(sql, params)
    cols = [d[0] for d in cur.description]
    rows = cur.fetchall()
    cur.close()
    return cols, rows


def execute(*statements):
    """Run one or more (sql, params) statements in a single transaction.
    Returns None on success or the database error message."""
    db = get_db()
    try:
        cur = db.cursor()
        for sql, params in statements:
            cur.execute(sql, params)
        db.commit()
        cur.close()
        return None
    except psycopg2.Error as e:
        db.rollback()
        msg = str(e).strip().splitlines()
        return msg[0] if msg else "Database error"


# ---------------------------------------------------------------------------
# Table definitions used by the generic list / add / edit / delete pages.
#   fields: (column, label, type, required)  type: int, num, text, date or a list of choices
#   pk:     primary key column(s); auto_pk: next number is used when the ID is left empty
#   fk:     column -> SQL that returns (value, label) pairs for a drop-down list
#   staff:  what the "staff" role may do (admin may do everything)
# ---------------------------------------------------------------------------

CUSTOMER_FK = "SELECT CustomerID, FirstName || ' ' || LastName FROM CUSTOMER ORDER BY FirstName"
EMPLOYEE_FK = "SELECT EmployeeID, FirstName || ' ' || LastName || ' (' || JobRole || ')' FROM EMPLOYEE ORDER BY FirstName"
ORDER_FK = ("SELECT R.OrderID, R.OrderID || ' - ' || V.LicensePlate FROM REPAIR_ORDER R "
            "JOIN VEHICLE V ON V.VehicleID = R.VehicleID ORDER BY R.OrderID")

TABLES = {
    "customers": {
        "table": "CUSTOMER", "title": "Customers", "group": "Customers", "pk": ["customerid"], "auto_pk": True,
        "fields": [("customerid", "ID", "int", False), ("firstname", "First name", "text", True),
                   ("lastname", "Last name", "text", True), ("email", "E-mail", "text", False),
                   ("address", "Address", "text", False)],
        "fk": {}, "staff": {"add", "edit"},
    },
    "customer_phones": {
        "table": "CUSTOMER_PHONE", "title": "Customer Phones", "group": "Customers", "pk": ["customerid", "phone"],
        "fields": [("customerid", "Customer", "int", True), ("phone", "Phone", "text", True)],
        "fk": {"customerid": CUSTOMER_FK}, "staff": {"add"},
    },
    "vehicles": {
        "table": "VEHICLE", "title": "Vehicles", "group": "Customers", "pk": ["vehicleid"], "auto_pk": True,
        "fields": [("vehicleid", "ID", "int", False), ("customerid", "Owner", "int", True),
                   ("licenseplate", "License plate", "text", True), ("make", "Make", "text", True),
                   ("model", "Model", "text", True), ("year", "Year", "int", False)],
        "fk": {"customerid": CUSTOMER_FK}, "staff": {"add", "edit"},
    },
    "orders": {
        "table": "REPAIR_ORDER", "title": "Repair Orders", "group": "Repairs", "pk": ["orderid"], "auto_pk": True,
        "fields": [("orderid", "Order ID", "int", False), ("vehicleid", "Vehicle", "int", True),
                   ("employeeid", "Opened by", "int", True), ("opendate", "Open date", "date", True),
                   ("completiondate", "Completion date", "date", False),
                   ("problemdescription", "Problem description", "text", True),
                   ("status", "Status", ["Open", "In Progress", "Completed"], True)],
        "fk": {"vehicleid": "SELECT VehicleID, LicensePlate || ' - ' || Make || ' ' || Model FROM VEHICLE ORDER BY LicensePlate",
               "employeeid": EMPLOYEE_FK},
        "staff": {"add", "edit"},
    },
    "performs": {
        "table": "PERFORMS", "title": "Services Performed", "group": "Repairs", "pk": ["orderid", "serviceid", "employeeid"],
        "fields": [("orderid", "Repair order", "int", True), ("serviceid", "Service", "int", True),
                   ("employeeid", "Mechanic", "int", True), ("laborhours", "Labor hours", "num", True),
                   ("laborcost", "Labor cost (TL)", "num", False)],
        "fk": {"orderid": ORDER_FK,
               "serviceid": "SELECT ServiceID, Description FROM SERVICE_TYPE ORDER BY Description",
               "employeeid": "SELECT EmployeeID, FirstName || ' ' || LastName FROM EMPLOYEE "
                             "WHERE JobRole = 'Mechanic' ORDER BY FirstName"},
        "staff": {"add", "edit"},
        "hint": "Leave labor cost empty to calculate it as labor hours × the mechanic's hourly rate.",
    },
    "uses": {
        "table": "USES", "title": "Parts Used", "group": "Repairs", "pk": ["orderid", "partid"],
        "fields": [("orderid", "Repair order", "int", True), ("partid", "Part", "int", True),
                   ("quantity", "Quantity", "int", True)],
        "fk": {"orderid": ORDER_FK, "partid": "SELECT PartID, PartName FROM PART ORDER BY PartName"},
        "staff": {"add", "edit"},
        "hint": "The stock of the part is updated automatically.",
    },
    "invoices": {
        "table": "INVOICE", "title": "Invoices", "group": "Repairs", "pk": ["invoiceid"], "auto_pk": True,
        "fields": [("invoiceid", "Invoice ID", "int", False), ("orderid", "Repair order", "int", True),
                   ("issuedate", "Issue date", "date", True), ("totalamount", "Total (TL)", "num", False),
                   ("paymentstatus", "Payment status", ["Unpaid", "Paid"], True)],
        "fk": {"orderid": ORDER_FK}, "staff": {"add", "edit"},
        "hint": "Leave the total empty to calculate it from the labor costs and the parts of the order.",
    },
    "employees": {
        "table": "EMPLOYEE", "title": "Employees", "group": "Shop", "pk": ["employeeid"], "auto_pk": True,
        "fields": [("employeeid", "ID", "int", False), ("firstname", "First name", "text", True),
                   ("lastname", "Last name", "text", True),
                   ("jobrole", "Job role", ["Mechanic", "Receptionist", "Manager"], True),
                   ("hourlyrate", "Hourly rate (TL)", "num", True), ("email", "E-mail", "text", False)],
        "fk": {}, "staff": set(),
    },
    "employee_phones": {
        "table": "EMPLOYEE_PHONE", "title": "Employee Phones", "group": "Shop", "pk": ["employeeid", "phone"],
        "fields": [("employeeid", "Employee", "int", True), ("phone", "Phone", "text", True)],
        "fk": {"employeeid": EMPLOYEE_FK}, "staff": set(),
    },
    "services": {
        "table": "SERVICE_TYPE", "title": "Service Types", "group": "Shop", "pk": ["serviceid"], "auto_pk": True,
        "fields": [("serviceid", "ID", "int", False), ("description", "Description", "text", True)],
        "fk": {}, "staff": set(),
    },
    "parts": {
        "table": "PART", "title": "Parts", "group": "Shop", "pk": ["partid"], "auto_pk": True,
        "fields": [("partid", "ID", "int", False), ("supplierid", "Supplier", "int", True),
                   ("partname", "Part name", "text", True), ("unitprice", "Unit price (TL)", "num", True),
                   ("quantityinstock", "In stock", "int", True)],
        "fk": {"supplierid": "SELECT SupplierID, SupplierName FROM SUPPLIER ORDER BY SupplierName"},
        "staff": set(),
    },
    "suppliers": {
        "table": "SUPPLIER", "title": "Suppliers", "group": "Shop", "pk": ["supplierid"], "auto_pk": True,
        "fields": [("supplierid", "ID", "int", False), ("suppliername", "Supplier name", "text", True),
                   ("address", "Address", "text", False)],
        "fk": {}, "staff": set(),
    },
    "supplier_phones": {
        "table": "SUPPLIER_PHONE", "title": "Supplier Phones", "group": "Shop", "pk": ["supplierid", "phone"],
        "fields": [("supplierid", "Supplier", "int", True), ("phone", "Phone", "text", True)],
        "fk": {"supplierid": "SELECT SupplierID, SupplierName FROM SUPPLIER ORDER BY SupplierName"},
        "staff": set(),
    },
}
GROUPS = ["Customers", "Repairs", "Shop"]


def can(action, key):
    """action: view, add, edit, delete"""
    role = session.get("role")
    if role == "admin":
        return True
    if role == "staff":
        return action == "view" or action in TABLES[key]["staff"]
    return False


def pk_str(t, row):
    return "~".join(str(row[c]) for c in t["pk"])


COUNT_COLS = {"orders", "invoices", "timesused", "totalquantity", "quantityinstock", "orderid", "invoiceid"}
NUM_COLS = COUNT_COLS | {"totalhours", "totallaborcost", "laborcost", "partscost", "invoiced", "paid", "unpaid", "totalamount"}
# PostgreSQL returns unquoted column names in lower case, so report headings come from this list
HEADINGS = {"mechanic": "Mechanic", "orders": "Orders", "totalhours": "Total hours", "totallaborcost": "Labor cost (TL)",
            "orderid": "Order", "licenseplate": "License plate", "opendate": "Opened", "status": "Status",
            "laborcost": "Labor (TL)", "partscost": "Parts (TL)", "customer": "Customer", "invoices": "Invoices",
            "invoiced": "Invoiced (TL)", "paid": "Paid (TL)", "unpaid": "Unpaid (TL)", "partname": "Part",
            "timesused": "Times used", "totalquantity": "Total quantity", "quantityinstock": "In stock",
            "suppliername": "Supplier", "invoiceid": "Invoice", "totalamount": "Total (TL)", "paymentstatus": "Payment"}
app.jinja_env.globals.update(can=can, TABLES=TABLES, GROUPS=GROUPS, pk_str=pk_str, COUNT_COLS=COUNT_COLS,
                             NUM_COLS=NUM_COLS, HEADINGS=HEADINGS)

# ---------------------------------------------------------------------------
# Authentication
# ---------------------------------------------------------------------------


def login_required(f):
    @wraps(f)
    def wrapper(*a, **kw):
        if "user_id" not in session:
            return redirect(url_for("login", next=request.path))
        return f(*a, **kw)
    return wrapper


def admin_required(f):
    @wraps(f)
    @login_required
    def wrapper(*a, **kw):
        if session.get("role") != "admin":
            abort(403)
        return f(*a, **kw)
    return wrapper


@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        user = query("SELECT * FROM APP_USER WHERE Username = %s", (request.form.get("username", ""),), one=True)
        if user and check_password_hash(user["passwordhash"], request.form.get("password", "")):
            session.clear()
            session.update(user_id=user["userid"], username=user["username"], role=user["role"])
            nxt = request.args.get("next", "")
            return redirect(nxt if nxt.startswith("/") else url_for("index"))
        flash("Wrong username or password.", "error")
    return render_template("login.html")


@app.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("login"))


@app.errorhandler(403)
def forbidden(e):
    return render_template("message.html", title="Access denied",
                           text="Your role does not have permission for this page."), 403

# ---------------------------------------------------------------------------
# Dashboard, vehicle history and reports
# ---------------------------------------------------------------------------


@app.route("/")
@login_required
def index():
    counts = {k: query(f"SELECT COUNT(*) AS n FROM {t['table']}", one=True)["n"]
              for k, t in TABLES.items() if "_phones" not in k}
    open_orders = query(
        "SELECT R.OrderID, V.LicensePlate, R.OpenDate, R.Status, R.ProblemDescription FROM REPAIR_ORDER R "
        "JOIN VEHICLE V ON V.VehicleID = R.VehicleID WHERE R.Status <> 'Completed' ORDER BY R.OpenDate")
    unpaid = query(
        "SELECT I.InvoiceID, V.LicensePlate, I.IssueDate, I.TotalAmount FROM INVOICE I "
        "JOIN REPAIR_ORDER R ON R.OrderID = I.OrderID JOIN VEHICLE V ON V.VehicleID = R.VehicleID "
        "WHERE I.PaymentStatus = 'Unpaid' ORDER BY I.IssueDate")
    return render_template("index.html", counts=counts, open_orders=open_orders, unpaid=unpaid)


@app.route("/history")
@login_required
def history():
    plate = request.args.get("plate", "").strip().upper()
    vehicle, phones, orders = None, [], []
    if plate:
        vehicle = query("SELECT V.*, C.FirstName, C.LastName, C.Email FROM VEHICLE V "
                        "JOIN CUSTOMER C ON C.CustomerID = V.CustomerID "
                        "WHERE UPPER(V.LicensePlate) = %s", (plate,), one=True)
        if vehicle:
            phones = [r["phone"] for r in query("SELECT Phone FROM CUSTOMER_PHONE WHERE CustomerID = %s",
                                                (vehicle["customerid"],))]
            for o in query("SELECT * FROM REPAIR_ORDER WHERE VehicleID = %s ORDER BY OpenDate DESC",
                           (vehicle["vehicleid"],)):
                o["services"] = query(
                    "SELECT S.Description, E.FirstName || ' ' || E.LastName AS mechanic, P.LaborHours, P.LaborCost "
                    "FROM PERFORMS P JOIN SERVICE_TYPE S ON S.ServiceID = P.ServiceID "
                    "JOIN EMPLOYEE E ON E.EmployeeID = P.EmployeeID WHERE P.OrderID = %s", (o["orderid"],))
                o["parts"] = query(
                    "SELECT PT.PartName, U.Quantity, PT.UnitPrice, U.Quantity * PT.UnitPrice AS cost "
                    "FROM USES U JOIN PART PT ON PT.PartID = U.PartID WHERE U.OrderID = %s", (o["orderid"],))
                o["invoice"] = query("SELECT * FROM INVOICE WHERE OrderID = %s", (o["orderid"],), one=True)
                orders.append(o)
        else:
            flash(f"No vehicle with license plate {plate}.", "error")
    return render_template("history.html", plate=plate, vehicle=vehicle, phones=phones, orders=orders)


@app.route("/reports")
@login_required
def reports():
    start = request.args.get("start") or "2026-01-01"
    end = request.args.get("end") or date.today().isoformat()
    period = (start, end)
    data = [
        ("Mechanic working hours in the selected period", query_table(
            """SELECT E.FirstName || ' ' || E.LastName AS Mechanic,
                      COUNT(DISTINCT P.OrderID) AS Orders, SUM(P.LaborHours) AS TotalHours,
                      SUM(P.LaborCost) AS TotalLaborCost
               FROM EMPLOYEE E
               JOIN PERFORMS P ON P.EmployeeID = E.EmployeeID
               JOIN REPAIR_ORDER R ON R.OrderID = P.OrderID
               WHERE E.JobRole = 'Mechanic' AND R.OpenDate BETWEEN %s AND %s
               GROUP BY E.EmployeeID, E.FirstName, E.LastName
               ORDER BY TotalHours DESC""", period)),
        ("Repair costs in the selected period", query_table(
            """SELECT R.OrderID, V.LicensePlate, R.OpenDate, R.Status,
                      COALESCE((SELECT SUM(P.LaborCost) FROM PERFORMS P WHERE P.OrderID = R.OrderID), 0) AS LaborCost,
                      COALESCE((SELECT SUM(U.Quantity * PT.UnitPrice) FROM USES U
                                JOIN PART PT ON PT.PartID = U.PartID WHERE U.OrderID = R.OrderID), 0) AS PartsCost
               FROM REPAIR_ORDER R JOIN VEHICLE V ON V.VehicleID = R.VehicleID
               WHERE R.OpenDate BETWEEN %s AND %s
               ORDER BY R.OpenDate""", period)),
        ("Customer payments", query_table(
            """SELECT C.FirstName || ' ' || C.LastName AS Customer, COUNT(I.InvoiceID) AS Invoices,
                      SUM(I.TotalAmount) AS Invoiced,
                      SUM(CASE WHEN I.PaymentStatus = 'Paid' THEN I.TotalAmount ELSE 0 END) AS Paid,
                      SUM(CASE WHEN I.PaymentStatus = 'Unpaid' THEN I.TotalAmount ELSE 0 END) AS Unpaid
               FROM CUSTOMER C
               JOIN VEHICLE V ON V.CustomerID = C.CustomerID
               JOIN REPAIR_ORDER R ON R.VehicleID = V.VehicleID
               JOIN INVOICE I ON I.OrderID = R.OrderID
               GROUP BY C.CustomerID, C.FirstName, C.LastName
               ORDER BY Unpaid DESC, Invoiced DESC""")),
        ("Frequently used parts", query_table(
            """SELECT PT.PartName, COUNT(U.OrderID) AS TimesUsed, SUM(U.Quantity) AS TotalQuantity,
                      PT.QuantityInStock, S.SupplierName
               FROM PART PT
               JOIN USES U ON U.PartID = PT.PartID
               JOIN SUPPLIER S ON S.SupplierID = PT.SupplierID
               GROUP BY PT.PartID, PT.PartName, PT.QuantityInStock, S.SupplierName
               ORDER BY TotalQuantity DESC, TimesUsed DESC""")),
        ("Invoices above the average invoice amount", query_table(
            """SELECT C.FirstName || ' ' || C.LastName AS Customer, V.LicensePlate,
                      I.InvoiceID, I.TotalAmount, I.PaymentStatus
               FROM INVOICE I
               JOIN REPAIR_ORDER R ON R.OrderID = I.OrderID
               JOIN VEHICLE V ON V.VehicleID = R.VehicleID
               JOIN CUSTOMER C ON C.CustomerID = V.CustomerID
               WHERE I.TotalAmount > (SELECT AVG(TotalAmount) FROM INVOICE)
               ORDER BY I.TotalAmount DESC""")),
    ]
    return render_template("reports.html", reports=data, start=start, end=end)

# ---------------------------------------------------------------------------
# Generic list / add / edit / delete
# ---------------------------------------------------------------------------


def get_table(key):
    t = TABLES.get(key)
    if not t:
        abort(404)
    return t


def fk_options(t):
    return {col: query(sql) for col, sql in t["fk"].items()}


def pk_where(t):
    return " AND ".join(f"{c} = %s" for c in t["pk"])


def pk_values(t):
    vals = request.args.get("id", "").split("~")
    if len(vals) != len(t["pk"]):
        abort(404)
    return vals


def read_form(t, skip_pk):
    """Read and check the form. Returns (dict of column -> value, error message)."""
    data = {}
    for col, label, typ, required in t["fields"]:
        if skip_pk and col in t["pk"]:
            continue
        v = request.form.get(col, "").strip()
        if v == "":
            if required:
                return None, f"{label} is required."
            v = None
        elif typ == "int":
            try:
                v = int(v)
            except ValueError:
                return None, f"{label} must be a whole number."
        elif typ == "num":
            try:
                v = float(v)
            except ValueError:
                return None, f"{label} must be a number."
        data[col] = v
    return data, None


def fill_calculated(key, data, row=None):
    """Values the user may leave empty: labor cost and invoice total."""
    full = dict(row or {}, **data)
    if key == "performs" and data.get("laborcost") is None:
        emp = query("SELECT HourlyRate FROM EMPLOYEE WHERE EmployeeID = %s", (full["employeeid"],), one=True)
        if emp:
            data["laborcost"] = round(float(full["laborhours"]) * float(emp["hourlyrate"]), 2)
    if key == "invoices" and data.get("totalamount") is None:
        r = query("""SELECT COALESCE((SELECT SUM(LaborCost) FROM PERFORMS WHERE OrderID = %s), 0)
                          + COALESCE((SELECT SUM(U.Quantity * P.UnitPrice) FROM USES U
                                      JOIN PART P ON P.PartID = U.PartID WHERE U.OrderID = %s), 0) AS total""",
                  (full["orderid"], full["orderid"]), one=True)
        data["totalamount"] = float(r["total"])


STOCK_SQL = "UPDATE PART SET QuantityInStock = QuantityInStock - %s WHERE PartID = %s"


@app.route("/t/<key>")
@login_required
def table_list(key):
    t = get_table(key)
    rows = query(f"SELECT * FROM {t['table']} ORDER BY {', '.join(t['pk'])}")
    labels = {col: {list(o.values())[0]: list(o.values())[1] for o in opts} for col, opts in fk_options(t).items()}
    return render_template("list.html", key=key, t=t, rows=rows, labels=labels)


@app.route("/t/<key>/new", methods=["GET", "POST"])
@login_required
def table_new(key):
    t = get_table(key)
    if not can("add", key):
        abort(403)
    if request.method == "POST":
        data, err = read_form(t, skip_pk=False)
        if not err:
            if t.get("auto_pk") and data[t["pk"][0]] is None:
                pk = t["pk"][0]
                data[pk] = query(f"SELECT COALESCE(MAX({pk}), 0) + 1 AS n FROM {t['table']}", one=True)["n"]
            fill_calculated(key, data)
            cols = list(data)
            stmts = [(f"INSERT INTO {t['table']} ({', '.join(cols)}) VALUES ({', '.join(['%s'] * len(cols))})",
                      [data[c] for c in cols])]
            if key == "uses":
                stmts.append((STOCK_SQL, (data["quantity"], data["partid"])))
            err = execute(*stmts)
        if not err:
            flash(f"New record added to {t['title']}.", "ok")
            return redirect(url_for("table_list", key=key))
        flash(friendly(err), "error")
    return render_template("form.html", key=key, t=t, row=request.form if request.method == "POST" else {},
                           opts=fk_options(t), editing=False)


@app.route("/t/<key>/edit", methods=["GET", "POST"])
@login_required
def table_edit(key):
    t = get_table(key)
    if not can("edit", key):
        abort(403)
    ids = pk_values(t)
    row = query(f"SELECT * FROM {t['table']} WHERE {pk_where(t)}", ids, one=True)
    if not row:
        abort(404)
    if len(t["fields"]) == len(t["pk"]):
        flash("This table has only key columns. Delete the row and add a new one instead.", "error")
        return redirect(url_for("table_list", key=key))
    if request.method == "POST":
        data, err = read_form(t, skip_pk=True)
        if not err:
            fill_calculated(key, data, row)
            sets = ", ".join(f"{c} = %s" for c in data)
            stmts = [(f"UPDATE {t['table']} SET {sets} WHERE {pk_where(t)}", list(data.values()) + ids)]
            if key == "uses":
                stmts.append((STOCK_SQL, (data["quantity"] - row["quantity"], row["partid"])))
            err = execute(*stmts)
        if not err:
            flash("Record updated.", "ok")
            return redirect(url_for("table_list", key=key))
        flash(friendly(err), "error")
        row = dict(row, **request.form)
    return render_template("form.html", key=key, t=t, row=row, opts=fk_options(t), editing=True)


@app.route("/t/<key>/delete", methods=["POST"])
@login_required
def table_delete(key):
    t = get_table(key)
    if not can("delete", key):
        abort(403)
    ids = pk_values(t)
    row = query(f"SELECT * FROM {t['table']} WHERE {pk_where(t)}", ids, one=True)
    stmts = [(f"DELETE FROM {t['table']} WHERE {pk_where(t)}", ids)]
    if key == "uses" and row:
        stmts.append((STOCK_SQL, (-row["quantity"], row["partid"])))
    err = execute(*stmts)
    if err:
        app.logger.warning("Delete failed on %s %s: %s", t["table"], ids, err)
        flash("This record cannot be deleted because other records depend on it "
              "(for example, a vehicle that has repair orders).", "error")
    else:
        flash("Record deleted.", "ok")
    return redirect(url_for("table_list", key=key))


def friendly(err):
    e = err.lower()
    if "quantityinstock" in e or "part_quantityinstock_check" in e:
        return "There are not enough parts in stock."
    if "unique" in e or "duplicate key" in e:
        return "A record with the same value already exists. (" + err + ")"
    if "check" in e:
        return "A value is not allowed by the database rules. (" + err + ")"
    if "foreign key" in e:
        return "A linked record does not exist. (" + err + ")"
    return err

# ---------------------------------------------------------------------------
# User management (admin only)
# ---------------------------------------------------------------------------


@app.route("/users", methods=["GET", "POST"])
@admin_required
def users():
    if request.method == "POST":
        username = request.form.get("username", "").strip()
        password = request.form.get("password", "")
        role = request.form.get("role", "staff")
        if not username or len(password) < 6 or role not in ("admin", "staff"):
            flash("Enter a username, a password of at least 6 characters and a role.", "error")
        else:
            nxt = query("SELECT COALESCE(MAX(UserID), 0) + 1 AS n FROM APP_USER", one=True)["n"]
            err = execute(("INSERT INTO APP_USER (UserID, Username, PasswordHash, Role) VALUES (%s, %s, %s, %s)",
                           (nxt, username, generate_password_hash(password, method="pbkdf2:sha256"), role)))
            flash(err or f"User {username} created.", "error" if err else "ok")
        return redirect(url_for("users"))
    return render_template("users.html", users=query("SELECT UserID, Username, Role FROM APP_USER ORDER BY UserID"))


@app.route("/users/<int:uid>/delete", methods=["POST"])
@admin_required
def user_delete(uid):
    if uid == session.get("user_id"):
        flash("You cannot delete your own account.", "error")
    else:
        err = execute(("DELETE FROM APP_USER WHERE UserID = %s", (uid,)))
        flash(err or "User deleted.", "error" if err else "ok")
    return redirect(url_for("users"))


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8000, debug=True)

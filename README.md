# AutoRepair Database System

CMPE341 Database Design and Management term project, Atılım University, Fall 2026-2027.
Group 1 section 2: Boran Ergül,Yağmur Ataman,Yalçın Yaşar

A web app for a car repair shop. It keeps customers, vehicles, employees, repair orders,
the services and parts of each repair, suppliers and invoices in a PostgreSQL database.

Main features:

- insert, update and delete pages for all 13 tables, with drop-down lists for foreign keys
- vehicle history: search a license plate and see the owner, every repair order, the services,
  mechanics, parts and the invoice
- reports for a selected period: mechanic working hours, repair costs, customer payments,
  frequently used parts and invoices above the average
- labor cost (hours × hourly rate) and invoice totals are calculated when left empty,
  and part stock goes down automatically when parts are used

## Run it

You only need Docker (Docker Desktop on Windows/macOS).

```bash
git clone https://github.com/BoranErgul/autorepair-database-system-group-X.git
cd autorepair-database-system-group-X
docker compose up
```

The first start creates the database and loads the tables and sample data from `db/init/`.

Open: **http://localhost:8080**

On the server the app runs on port 80, so it opens at **http://<server-ip>** (see `DEPLOYMENT.md`).

## Test accounts

| Role  | Username | Password   | What the role can do |
|-------|----------|------------|----------------------|
| admin | `admin`  | `admin123` | View, add, edit and delete every table, manage users |
| staff | `staff`  | `staff123` | View every table and report; add and edit customers, customer phones, vehicles, repair orders, services performed, parts used and invoices; no delete |

Passwords are stored as salted PBKDF2-SHA256 hashes in the `app_user` table.

## Project structure

```
docker-compose.yml        database + web app
db/init/01_schema.sql     CREATE TABLE statements with constraints (13 tables)
db/init/02_data.sql       sample data (at least 3 rows per table)
db/init/03_users.sql      login table and the two test users
db/queries.sql            the three queries from the report
app/app.py                Flask app (login, roles, insert / update / delete, vehicle history, reports)
app/templates/            HTML pages
app/Dockerfile            image for the web app
DEPLOYMENT.md             how the app is put on a cloud server
```

## Reset the database

The SQL files in `db/init/` only run when the database volume is empty. To start again from the sample data:

```bash
docker compose down -v
docker compose up
```

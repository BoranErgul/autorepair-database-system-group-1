-- AutoRepair Database System - sample data

INSERT INTO CUSTOMER VALUES
  (1, 'Boran', 'Ergul', 'ergul.boran@gmail.com', 'Çankaya, Ankara'),
  (2, 'Yagmur', 'Ataman', 'atman.yagmur@mail.com', 'Yenimahalle, Ankara'),
  (3, 'Yalçın', 'Yaşar', 'yaşar.yalcin@mail.com', 'İncek, Ankara'),
  (4, 'Zeynep', 'Şahin', 'zeynep.sahin@mail.com', 'Etimesgut, Ankara'),
  (5, 'Can', 'Öztürk', 'can.ozturk@mail.com', 'Bornova, İzmir');
INSERT INTO CUSTOMER_PHONE VALUES
  (1, '05321234567'), (1, '03124567890'), (2, '05337654321'), (3, '05441112233'),
  (4, '05059998877'), (5, '05423334455'), (5, '02324445566');
INSERT INTO VEHICLE VALUES
  (1, 1, '06 BRN 205', 'Opel', 'Grandland', 2023),
  (2, 2, '06 AZ 456', 'Audi', 'A3', 2010),
  (3, 3, '34 BE 789', 'Toyota', 'Corolla', 2019),
  (4, 1, '06 DEF 321', 'Fiat', 'Egea', 2021),
  (5, 5, '35 TRK 555', 'Ford', 'Focus', 2017),
  (6, 4, '06 NR 202', 'Kia', 'Picanto', 2023);
INSERT INTO EMPLOYEE VALUES
  (1, 'Hasan', 'Arslan', 'Mechanic', 450, 'hasan.arslan@autorepair.com'),
  (2, 'Murat', 'Çelik', 'Mechanic', 400, 'murat.celik@autorepair.com'),
  (3, 'Burak', 'Aydın', 'Mechanic', 380, 'burak.aydin@autorepair.com'),
  (4, 'Emre', 'Koç', 'Mechanic', 350, 'emre.koc@autorepair.com'),
  (5, 'Ayşe', 'Polat', 'Receptionist', 250, 'ayse.polat@autorepair.com'),
  (6, 'Selin', 'Güneş', 'Receptionist', 250, 'selin.gunes@autorepair.com'),
  (7, 'Kemal', 'Öz', 'Manager', 600, 'kemal.oz@autorepair.com');

INSERT INTO EMPLOYEE_PHONE VALUES
  (1, '05301110001'),
  (1, '05551110001'),
  (2, '05301110002'),
  (3, '05301110003'),
  (4, '05301110004'),
  (5, '05301110005'),
  (6, '05301110006'),
  (7, '05301110007');

INSERT INTO REPAIR_ORDER VALUES
  (1001, 1, 5, '2026-09-15', '2026-09-16', 'Periodic oil change', 'Completed'),
  (1002, 2, 6, '2026-09-22', '2026-09-24', 'Squeaking noise when braking', 'Completed'),
  (1003, 3, 5, '2026-10-10', '2026-10-10', 'Flat front tire', 'Completed'),
  (1004, 1, 6, '2026-10-20', '2026-10-22', 'A/C is not cooling', 'Completed'),
  (1005, 4, 5, '2026-11-02', '2026-11-04', 'Engine warning light is on', 'Completed'),
  (1006, 5, 6, '2026-11-15', NULL, 'Brake noise, oil change due', 'In Progress'),
  (1007, 6, 5, '2026-11-20', NULL, 'Car does not start in the morning', 'Open');

INSERT INTO SERVICE_TYPE VALUES
  (1, 'Oil Change'),
  (2, 'Brake Repair'),
  (3, 'Engine Diagnostics'),
  (4, 'Tire Replacement'),
  (5, 'A/C Service'),
  (6, 'Battery Replacement');

INSERT INTO PERFORMS VALUES
  (1001, 1, 1, 0.5, 225.00),
  (1002, 2, 2, 2.0, 800.00),
  (1002, 3, 3, 1.0, 380.00),
  (1003, 4, 4, 1.0, 350.00),
  (1004, 5, 3, 1.5, 570.00),
  (1004, 3, 1, 1.0, 450.00),
  (1005, 3, 1, 1.5, 675.00),
  (1005, 1, 2, 0.5, 200.00),
  (1006, 2, 2, 2.0, 800.00),
  (1006, 2, 4, 1.0, 350.00),
  (1007, 3, 3, 0.5, 190.00);

INSERT INTO SUPPLIER VALUES
  (1, 'Boran Oto Yedek Parça', 'Ostim, Ankara'),
  (2, 'Özdemir Fren Sistemleri', 'Ümraniye, İstanbul'),
  (3, 'Lastikçi Kardeşler', 'Sincan, Ankara'),
  (4, 'Ege Akü', 'Bornova, İzmir');

INSERT INTO SUPPLIER_PHONE VALUES
  (1, '03124445566'),
  (1, '05324445566'),
  (2, '02167778899'),
  (3, '03123332211'),
  (4, '02325556677');

INSERT INTO PART VALUES
  (1, 1, 'Engine Oil 5W-30 (1 L)', 450, 60),
  (2, 1, 'Oil Filter', 350, 25),
  (3, 2, 'Brake Pad Set', 2200, 10),
  (4, 1, 'Air Filter', 400, 18),
  (5, 3, 'Tire 205/55 R16', 3200, 16),
  (6, 2, 'A/C Refrigerant Gas', 900, 8),
  (7, 4, 'Car Battery 60 Ah', 3500, 5);

INSERT INTO USES VALUES
  (1001, 1, 4),
  (1001, 2, 1),
  (1002, 3, 1),
  (1003, 5, 1),
  (1004, 6, 1),
  (1005, 1, 4),
  (1005, 2, 1),
  (1005, 4, 1),
  (1006, 3, 1);

INSERT INTO INVOICE VALUES
  (5001, 1001, '2026-09-16', 2375.00, 'Paid'),
  (5002, 1002, '2026-09-24', 3380.00, 'Paid'),
  (5003, 1003, '2026-10-10', 3550.00, 'Paid'),
  (5004, 1004, '2026-10-22', 1920.00, 'Unpaid'),
  (5005, 1005, '2026-11-04', 3425.00, 'Unpaid');

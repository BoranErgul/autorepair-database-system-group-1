-- AutoRepair Database System - the three queries of Section 5.3 (PostgreSQL 16)

-- Query 1 (join): repair history of one vehicle
SELECT R.OrderID, R.OpenDate,
       C.FirstName || ' ' || C.LastName AS Customer,
       S.Description                    AS Service,
       E.FirstName || ' ' || E.LastName AS Mechanic,
       P.LaborHours, P.LaborCost
FROM VEHICLE V
JOIN CUSTOMER     C ON V.CustomerID = C.CustomerID
JOIN REPAIR_ORDER R ON R.VehicleID  = V.VehicleID
JOIN PERFORMS     P ON P.OrderID    = R.OrderID
JOIN SERVICE_TYPE S ON S.ServiceID  = P.ServiceID
JOIN EMPLOYEE     E ON E.EmployeeID = P.EmployeeID
WHERE V.LicensePlate = '06 BRN 205'
ORDER BY R.OpenDate, S.Description;

-- Query 2 (group by / order by): mechanic working hours in a period
SELECT E.FirstName, E.LastName,
       COUNT(DISTINCT P.OrderID) AS Orders,
       SUM(P.LaborHours)         AS TotalHours,
       SUM(P.LaborCost)          AS TotalLaborCost
FROM EMPLOYEE E
JOIN PERFORMS     P ON P.EmployeeID = E.EmployeeID
JOIN REPAIR_ORDER R ON R.OrderID    = P.OrderID
WHERE E.JobRole = 'Mechanic'
  AND R.OpenDate BETWEEN '2026-10-01' AND '2026-11-30'
GROUP BY E.EmployeeID, E.FirstName, E.LastName
ORDER BY TotalHours DESC, E.LastName;

-- Query 3 (subquery): invoices above the average
SELECT C.FirstName, C.LastName, V.LicensePlate,
       I.InvoiceID, I.TotalAmount, I.PaymentStatus
FROM INVOICE I
JOIN REPAIR_ORDER R ON R.OrderID    = I.OrderID
JOIN VEHICLE      V ON V.VehicleID  = R.VehicleID
JOIN CUSTOMER     C ON C.CustomerID = V.CustomerID
WHERE I.TotalAmount > (SELECT AVG(TotalAmount) FROM INVOICE)
ORDER BY I.TotalAmount DESC;

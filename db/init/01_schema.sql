-- AutoRepair Database System - tables and constraints (PostgreSQL 16)

CREATE TABLE CUSTOMER (
    CustomerID   INT           PRIMARY KEY,
    FirstName    VARCHAR(30)   NOT NULL,
    LastName     VARCHAR(30)   NOT NULL,
    Email        VARCHAR(60)   UNIQUE,
    Address      VARCHAR(100)
);

CREATE TABLE CUSTOMER_PHONE (
    CustomerID   INT           NOT NULL,
    Phone        VARCHAR(15)   NOT NULL,
    PRIMARY KEY (CustomerID, Phone),
    FOREIGN KEY (CustomerID) REFERENCES CUSTOMER(CustomerID) ON DELETE CASCADE
);

CREATE TABLE VEHICLE (
    VehicleID    INT           PRIMARY KEY,
    CustomerID   INT           NOT NULL,
    LicensePlate VARCHAR(12)   NOT NULL UNIQUE,
    Make         VARCHAR(30)   NOT NULL,
    Model        VARCHAR(30)   NOT NULL,
    Year         INT           CHECK (Year BETWEEN 1950 AND 2027),
    FOREIGN KEY (CustomerID) REFERENCES CUSTOMER(CustomerID)
);

CREATE TABLE EMPLOYEE (
    EmployeeID   INT           PRIMARY KEY,
    FirstName    VARCHAR(30)   NOT NULL,
    LastName     VARCHAR(30)   NOT NULL,
    JobRole      VARCHAR(15)   NOT NULL
                 CHECK (JobRole IN ('Mechanic', 'Receptionist', 'Manager')),
    HourlyRate   DECIMAL(8,2)  NOT NULL CHECK (HourlyRate >= 0),
    Email        VARCHAR(60)   UNIQUE
);

CREATE TABLE EMPLOYEE_PHONE (
    EmployeeID   INT           NOT NULL,
    Phone        VARCHAR(15)   NOT NULL,
    PRIMARY KEY (EmployeeID, Phone),
    FOREIGN KEY (EmployeeID) REFERENCES EMPLOYEE(EmployeeID) ON DELETE CASCADE
);

CREATE TABLE REPAIR_ORDER (
    OrderID            INT           PRIMARY KEY,
    VehicleID          INT           NOT NULL,
    EmployeeID         INT           NOT NULL,
    OpenDate           DATE          NOT NULL,
    CompletionDate     DATE,
    ProblemDescription VARCHAR(200)  NOT NULL,
    Status             VARCHAR(15)   NOT NULL
                       CHECK (Status IN ('Open', 'In Progress', 'Completed')),
    FOREIGN KEY (VehicleID)  REFERENCES VEHICLE(VehicleID),
    FOREIGN KEY (EmployeeID) REFERENCES EMPLOYEE(EmployeeID),
    CHECK (CompletionDate IS NULL OR CompletionDate >= OpenDate)
);

CREATE TABLE SERVICE_TYPE (
    ServiceID    INT           PRIMARY KEY,
    Description  VARCHAR(60)   NOT NULL UNIQUE
);

CREATE TABLE PERFORMS (
    OrderID      INT           NOT NULL,
    ServiceID    INT           NOT NULL,
    EmployeeID   INT           NOT NULL,
    LaborHours   DECIMAL(4,1)  NOT NULL CHECK (LaborHours > 0),
    LaborCost    DECIMAL(10,2) NOT NULL CHECK (LaborCost >= 0),
    PRIMARY KEY (OrderID, ServiceID, EmployeeID),
    FOREIGN KEY (OrderID)    REFERENCES REPAIR_ORDER(OrderID) ON DELETE CASCADE,
    FOREIGN KEY (ServiceID)  REFERENCES SERVICE_TYPE(ServiceID),
    FOREIGN KEY (EmployeeID) REFERENCES EMPLOYEE(EmployeeID)
);

CREATE TABLE SUPPLIER (
    SupplierID   INT           PRIMARY KEY,
    SupplierName VARCHAR(60)   NOT NULL,
    Address      VARCHAR(100)
);

CREATE TABLE SUPPLIER_PHONE (
    SupplierID   INT           NOT NULL,
    Phone        VARCHAR(15)   NOT NULL,
    PRIMARY KEY (SupplierID, Phone),
    FOREIGN KEY (SupplierID) REFERENCES SUPPLIER(SupplierID) ON DELETE CASCADE
);

CREATE TABLE PART (
    PartID          INT           PRIMARY KEY,
    SupplierID      INT           NOT NULL,
    PartName        VARCHAR(50)   NOT NULL,
    UnitPrice       DECIMAL(10,2) NOT NULL CHECK (UnitPrice >= 0),
    QuantityInStock INT           NOT NULL DEFAULT 0 CHECK (QuantityInStock >= 0),
    FOREIGN KEY (SupplierID) REFERENCES SUPPLIER(SupplierID)
);

CREATE TABLE USES (
    OrderID      INT           NOT NULL,
    PartID       INT           NOT NULL,
    Quantity     INT           NOT NULL CHECK (Quantity > 0),
    PRIMARY KEY (OrderID, PartID),
    FOREIGN KEY (OrderID) REFERENCES REPAIR_ORDER(OrderID) ON DELETE CASCADE,
    FOREIGN KEY (PartID)  REFERENCES PART(PartID)
);

CREATE TABLE INVOICE (
    InvoiceID     INT           PRIMARY KEY,
    OrderID       INT           NOT NULL UNIQUE,
    IssueDate     DATE          NOT NULL,
    TotalAmount   DECIMAL(10,2) NOT NULL CHECK (TotalAmount >= 0),
    PaymentStatus VARCHAR(10)   NOT NULL DEFAULT 'Unpaid'
                  CHECK (PaymentStatus IN ('Paid', 'Unpaid')),
    FOREIGN KEY (OrderID) REFERENCES REPAIR_ORDER(OrderID)
);

CREATE DATABASE MauritiusTourism;
GO
USE MauritiusTourism;
GO

CREATE TABLE Date_Dim (
    Arrival_ID CHAR(7) PRIMARY KEY,      -- e.g. 'A201801'
    Full_Date DATE NOT NULL,
    Year INT NOT NULL,
    Month INT NOT NULL,
    Month_Name VARCHAR(20) NOT NULL
);

CREATE TABLE Countries (
    Country_ID INT IDENTITY(1,1) PRIMARY KEY,
    Country_Name VARCHAR(100) NOT NULL UNIQUE,
    Continent VARCHAR(50)
);

CREATE TABLE Arrivals_Fact (
    Fact_ID INT IDENTITY(1,1) PRIMARY KEY,
    Arrival_ID CHAR(7) FOREIGN KEY REFERENCES Date_Dim(Arrival_ID),
    Country_ID INT FOREIGN KEY REFERENCES Countries(Country_ID),
    Air_Arrivals INT,
    Sea_Arrivals INT
);

CREATE TABLE Income_Dim (
    Arrival_ID CHAR(7) PRIMARY KEY FOREIGN KEY REFERENCES Date_Dim(Arrival_ID),
    Net_Income DECIMAL(18,2)
);

CREATE TABLE Events (
    Event_ID INT IDENTITY(1,1) PRIMARY KEY,
    Arrival_ID CHAR(7) FOREIGN KEY REFERENCES Date_Dim(Arrival_ID),
    Event_Date DATE,
    Event_Name VARCHAR(200)
);

SELECT 
    fk.name AS ForeignKey,
    OBJECT_NAME(fk.parent_object_id) AS ChildTable,
    OBJECT_NAME(fk.referenced_object_id) AS ParentTable
FROM sys.foreign_keys fk;

;WITH Months AS (
    SELECT CAST('2018-01-01' AS DATE) AS Full_Date
    UNION ALL
    SELECT DATEADD(MONTH, 1, Full_Date)
    FROM Months
    WHERE Full_Date < '2025-12-01'
)
INSERT INTO Date_Dim (Arrival_ID, Full_Date, Year, Month, Month_Name)
SELECT
    'A' + CAST(YEAR(Full_Date) AS CHAR(4)) + RIGHT('0' + CAST(MONTH(Full_Date) AS VARCHAR(2)), 2) AS Arrival_ID,
    Full_Date,
    YEAR(Full_Date) AS Year,
    MONTH(Full_Date) AS Month,
    DATENAME(MONTH, Full_Date) AS Month_Name
FROM Months
OPTION (MAXRECURSION 100);
SELECT TOP 5 * FROM Date_Dim ORDER BY Full_Date;
SELECT TOP 5 * FROM Date_Dim ORDER BY Full_Date DESC;

SELECT e.Arrival_ID, e.Event_Date, e.Event_Name, d.Month_Name, d.Year
FROM Events e
JOIN Date_Dim d ON e.Arrival_ID = d.Arrival_ID
ORDER BY e.Event_Date;
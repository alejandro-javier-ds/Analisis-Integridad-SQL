CREATE DATABASE PortafolioDB;
GO

USE PortafolioDB;
GO

CREATE TABLE VentasCrudas (
    ID_Venta INT,
    Producto VARCHAR(100),
    Cantidad INT,
    Precio_Unitario DECIMAL(10, 2),
    Correo VARCHAR(150)
);
GO

SELECT * FROM dbo.VentasCrudas;
SELECT * FROM dbo.VentasLimpias;
SELECT * FROM dbo.VentasBasura;

BULK INSERT VentasCrudas
FROM 'C:\Users\ALEX\Desktop\Proyectos-Git\Analisis-Integridad-SQL\ventas_crudas.csv'
WITH (
    FIELDTERMINATOR = ',',
    ROWTERMINATOR = '\n',
    FIRSTROW = 2,
    CODEPAGE = '65001'
);


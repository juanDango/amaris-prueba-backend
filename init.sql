CREATE TABLE IF NOT EXISTS cliente (
    id INTEGER PRIMARY KEY,
    nombre VARCHAR(100) NOT NULL,
    apellidos VARCHAR(100) NOT NULL,
    ciudad VARCHAR(100) NOT NULL
);

CREATE TABLE IF NOT EXISTS sucursal (
    id INTEGER PRIMARY KEY,
    nombre VARCHAR(100) NOT NULL,
    ciudad VARCHAR(100) NOT NULL
);

CREATE TABLE IF NOT EXISTS producto (
    id INTEGER PRIMARY KEY,
    nombre VARCHAR(100) NOT NULL,
    tipo_producto VARCHAR(100) NOT NULL,
);

CREATE TABLE IF NOT EXISTS inscripcion (
    id_producto INTEGER NOT NULL REFERENCES producto(id) ON DELETE CASCADE,
    id_cliente  INTEGER NOT NULL REFERENCES cliente(id)  ON DELETE CASCADE,
    PRIMARY KEY (id_producto, id_cliente)
);

CREATE TABLE IF NOT EXISTS disponibilidad (
    id_sucursal INTEGER NOT NULL REFERENCES sucursal(id) ON DELETE CASCADE,
    id_producto INTEGER NOT NULL REFERENCES producto(id) ON DELETE CASCADE,
    PRIMARY KEY (id_sucursal, id_producto)
);

CREATE TABLE IF NOT EXISTS visitan (
    id_cliente  INTEGER NOT NULL REFERENCES cliente(id)  ON DELETE CASCADE,
    id_sucursal INTEGER NOT NULL REFERENCES sucursal(id) ON DELETE CASCADE,
    fecha DATE NOT NULL,
    PRIMARY KEY (id_cliente, id_sucursal)
);

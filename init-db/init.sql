CREATE TABLE IF NOT EXISTS cliente (
    ci VARCHAR(20) PRIMARY KEY,
    nombre VARCHAR(50) NOT NULL,
    apellidos VARCHAR(50) NOT NULL
);

CREATE TABLE IF NOT EXISTS casoJuridico (
    nrocaso VARCHAR(50) PRIMARY KEY,
    materia VARCHAR(50) NOT NULL
);

CREATE TABLE IF NOT EXISTS contratoServicio (
    nrocontrato VARCHAR(50) PRIMARY KEY,
    fecha DATE NOT NULL,
    monto NUMERIC(10,2) NOT NULL,
    cicliente VARCHAR(20) NOT NULL,
    nrocasojuridico VARCHAR(50),
    FOREIGN KEY (cicliente) REFERENCES cliente(ci)
        ON DELETE CASCADE
        ON UPDATE CASCADE,
    FOREIGN KEY (nrocasojuridico) REFERENCES casoJuridico(nrocaso)
        ON DELETE CASCADE
        ON UPDATE CASCADE
);

-- Crear base de datos si no existe
CREATE DATABASE IF NOT EXISTS chat_system;

-- Usar la base de datos
USE chat_system;

-- Crear la tabla de usuarios
CREATE TABLE IF NOT EXISTS users (
    id INT AUTO_INCREMENT PRIMARY KEY,
    username VARCHAR(50) NOT NULL UNIQUE,
    password VARCHAR(100) NOT NULL,
    role ENUM('client', 'moderator') NOT NULL DEFAULT 'client'
);

INSERT INTO users (username, password, role) VALUES
('carlos', '1', 'client'),
('chino', '1', 'client'),
('dulce', '2', 'moderator');

select*from users;
CREATE TABLE IF NOT EXISTS messages (
    id INT AUTO_INCREMENT PRIMARY KEY,
    username VARCHAR(50) NOT NULL,
    role VARCHAR(20),
    message TEXT NOT NULL,
    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

select*from users;
 show tables

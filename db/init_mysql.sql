-- Table des utilisateurs
CREATE TABLE IF NOT EXISTS users (
    id INT AUTO_INCREMENT PRIMARY KEY,
    username VARCHAR(50) UNIQUE NOT NULL,
    password VARCHAR(100) NOT NULL,
    is_admin BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    INDEX idx_created_at (created_at)
);

-- Création de l'admin par défaut si n'existe pas
INSERT IGNORE INTO users (username, password, is_admin)
VALUES ('admin', 'admin', TRUE);

-- Vider le cache après les modifications
FLUSH TABLES users;

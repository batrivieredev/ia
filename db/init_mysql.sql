-- Table des utilisateurs
CREATE TABLE IF NOT EXISTS users (
    id INT AUTO_INCREMENT PRIMARY KEY,
    username VARCHAR(50) UNIQUE NOT NULL,
    password VARCHAR(100) NOT NULL,
    is_admin BOOLEAN DEFAULT FALSE,
    preferences JSON DEFAULT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    INDEX idx_created_at (created_at)
);

-- Table des préférences par défaut
CREATE TABLE IF NOT EXISTS default_preferences (
    id INT AUTO_INCREMENT PRIMARY KEY,
    preferences JSON NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Création de l'admin par défaut si n'existe pas
INSERT IGNORE INTO users (username, password, is_admin)
VALUES ('admin', 'admin', TRUE);

-- Préférences par défaut
INSERT IGNORE INTO default_preferences (id, preferences) VALUES (1, '{
    "language": "fr",
    "interests": [],
    "model": "phi",
    "system_message": "Tu es Fusikab IA, un assistant qui aide les utilisateurs de manière amicale et professionnelle, spécialisé dans la musique et le DJing."
}');

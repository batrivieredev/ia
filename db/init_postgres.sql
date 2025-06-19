-- Table des utilisateurs
CREATE TABLE IF NOT EXISTS users (
    id SERIAL PRIMARY KEY,
    username VARCHAR(50) UNIQUE NOT NULL,
    password VARCHAR(100) NOT NULL,
    is_admin BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Création de l'admin par défaut
INSERT INTO users (username, password, is_admin)
VALUES ('admin', 'admin', TRUE)
ON CONFLICT (username) DO NOTHING;

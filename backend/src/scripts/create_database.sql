-- Создание базы данных
CREATE DATABASE IF NOT EXISTS sportmaster CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;

-- Использование базы данных
USE sportmaster;

-- Таблица продуктов
CREATE TABLE IF NOT EXISTS products (
    model_id INT PRIMARY KEY,
    product_type VARCHAR(100) NOT NULL,
    rating FLOAT NOT NULL,
    last_review_id INT NULL,
    ai_summary TEXT NULL,
    ai_summary_likes INT DEFAULT 0 NOT NULL,
    ai_summary_dislikes INT DEFAULT 0 NOT NULL,
    last_generation_review_count INT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- Таблица отзывов
CREATE TABLE IF NOT EXISTS reviews (
    review_id INT PRIMARY KEY AUTO_INCREMENT,
    model_id INT NOT NULL,
    general_review TEXT DEFAULT '',
    review_rating FLOAT NULL,
    reviewer_name VARCHAR(100) NULL,
    pros TEXT NULL,
    cons TEXT NULL,
    INDEX idx_model_id (model_id),
    FOREIGN KEY (model_id) REFERENCES products(model_id) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- Таблица аспектов
CREATE TABLE IF NOT EXISTS aspects (
    id INT PRIMARY KEY AUTO_INCREMENT,
    model_id INT NOT NULL,
    aspect_type VARCHAR(10) NOT NULL,
    aspect VARCHAR(255) NOT NULL,
    count INT DEFAULT 0 NOT NULL,
    INDEX idx_model_id (model_id),
    FOREIGN KEY (model_id) REFERENCES products(model_id) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- Таблица цитат
CREATE TABLE IF NOT EXISTS quotes (
    id INT PRIMARY KEY AUTO_INCREMENT,
    model_id INT NOT NULL,
    text TEXT NOT NULL,
    review_id INT NOT NULL,
    sentiment VARCHAR(20) NOT NULL,
    INDEX idx_model_id (model_id),
    FOREIGN KEY (model_id) REFERENCES products(model_id) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- Связь аспектов и отзывов
CREATE TABLE IF NOT EXISTS aspect_reviews (
    aspect_id INT NOT NULL,
    review_id INT NOT NULL,
    PRIMARY KEY (aspect_id, review_id),
    FOREIGN KEY (aspect_id) REFERENCES aspects(id) ON DELETE CASCADE,
    FOREIGN KEY (review_id) REFERENCES reviews(review_id) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- Связь продуктов и финальных преимуществ
CREATE TABLE IF NOT EXISTS product_final_advantages (
    model_id INT NOT NULL,
    aspect_id INT NOT NULL,
    PRIMARY KEY (model_id, aspect_id),
    FOREIGN KEY (model_id) REFERENCES products(model_id) ON DELETE CASCADE,
    FOREIGN KEY (aspect_id) REFERENCES aspects(id) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- Связь продуктов и финальных недостатков
CREATE TABLE IF NOT EXISTS product_final_disadvantages (
    model_id INT NOT NULL,
    aspect_id INT NOT NULL,
    PRIMARY KEY (model_id, aspect_id),
    FOREIGN KEY (model_id) REFERENCES products(model_id) ON DELETE CASCADE,
    FOREIGN KEY (aspect_id) REFERENCES aspects(id) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- Комментарии пользователя к AI-сводке (кнопка «Обратная связь» на карточке товара)
CREATE TABLE IF NOT EXISTS summary_feedback (
    id INT PRIMARY KEY AUTO_INCREMENT,
    model_id INT NOT NULL,
    text TEXT NOT NULL,
    INDEX idx_model_id (model_id),
    FOREIGN KEY (model_id) REFERENCES products(model_id) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
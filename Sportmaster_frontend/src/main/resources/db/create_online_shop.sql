-- Схема БД online_shop (Java-часть: каталог, пользователи, корзина, заказы)
-- model_id в products — связка с sportmaster.products.model_id (Python-часть: отзывы/рейтинг/AI-сводка)

CREATE TABLE IF NOT EXISTS categories (
    id INT PRIMARY KEY AUTO_INCREMENT,
    name VARCHAR(100) NOT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

CREATE TABLE IF NOT EXISTS products (
    id INT PRIMARY KEY AUTO_INCREMENT,
    name VARCHAR(255) NOT NULL,
    description TEXT,
    price DOUBLE NOT NULL,
    category_id INT NOT NULL,
    model_id INT NULL,
    FOREIGN KEY (category_id) REFERENCES categories(id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

CREATE TABLE IF NOT EXISTS users (
    id INT PRIMARY KEY AUTO_INCREMENT,
    name VARCHAR(100) NOT NULL,
    email VARCHAR(150) NOT NULL UNIQUE,
    password VARCHAR(255) NOT NULL,
    role VARCHAR(20) NOT NULL DEFAULT 'USER'
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

CREATE TABLE IF NOT EXISTS cart (
    user_id INT NOT NULL,
    product_id INT NOT NULL,
    quantity INT NOT NULL DEFAULT 1,
    PRIMARY KEY (user_id, product_id),
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
    FOREIGN KEY (product_id) REFERENCES products(id) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

CREATE TABLE IF NOT EXISTS orders (
    id INT PRIMARY KEY AUTO_INCREMENT,
    user_id INT NOT NULL,
    order_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    status VARCHAR(30) NOT NULL DEFAULT 'NEW',
    FOREIGN KEY (user_id) REFERENCES users(id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

CREATE TABLE IF NOT EXISTS order_items (
    id INT PRIMARY KEY AUTO_INCREMENT,
    order_id INT NOT NULL,
    product_id INT NOT NULL,
    quantity INT NOT NULL,
    price DOUBLE NOT NULL,
    FOREIGN KEY (order_id) REFERENCES orders(id) ON DELETE CASCADE,
    FOREIGN KEY (product_id) REFERENCES products(id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- Демо-каталог: 3 товара, связанные с реальными model_id из sportmaster.products
INSERT INTO categories (id, name) VALUES
    (1, 'Куртки'), (2, 'Кроссовки'), (3, 'Кеды')
ON DUPLICATE KEY UPDATE name = VALUES(name);

INSERT INTO products (id, name, description, price, category_id, model_id) VALUES
    (1, 'Ультралегкий пуховик мужской', 'Лёгкий демисезонный пуховик с водоотталкивающей тканью.', 8649, 1, 11695),
    (2, 'Кроссовки мужские PUMA', 'Повседневные кроссовки для города и тренировок.', 7999, 2, 17960),
    (3, 'Кеды Adidas Forum', 'Классические кеды в стиле ретро-баскетбол.', 13642, 3, 13433)
ON DUPLICATE KEY UPDATE
    name = VALUES(name), description = VALUES(description),
    price = VALUES(price), category_id = VALUES(category_id), model_id = VALUES(model_id);

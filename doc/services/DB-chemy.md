-- Пользователи
CREATE TABLE Users (
    user_id SERIAL PRIMARY KEY,
    email VARCHAR(255) UNIQUE NOT NULL,
    goodle_id VARCHAR(255) UNIQUE NOT NULL,
    location VARCHAR(255),
    created_at TIMESTAMP DEFAULT NOW()
);

-- Товары
CREATE TABLE Products (
    product_id SERIAL PRIMARY KEY,
    seller_id INTEGER REFERENCES Users(user_id),  -- кто продаёт
    status_id INTEGER REFERENCES ProductStatus(status_id),
    name VARCHAR(255) NOT NULL,
    description TEXT,
    price DECIMAL(10,2) NOT NULL,
    quantity INTEGER NOT NULL,
    media_url VARCHAR(255),
    updated_at TIMESTAMP DEFAULT NOW()
);

-- Справочник статусов товара
CREATE TABLE ProductStatus (
    status_id SERIAL PRIMARY KEY,
    status_name VARCHAR(50) UNIQUE NOT NULL
);
-- Вставка данных
INSERT INTO ProductStatus (status_name) VALUES 
    ('new'), ('used'), ('broken'), ('inactive'), ('out_of_stock');

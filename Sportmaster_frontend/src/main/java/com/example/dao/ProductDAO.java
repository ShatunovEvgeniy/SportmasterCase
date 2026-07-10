package com.example.dao;

import com.example.beans.Product;

import java.util.List;

public interface ProductDAO {
    //Получение списка всех товаров
    List<Product> getAllProducts();

    //Получение списка товаров по категории
    List<Product> getProductsByCategoryId(int categoryId);

    //Получение товара по id
    Product getProductById(int productId);
}

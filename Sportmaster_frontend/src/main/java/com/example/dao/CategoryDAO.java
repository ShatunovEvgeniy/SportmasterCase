package com.example.dao;

import com.example.beans.Category;

import java.util.List;

public interface CategoryDAO {
    //Просмотр всех категорий
    List<Category> getAllCategories();

    //Получение категории по id
    Category getCategoryById(int categoryId);
}

package com.example.dao.Impl;

import com.example.beans.Category;
import com.example.dao.CategoryDAO;
import com.example.util.DatabaseConnection;

import java.sql.*;
import java.util.ArrayList;
import java.util.List;

public class CategoryDaoImpl implements CategoryDAO {
    //Просмотр всех категорий
    @Override
    public List<Category> getAllCategories() {
        List<Category> categories = new ArrayList<>();
        String sql = "SELECT * FROM categories";
        try(Connection connection = DatabaseConnection.getConnection();
            PreparedStatement prSt = connection.prepareStatement(sql);
            ResultSet rs = prSt.executeQuery()){
            while (rs.next()){
                Category category = new Category();
                category.setId(rs.getInt("id"));
                category.setName(rs.getString("name"));
                categories.add(category);
            }
        } catch (SQLException e){
            e.printStackTrace();
        }
        return categories;
    }

    //Получение категории по id
    @Override
    public Category getCategoryById(int categoryId){
        String sql = "SELECT * FROM categories WHERE id = ?";
        try(Connection connection = DatabaseConnection.getConnection();
            PreparedStatement prSt = connection.prepareStatement(sql)){
            prSt.setInt(1, categoryId);
            ResultSet rs = prSt.executeQuery();
            if (rs.next()){
                Category category = new Category();
                category.setId(rs.getInt("id"));
                category.setName(rs.getString("name"));
                return category;
            }
        } catch (SQLException e){
            e.printStackTrace();
        }
        return null;
    }
}
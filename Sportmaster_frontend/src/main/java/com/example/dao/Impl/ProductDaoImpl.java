package com.example.dao.Impl;

import com.example.beans.Product;
import com.example.dao.ProductDAO;
import com.example.util.DatabaseConnection;

import java.sql.Connection;
import java.sql.PreparedStatement;
import java.sql.ResultSet;
import java.sql.SQLException;
import java.util.ArrayList;
import java.util.List;

public class ProductDaoImpl implements ProductDAO {
    //Получение списка всех товаров
    @Override
    public List<Product> getAllProducts(){
        List<Product> products = new ArrayList<>();
        String sql = "SELECT * FROM products";
        try(Connection connection = DatabaseConnection.getConnection();
            PreparedStatement prSt = connection.prepareStatement(sql);
            ResultSet rs = prSt.executeQuery()){
            while (rs.next()){
                Product product = new Product();
                product.setId(rs.getInt("id"));
                product.setName(rs.getString("name"));
                product.setDescription(rs.getString("description"));
                product.setPrice(rs.getDouble("price"));
                product.setCategoryId(rs.getInt("category_id"));
                product.setModelId((Integer) rs.getObject("model_id"));
                products.add(product);
            }
        } catch (SQLException e){
            e.printStackTrace();
        }
        return products;
    }

    //Получение списка товаров по категории
    @Override
    public List<Product> getProductsByCategoryId(int categoryId){
        List<Product> productsByCategory = new ArrayList<>();
        String sql = "SELECT * FROM products WHERE category_id = ?";
        try (Connection connection = DatabaseConnection.getConnection();
            PreparedStatement prSt = connection.prepareStatement(sql)){
            prSt.setInt(1, categoryId);
            ResultSet rs = prSt.executeQuery();
            while (rs.next()){
                Product product = new Product();
                product.setId(rs.getInt("id"));
                product.setName(rs.getString("name"));
                product.setDescription(rs.getString("description"));
                product.setPrice(rs.getDouble("price"));
                product.setCategoryId(rs.getInt("category_id"));
                product.setModelId((Integer) rs.getObject("model_id"));
                productsByCategory.add(product);
            }

        } catch (SQLException e){
            e.printStackTrace();
        }
        return productsByCategory;
    }

    //Получение товара по id
    @Override
    public Product getProductById(int productId){
        String sql = "SELECT * FROM products WHERE id = ?";
        try(Connection connection = DatabaseConnection.getConnection();
            PreparedStatement prSt = connection.prepareStatement(sql)){
            prSt.setInt(1, productId);
            ResultSet rs = prSt.executeQuery();
            if (rs.next()){
                Product product = new Product();
                product.setId(rs.getInt("id"));
                product.setName(rs.getString("name"));
                product.setDescription(rs.getString("description"));
                product.setPrice(rs.getDouble("price"));
                product.setCategoryId(rs.getInt("category_id"));
                product.setModelId((Integer) rs.getObject("model_id"));
                return product;
            }
        }catch (SQLException e){
            e.printStackTrace();
        }
        return null;
    }
}

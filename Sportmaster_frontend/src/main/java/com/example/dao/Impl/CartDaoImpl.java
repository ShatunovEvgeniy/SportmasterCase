package com.example.dao.Impl;

import com.example.beans.Cart;
import com.example.beans.Product;
import com.example.dao.CartDAO;
import com.example.util.DatabaseConnection;
import org.w3c.dom.CDATASection;

import java.sql.Connection;
import java.sql.PreparedStatement;
import java.sql.ResultSet;
import java.sql.SQLException;
import java.util.ArrayList;
import java.util.List;

public class CartDaoImpl implements CartDAO {
    //Добавление продукта в корзину
    @Override
    public boolean addToCart(Cart cartItem){
        //Лежит ли товар уже в корзине?
        String checkingSql = "SELECT quantity FROM cart WHERE user_id = ? AND product_id = ?";
        //Не лежит - добавляем 1 шт по умолчанию
        String firstAddSql = "INSERT INTO cart (user_id, product_id, quantity) VALUES (?, ?, 1)";
        //Лежит - добавляем + 1
        String notNewAdd = "UPDATE cart SET quantity = quantity + 1 WHERE user_id = ? AND product_id = ?";
        try(Connection connection = DatabaseConnection.getConnection()){
            PreparedStatement CheckingPrSt = connection.prepareStatement(checkingSql);
            CheckingPrSt.setInt(1, cartItem.getUserId());
            CheckingPrSt.setInt(2, cartItem.getProductId());
            ResultSet rs = CheckingPrSt.executeQuery();

            if (rs.next()){
                PreparedStatement notNewPrSt = connection.prepareStatement(notNewAdd);
                notNewPrSt.setInt(1, cartItem.getUserId());
                notNewPrSt.setInt(2, cartItem.getProductId());
                notNewPrSt.executeUpdate();

            }else {
                PreparedStatement firstAddPrSt = connection.prepareStatement(firstAddSql);
                firstAddPrSt.setInt(1, cartItem.getUserId());
                firstAddPrSt.setInt(2, cartItem.getProductId());
                firstAddPrSt.executeUpdate();
            }
            return true;
        }catch (SQLException e){
            e.printStackTrace();
            return false;
        }
    }

    //Обновление товара в корзине
    @Override
    public boolean updateCartItem (int userId, int productId, int quantity){
        String sql = "UPDATE cart SET quantity = ? WHERE user_id = ? AND product_id = ?";
        try(Connection connection = DatabaseConnection.getConnection();
            PreparedStatement prSt = connection.prepareStatement(sql)){
            prSt.setInt(1, quantity);
            prSt.setInt(2, userId);
            prSt.setInt(3, productId);
            prSt.executeUpdate();
            return true;
        }catch (SQLException e){
            e.printStackTrace();
            return false;
        }
    }

    //Удаление товара из корзины
    @Override
    public boolean deleteFromCart (int userId, int productId){
        String sql = "DELETE FROM cart WHERE user_id = ? AND product_id = ?";
        try(Connection connection = DatabaseConnection.getConnection();
            PreparedStatement prSt = connection.prepareStatement(sql)){
            prSt.setInt(1, userId);
            prSt.setInt(2, productId);
            prSt.executeUpdate();
            return true;
        }catch (SQLException e){
            e.printStackTrace();
            return false;
        }
    }

    //Просмотр корзины пользователя (по его id)
    @Override
    public List<Cart> getCartByUserId(int userId){
        List<Cart> allCart = new ArrayList<>();
        String sql = "SELECT c.*, pr.category_id, pr.name, pr.description, pr.price\n" +
                "FROM cart c LEFT JOIN products pr ON c.product_id = pr.id " +
                "WHERE c.user_id = ? ORDER BY pr.name\n";
        try(Connection connection = DatabaseConnection.getConnection();
            PreparedStatement prSt = connection.prepareStatement(sql)){
            prSt.setInt(1, userId);
            ResultSet rs = prSt.executeQuery();
            while (rs.next()){
                Cart cartItem = new Cart();
                cartItem.setUserId(rs.getInt("user_id"));
                cartItem.setProductId(rs.getInt("product_id"));
                cartItem.setQuantity(rs.getInt("quantity"));

                Product product = new Product();
                product.setId(rs.getInt("product_id"));
                product.setName(rs.getString("name"));
                product.setDescription(rs.getString("description"));
                product.setPrice(rs.getDouble("price"));
                product.setCategoryId(rs.getInt("category_id"));
                cartItem.setProduct(product);
                allCart.add(cartItem);
            }
        } catch (SQLException e){
            e.printStackTrace();
        }
        return allCart;
    }

    //Очистка корзины
    @Override
    public boolean clearCart(int userId){
        String sql = "DELETE FROM cart WHERE user_id = ?";
        try(Connection connection = DatabaseConnection.getConnection();
            PreparedStatement prSt = connection.prepareStatement(sql)){
            prSt.setInt(1, userId);
            prSt.executeUpdate();
            return true;
        }catch (SQLException e){
            e.printStackTrace();
            return false;
        }
    }
}

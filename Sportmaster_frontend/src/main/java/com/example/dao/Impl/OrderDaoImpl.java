package com.example.dao.Impl;

import com.example.beans.Cart;
import com.example.beans.Order;
import com.example.beans.OrderItem;
import com.example.beans.Product;
import com.example.dao.OrderDAO;
import com.example.util.DatabaseConnection;

import java.sql.*;
import java.util.ArrayList;
import java.util.List;

public class OrderDaoImpl implements OrderDAO {
    //Создание заказа
    @Override
    public boolean createOrder(Order order, List<Cart> allCart){
        String sql = "INSERT INTO orders (user_id, status) VALUES (?, ?)";
        try(Connection connection = DatabaseConnection.getConnection();
            PreparedStatement prSt = connection.prepareStatement(sql, Statement.RETURN_GENERATED_KEYS)){
            prSt.setInt(1, order.getUserId());
            prSt.setString(2, order.getStatus());
            prSt.executeUpdate();

            ResultSet rs = prSt.getGeneratedKeys();
            if (rs.next()) {
                int orderId = rs.getInt(1);
                for (Cart item : allCart){
                    String addToOrderSql = "INSERT INTO order_items (order_id, product_id, quantity, price) VALUES (?, ?, ?, ?)";
                    try(PreparedStatement prStOI = connection.prepareStatement(addToOrderSql)){
                        prStOI.setInt(1, orderId);
                        prStOI.setInt(2, item.getProductId());
                        prStOI.setInt(3, item.getQuantity());
                        prStOI.setDouble(4, item.getProduct().getPrice());
                        prStOI.executeUpdate();
                    }
                }
                return true;
            }
        }catch (SQLException e) {
            e.printStackTrace();
        }
        return false;
    }

    //Просмотр общей информации о конкретном заказе
    @Override
    public Order getOrderByOrderId(int orderId){
        String sql = "SELECT o.*,\n" +
                "\tSUM(oi.price * oi.quantity) AS total\n" +
                "FROM orders o LEFT JOIN order_items oi ON o.id = oi.order_id\n" +
                "WHERE o.id = ? GROUP BY o.id";
        try(Connection connection = DatabaseConnection.getConnection();
            PreparedStatement prSt = connection.prepareStatement(sql)){
            prSt.setInt(1, orderId);
            ResultSet rs = prSt.executeQuery();
            if (rs.next()){
                Order order = new Order();
                order.setId(rs.getInt("id"));
                order.setUserId(rs.getInt("user_id"));
                order.setOrderDate(rs.getTimestamp("order_date"));
                order.setStatus(rs.getString("status"));
                order.setTotal(rs.getDouble("total"));
                return order;
            }
        }catch (SQLException e) {
            e.printStackTrace();
        }
        return null;
    }

    //Просмотр товаров из конкретного заказа
    @Override
    public List<OrderItem> getOrderItems (int orderId){
        List<OrderItem> allItems = new ArrayList<>();
        String sql = "SELECT oi.*, pr.name, pr.description, pr.category_id \n" +
                "FROM order_items oi LEFT JOIN products pr ON oi.product_id = pr.id\n" +
                "WHERE oi.order_id = ?";
        try(Connection connection = DatabaseConnection.getConnection();
            PreparedStatement prSt = connection.prepareStatement(sql)){
            prSt.setInt(1, orderId);
            ResultSet rs = prSt.executeQuery();
            if (rs.next()){
                OrderItem item = new OrderItem();
                item.setOrderId(rs.getInt("order_id"));
                item.setProductId(rs.getInt("product_id"));
                item.setQuantity(rs.getInt("quantity"));
                item.setPrice(rs.getDouble("price"));

                Product product = new Product();
                product.setId(rs.getInt("product_id"));
                product.setName(rs.getString("name"));
                product.setDescription(rs.getString("description"));
                product.setCategoryId(rs.getInt("category_id"));
                item.setProduct(product);
                allItems.add(item);
            }
        }catch (SQLException e) {
            e.printStackTrace();
        }
        return allItems;
    }

    //Просмотр истории заказов пользователя
    @Override
    public List<Order> getOrderHistoryByUserId(int userId){
        List<Order> ordersHistory = new ArrayList<>();
        String sql = "SELECT orders.*, \n" +
                "\tSUM(quantity * order_items.price) as total\n" +
                "FROM orders LEFT JOIN order_items ON orders.id = order_items.order_id \n" +
                "WHERE orders.user_id = ? GROUP BY orders.id ORDER BY orders.order_date DESC";
        try(Connection connection = DatabaseConnection.getConnection();
            PreparedStatement prSt = connection.prepareStatement(sql)){
            prSt.setInt(1, userId);
            ResultSet rs = prSt.executeQuery();
            while (rs.next()){
                Order order = new Order();
                order.setId(rs.getInt("id"));
                order.setUserId(rs.getInt("user_id"));
                order.setOrderDate(rs.getTimestamp("order_date"));
                order.setStatus(rs.getString("status"));
                order.setTotal(rs.getDouble("total"));
                ordersHistory.add(order);
            }
        }catch (SQLException e){
            e.printStackTrace();
        }
        return ordersHistory;
    }
}

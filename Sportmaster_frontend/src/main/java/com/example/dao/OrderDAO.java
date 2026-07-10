package com.example.dao;

import com.example.beans.Cart;
import com.example.beans.Order;
import com.example.beans.OrderItem;

import java.util.List;

public interface OrderDAO {
    //Создание заказа
    boolean createOrder(Order order, List<Cart> allCart);

    //Просмотр общей информации о конкретном заказе
    Order getOrderByOrderId(int orderId);

    //Просмотр товаров из конкретного заказа
    List<OrderItem> getOrderItems (int orderId);

    //Просмотр истории заказов пользователя
    List<Order> getOrderHistoryByUserId(int userId);
}

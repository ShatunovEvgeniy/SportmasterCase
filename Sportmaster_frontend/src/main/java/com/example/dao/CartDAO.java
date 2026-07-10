package com.example.dao;

import com.example.beans.Cart;

import java.util.List;

public interface CartDAO {
    //Добавление продукта в корзину
    boolean addToCart(Cart cartItem);

    //Обновление товара в корзине
    boolean updateCartItem (int userId, int productId, int quantity);

    //Удаление товара из корзины
    boolean deleteFromCart (int userId, int productId);

    //Просмотр корзины пользователя (по его id)
    List<Cart> getCartByUserId(int userId);

    //Очистка корзины
    boolean clearCart(int userId);

}

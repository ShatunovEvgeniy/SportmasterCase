package com.example.dao;

import com.example.beans.User;

public interface UserDAO {
    //Регистрация пользователя
    boolean register(User user);
    //Поиск пользователя по уникальному email
    User getByEmail (String email);

}

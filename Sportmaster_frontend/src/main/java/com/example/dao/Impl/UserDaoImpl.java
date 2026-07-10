package com.example.dao.Impl;

import com.example.beans.User;
import com.example.dao.UserDAO;
import com.example.util.DatabaseConnection;

import java.sql.*;

public class UserDaoImpl implements UserDAO {


    //Регистрация пользователя
    @Override
    public boolean register(User user){
        String sql = "INSERT INTO users (name, email, password, role) VALUES (?, ?, ?, ?)";
        try(Connection connection = DatabaseConnection.getConnection();
            PreparedStatement prSt = connection.prepareStatement(sql)){

            prSt.setString(1, user.getName());
            prSt.setString(2, user.getEmail());
            prSt.setString(3, user.getPassword());
            prSt.setString(4, "USER");
            prSt.executeUpdate();
            return true;
        } catch (SQLException e){
            e.printStackTrace();
            return false;
        }
    }

    //Получение пользователя по уникальному email
    @Override
    public User getByEmail(String email){
        String sql = "SELECT * FROM users WHERE email = ?";
        try (Connection connection = DatabaseConnection.getConnection();
             PreparedStatement prSt = connection.prepareStatement(sql)){
            prSt.setString(1, email);
            ResultSet rs = prSt.executeQuery();
            if (rs.next()){
                User user = new User();
                user.setId(rs.getInt("id"));
                user.setName(rs.getString("name"));
                user.setEmail(rs.getString("email"));
                user.setPassword(rs.getString("password"));
                user.setRole(rs.getString("role"));
                return user;
            }
        } catch (SQLException e){
            e.printStackTrace();
        }
        return null;
    }
}
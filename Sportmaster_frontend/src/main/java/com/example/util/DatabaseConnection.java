package com.example.util;

import java.sql.Connection;
import java.sql.DriverManager;
import java.sql.SQLException;

public class DatabaseConnection {
    // Хост параметризован через переменную окружения DB_HOST (нужно в Docker, где
    // MySQL живёт в отдельном контейнере под именем "mysql", а не "localhost").
    // Без переменной — прежнее поведение "localhost", как при обычном запуске.
    private static final String DB_HOST = env("DB_HOST", "localhost");

    private final static String JDBC_URL = "jdbc:mysql://" + DB_HOST + ":3306/online_shop";
    private static final String JDBC_USERNAME = env("ONLINE_SHOP_DB_USER", "root");
    private static final String JDBC_PASSWORD = env("ONLINE_SHOP_DB_PASSWORD", "mipt!mySQL8045");
    private static Connection connection = null;

    // Вторая БД: заполняется Python-пайплайном (отзывы, рейтинг, AI-сводка).
    // Java-часть только читает из неё, ничего не пишет.
    private final static String SPORTMASTER_JDBC_URL = "jdbc:mysql://" + DB_HOST + ":3306/sportmaster";
    private static final String SPORTMASTER_USERNAME = env("SPORTMASTER_DB_USER", "sportmaster");
    private static final String SPORTMASTER_PASSWORD = env("SPORTMASTER_DB_PASSWORD", "sportmaster123");
    private static Connection sportmasterConnection = null;

    private static String env(String name, String fallback) {
        String value = System.getenv(name);
        return (value == null || value.isEmpty()) ? fallback : value;
    }

    public static Connection getConnection() throws SQLException{
        if (connection == null || connection.isClosed()){
           try{
               Class.forName("com.mysql.cj.jdbc.Driver");
               connection = DriverManager.getConnection(JDBC_URL, JDBC_USERNAME, JDBC_PASSWORD);
           }catch (ClassNotFoundException e){
               throw new SQLException("MySQL Driver is not found");
           }
        } return connection;
    }

    public static Connection getSportmasterConnection() throws SQLException{
        if (sportmasterConnection == null || sportmasterConnection.isClosed()){
           try{
               Class.forName("com.mysql.cj.jdbc.Driver");
               sportmasterConnection = DriverManager.getConnection(
                       SPORTMASTER_JDBC_URL, SPORTMASTER_USERNAME, SPORTMASTER_PASSWORD);
           }catch (ClassNotFoundException e){
               throw new SQLException("MySQL Driver is not found");
           }
        } return sportmasterConnection;
    }
}



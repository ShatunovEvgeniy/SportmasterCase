package com.example.beans;

public class Category {
    private int id;
    private String name;

    //Конструкторы
    public Category() {}
    public Category (int id, String name){
        this.id = id;
        this.name = name;
    }

    //Геттеры и сеттеры
    public int getId() {
        return id;
    }
    public void setId(int id) {
        this.id = id;
    }

    public String getName(){
        return name;
    }
    public void setName(String name) {
        this.name = name;
    }
}

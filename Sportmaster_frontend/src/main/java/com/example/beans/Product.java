package com.example.beans;

public class Product {
    private int id;
    private String name;
    private String description;
    private double price;
    private int categoryId;

    // Связь с товаром в БД Python-пайплайна (sportmaster.products.model_id).
    // Null, если у товара ещё нет привязки к реальным отзывам/AI-сводке.
    private Integer modelId;

    // Денормализованные данные из sportmaster (для карточек в каталоге), читаются отдельным DAO
    private double rating;
    private int reviewCount;

    //Конструкторы
    public Product() {}
    public Product (int id, String name, String description, double price, int categoryId){
        this.id = id;
        this.name = name;
        this.description = description;
        this.price = price;
        this.categoryId = categoryId;
    }

    //Геттеры и сеттеры
    public int getId() {
        return id;
    }
    public void setId(int id) {
        this.id = id;
    }

    public String getName() {
        return name;
    }
    public void setName(String name) {
        this.name = name;
    }

    public String getDescription() {
        return description;
    }
    public void setDescription(String description) {
        this.description = description;
    }

    public double getPrice() {
        return price;
    }
    public void setPrice(double price) {
        this.price = price;
    }

    public int getCategoryId() {
        return categoryId;
    }
    public void setCategoryId(int categoryId) {
        this.categoryId = categoryId;
    }

    public Integer getModelId() {
        return modelId;
    }
    public void setModelId(Integer modelId) {
        this.modelId = modelId;
    }

    public double getRating() {
        return rating;
    }
    public void setRating(double rating) {
        this.rating = rating;
    }

    public int getReviewCount() {
        return reviewCount;
    }
    public void setReviewCount(int reviewCount) {
        this.reviewCount = reviewCount;
    }

    // Целое число звёзд для JSTL forEach (округление рейтинга)
    public int getStars() {
        return (int) Math.round(rating);
    }

    // Заполненность звёздной шкалы в процентах (4.8 из 5 -> 96%) для плавной заливки звёзд
    public double getRatingPercent() {
        return Math.max(0, Math.min(100, rating / 5.0 * 100));
    }

    // Цена с разделителем разрядов и без копеек, напр. "8 649" (обходит нестабильный fmt:formatNumber)
    public String getPriceFormatted() {
        return String.format("%,.0f", price).replace(',', ' ');
    }
}

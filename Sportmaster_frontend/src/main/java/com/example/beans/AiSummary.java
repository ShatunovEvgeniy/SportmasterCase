package com.example.beans;

import java.util.List;

// Данные из sportmaster (Python-пайплайн): рейтинг, AI-сводка, аспекты, цитаты, отзывы.
// Java только читает эти данные напрямую из БД; запись (лайк/дизлайк, новый отзыв,
// перерасчёт сводки) идёт через FastAPI на стороне Python.
public class AiSummary {
    private int modelId;
    private double rating;
    private int reviewCount;
    private String aiSummary;
    private int likes;
    private int dislikes;
    private List<AspectStat> pros;
    private List<AspectStat> cons;
    private List<QuoteDto> quotes;
    private List<ReviewDto> reviews;

    public int getModelId() { return modelId; }
    public void setModelId(int modelId) { this.modelId = modelId; }

    public double getRating() { return rating; }
    public void setRating(double rating) { this.rating = rating; }

    public int getReviewCount() { return reviewCount; }
    public void setReviewCount(int reviewCount) { this.reviewCount = reviewCount; }

    public String getAiSummary() { return aiSummary; }
    public void setAiSummary(String aiSummary) { this.aiSummary = aiSummary; }

    public int getLikes() { return likes; }
    public void setLikes(int likes) { this.likes = likes; }

    public int getDislikes() { return dislikes; }
    public void setDislikes(int dislikes) { this.dislikes = dislikes; }

    public List<AspectStat> getPros() { return pros; }
    public void setPros(List<AspectStat> pros) { this.pros = pros; }

    public List<AspectStat> getCons() { return cons; }
    public void setCons(List<AspectStat> cons) { this.cons = cons; }

    public List<QuoteDto> getQuotes() { return quotes; }
    public void setQuotes(List<QuoteDto> quotes) { this.quotes = quotes; }

    public List<ReviewDto> getReviews() { return reviews; }
    public void setReviews(List<ReviewDto> reviews) { this.reviews = reviews; }

    // Целое число звёзд для JSTL forEach (округление рейтинга)
    public int getStars() {
        return (int) Math.round(rating);
    }

    // Заполненность звёздной шкалы в процентах (4.8 из 5 -> 96%) для плавной заливки звёзд
    public double getRatingPercent() {
        return Math.max(0, Math.min(100, rating / 5.0 * 100));
    }

    // Формат "4,3" вместо "4.3" для отображения (русская локаль)
    public String getRatingFormatted() {
        return String.format("%.1f", rating).replace('.', ',');
    }
}

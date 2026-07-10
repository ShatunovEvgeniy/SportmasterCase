package com.example.beans;

public class QuoteDto {
    private String text;
    private int reviewId;
    private String sentiment;

    public QuoteDto() {}
    public QuoteDto(String text, int reviewId, String sentiment) {
        this.text = text;
        this.reviewId = reviewId;
        this.sentiment = sentiment;
    }

    public String getText() { return text; }
    public void setText(String text) { this.text = text; }

    public int getReviewId() { return reviewId; }
    public void setReviewId(int reviewId) { this.reviewId = reviewId; }

    public String getSentiment() { return sentiment; }
    public void setSentiment(String sentiment) { this.sentiment = sentiment; }
}

package com.example.beans;

public class ReviewDto {
    private int reviewId;
    private String text;
    private Double rating;
    private String reviewerName;
    private String pros;
    private String cons;

    public ReviewDto() {}
    public ReviewDto(int reviewId, String text, Double rating, String reviewerName, String pros, String cons) {
        this.reviewId = reviewId;
        this.text = text;
        this.rating = rating;
        this.reviewerName = reviewerName;
        this.pros = pros;
        this.cons = cons;
    }

    public int getReviewId() { return reviewId; }
    public void setReviewId(int reviewId) { this.reviewId = reviewId; }

    public String getText() { return text; }
    public void setText(String text) { this.text = text; }

    public Double getRating() { return rating; }
    public void setRating(Double rating) { this.rating = rating; }

    public String getReviewerName() { return reviewerName; }
    public void setReviewerName(String reviewerName) { this.reviewerName = reviewerName; }

    public String getPros() { return pros; }
    public void setPros(String pros) { this.pros = pros; }

    public String getCons() { return cons; }
    public void setCons(String cons) { this.cons = cons; }

    // Целое число звёзд для JSTL forEach (округление рейтинга)
    public int getStars() {
        return rating == null ? 0 : (int) Math.round(rating);
    }
}

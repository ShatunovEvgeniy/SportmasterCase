package com.example.beans;

import java.util.List;
import java.util.stream.Collectors;

public class AspectStat {
    private int id;
    private String aspect;
    private int count;
    private List<Integer> reviewIds;

    public AspectStat() {}
    public AspectStat(int id, String aspect, int count) {
        this.id = id;
        this.aspect = aspect;
        this.count = count;
    }

    public int getId() { return id; }
    public void setId(int id) { this.id = id; }

    public String getAspect() { return aspect; }
    public void setAspect(String aspect) { this.aspect = aspect; }

    public int getCount() { return count; }
    public void setCount(int count) { this.count = count; }

    public List<Integer> getReviewIds() { return reviewIds; }
    public void setReviewIds(List<Integer> reviewIds) { this.reviewIds = reviewIds; }

    // Список id отзывов через запятую — для data-ids в JS-фильтре на странице товара
    public String getReviewIdsCsv() {
        if (reviewIds == null || reviewIds.isEmpty()) return "";
        return reviewIds.stream().map(String::valueOf).collect(Collectors.joining(","));
    }
}

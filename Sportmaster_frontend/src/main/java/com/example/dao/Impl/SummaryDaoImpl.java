package com.example.dao.Impl;

import com.example.beans.AiSummary;
import com.example.beans.AspectStat;
import com.example.beans.Product;
import com.example.beans.QuoteDto;
import com.example.beans.ReviewDto;
import com.example.dao.SummaryDAO;
import com.example.util.DatabaseConnection;

import java.sql.Connection;
import java.sql.PreparedStatement;
import java.sql.ResultSet;
import java.sql.SQLException;
import java.util.ArrayList;
import java.util.List;

// Читает данные, которые пишет Python-пайплайн (БД sportmaster): рейтинг, отзывы,
// AI-сводку, аспекты и цитаты. Только чтение — запись идёт через FastAPI на стороне Python.
public class SummaryDaoImpl implements SummaryDAO {

    private static final int MAX_REVIEWS = 30;
    private static final int MAX_QUOTES = 6;

    @Override
    public AiSummary getSummary(Integer modelId) {
        if (modelId == null) return null;

        String productSql = "SELECT rating, ai_summary, ai_summary_likes, ai_summary_dislikes " +
                "FROM products WHERE model_id = ?";

        try (Connection connection = DatabaseConnection.getSportmasterConnection();
             PreparedStatement prSt = connection.prepareStatement(productSql)) {
            prSt.setInt(1, modelId);
            ResultSet rs = prSt.executeQuery();
            if (!rs.next()) {
                return null;
            }

            AiSummary summary = new AiSummary();
            summary.setModelId(modelId);
            summary.setRating(rs.getDouble("rating"));
            summary.setAiSummary(rs.getString("ai_summary"));
            summary.setLikes(rs.getInt("ai_summary_likes"));
            summary.setDislikes(rs.getInt("ai_summary_dislikes"));

            summary.setReviewCount(countReviews(connection, modelId));
            summary.setPros(loadAspects(connection, modelId, "product_final_advantages"));
            summary.setCons(loadAspects(connection, modelId, "product_final_disadvantages"));
            summary.setQuotes(loadQuotes(connection, modelId));
            summary.setReviews(loadReviews(connection, modelId));

            return summary;
        } catch (SQLException e) {
            e.printStackTrace();
            return null;
        }
    }

    @Override
    public void fillRatingInfo(Product product) {
        if (product.getModelId() == null) return;

        String sql = "SELECT rating FROM products WHERE model_id = ?";
        try (Connection connection = DatabaseConnection.getSportmasterConnection();
             PreparedStatement prSt = connection.prepareStatement(sql)) {
            prSt.setInt(1, product.getModelId());
            ResultSet rs = prSt.executeQuery();
            if (rs.next()) {
                product.setRating(rs.getDouble("rating"));
                product.setReviewCount(countReviews(connection, product.getModelId()));
            }
        } catch (SQLException e) {
            e.printStackTrace();
        }
    }

    private int countReviews(Connection connection, int modelId) throws SQLException {
        String sql = "SELECT COUNT(*) AS c FROM reviews WHERE model_id = ?";
        try (PreparedStatement prSt = connection.prepareStatement(sql)) {
            prSt.setInt(1, modelId);
            ResultSet rs = prSt.executeQuery();
            return rs.next() ? rs.getInt("c") : 0;
        }
    }

    private List<AspectStat> loadAspects(Connection connection, int modelId, String linkTable) throws SQLException {
        List<AspectStat> aspects = new ArrayList<>();
        String sql = "SELECT a.id, a.aspect, a.count FROM aspects a " +
                "JOIN " + linkTable + " l ON a.id = l.aspect_id " +
                "WHERE l.model_id = ? ORDER BY a.count DESC";
        try (PreparedStatement prSt = connection.prepareStatement(sql)) {
            prSt.setInt(1, modelId);
            ResultSet rs = prSt.executeQuery();
            while (rs.next()) {
                AspectStat aspect = new AspectStat(rs.getInt("id"), rs.getString("aspect"), rs.getInt("count"));
                aspect.setReviewIds(loadAspectReviewIds(connection, aspect.getId()));
                aspects.add(aspect);
            }
        }
        return aspects;
    }

    private List<Integer> loadAspectReviewIds(Connection connection, int aspectId) throws SQLException {
        List<Integer> reviewIds = new ArrayList<>();
        String sql = "SELECT review_id FROM aspect_reviews WHERE aspect_id = ?";
        try (PreparedStatement prSt = connection.prepareStatement(sql)) {
            prSt.setInt(1, aspectId);
            ResultSet rs = prSt.executeQuery();
            while (rs.next()) {
                reviewIds.add(rs.getInt("review_id"));
            }
        }
        return reviewIds;
    }

    private List<QuoteDto> loadQuotes(Connection connection, int modelId) throws SQLException {
        List<QuoteDto> quotes = new ArrayList<>();
        String sql = "SELECT text, review_id, sentiment FROM quotes WHERE model_id = ? ORDER BY id LIMIT " + MAX_QUOTES;
        try (PreparedStatement prSt = connection.prepareStatement(sql)) {
            prSt.setInt(1, modelId);
            ResultSet rs = prSt.executeQuery();
            while (rs.next()) {
                quotes.add(new QuoteDto(rs.getString("text"), rs.getInt("review_id"), rs.getString("sentiment")));
            }
        }
        return quotes;
    }

    private List<ReviewDto> loadReviews(Connection connection, int modelId) throws SQLException {
        List<ReviewDto> reviews = new ArrayList<>();
        String sql = "SELECT review_id, general_review, review_rating, reviewer_name, pros, cons FROM reviews " +
                "WHERE model_id = ? AND general_review <> '' ORDER BY review_id DESC LIMIT " + MAX_REVIEWS;
        try (PreparedStatement prSt = connection.prepareStatement(sql)) {
            prSt.setInt(1, modelId);
            ResultSet rs = prSt.executeQuery();
            while (rs.next()) {
                Object ratingObj = rs.getObject("review_rating");
                Double rating = ratingObj == null ? null : ((Number) ratingObj).doubleValue();
                reviews.add(new ReviewDto(rs.getInt("review_id"), rs.getString("general_review"), rating,
                        rs.getString("reviewer_name"), rs.getString("pros"), rs.getString("cons")));
            }
        }
        return reviews;
    }
}

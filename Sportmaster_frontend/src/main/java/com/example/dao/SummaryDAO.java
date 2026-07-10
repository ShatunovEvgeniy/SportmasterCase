package com.example.dao;

import com.example.beans.AiSummary;

public interface SummaryDAO {
    // Полная сводка по товару (рейтинг, AI-summary, аспекты, цитаты, отзывы) для страницы товара.
    // Возвращает null, если товар ещё не привязан к model_id или данных по нему пока нет.
    AiSummary getSummary(Integer modelId);

    // Лёгкий вариант (только рейтинг + кол-во отзывов) для карточек в каталоге.
    void fillRatingInfo(com.example.beans.Product product);
}

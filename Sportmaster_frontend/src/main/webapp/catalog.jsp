<%@ page language="java" contentType="text/html; charset=UTF-8" %>
<%@ taglib uri="jakarta.tags.core" prefix="c" %>
<%@ taglib uri="jakarta.tags.fmt" prefix="fmt" %>
<!DOCTYPE html>
<html lang="ru">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Каталог товаров</title>
    <link rel="icon" type="image/x-icon" href="${pageContext.request.contextPath}/favicon.ico">
    <link rel="icon" type="image/png" sizes="32x32" href="${pageContext.request.contextPath}/favicon-32.png">
    <link rel="stylesheet" href="${pageContext.request.contextPath}/style/style.css?v=<%= System.currentTimeMillis() %>">
</head>
<body class="catalog-page">
    <jsp:include page="/WEB-INF/const/catalog_header.jsp"/>

    <main class="cat-main">
        <h1 class="cat-title">Каталог товаров</h1>

        <div class="catalog">
            <%-- Товары из БД online_shop; рейтинг и кол-во отзывов сервлет уже подтянул
                 из sportmaster через SummaryDAO (product.rating / product.reviewCount). --%>
            <c:forEach var="p" items="${products}">
                <a class="pcard" href="${pageContext.request.contextPath}/catalog/product_info?id=${p.id}">
                    <div class="pcard-img"><img src="${pageContext.request.contextPath}/images/product${p.id}.jpg" alt="${p.name}"></div>
                    <div class="pcard-price">${p.priceFormatted} ₽</div>
                    <div class="pcard-name">${p.name}</div>
                    <c:if test="${p.reviewCount > 0}">
                        <div class="pcard-rate">
                            <span class="stars stars-frac">
                                <span class="stars-bg">★★★★★</span>
                                <span class="stars-fg" style="width:${p.ratingPercent}%">★★★★★</span>
                            </span>
                            <span class="rc">${p.reviewCount}</span>
                        </div>
                    </c:if>
                </a>
            </c:forEach>
        </div>
    </main>

    <jsp:include page="/WEB-INF/const/footer.jsp"/>
</body>
</html>

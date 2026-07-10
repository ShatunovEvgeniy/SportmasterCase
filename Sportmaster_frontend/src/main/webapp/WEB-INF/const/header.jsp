<%@ page contentType="text/html;charset=UTF-8" language="java" %>
<%@ taglib uri="jakarta.tags.core" prefix="c" %>
<%-- Базовый header (без регистрации/входа/корзины). Каталог и «О товаре»
     используют отдельную каталожную шапку catalog_header.jsp. --%>
<header>
    <nav>
        <ul>
            <li><a href="${pageContext.request.contextPath}/sportmaster-case.html">Главная</a></li>
            <li><a href="${pageContext.request.contextPath}/catalog">Каталог</a></li>
        </ul>
    </nav>
</header>

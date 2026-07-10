package com.example.controller;

import com.example.beans.*;
import com.example.dao.CartDAO;
import com.example.dao.Impl.CartDaoImpl;
import com.example.dao.Impl.OrderDaoImpl;
import com.example.dao.OrderDAO;
import jakarta.servlet.ServletException;
import jakarta.servlet.annotation.WebServlet;
import jakarta.servlet.http.HttpServlet;
import jakarta.servlet.http.HttpServletRequest;
import jakarta.servlet.http.HttpServletResponse;
import jakarta.servlet.http.HttpSession;

import java.io.IOException;
import java.util.List;

@WebServlet("/orders/*")
public class OrderServlet extends HttpServlet {
    private OrderDAO orderDao;
    private CartDAO cartDAO;
    @Override
    public void init(){
        orderDao = new OrderDaoImpl();
        cartDAO = new CartDaoImpl();
    }

    @Override
    protected void doGet(HttpServletRequest request, HttpServletResponse response)
        throws IOException, ServletException{
        //Проверка сессии
        HttpSession session = request.getSession(false);
        if (session == null || session.getAttribute("user") == null) {
            response.sendRedirect(request.getContextPath() + "/login.jsp");
            return;
        }
        User user = (User) session.getAttribute("user");

        String currentAction = request.getPathInfo();
        if (currentAction == null){
            currentAction = "";
        }

        switch (currentAction){
            case "/order_info":
                getAllOrderInfo(request, response);
                break;
            case "":
                getHistoryOfOrders(request, response, user);
                break;
            default:
                response.sendError(HttpServletResponse.SC_NOT_FOUND);
        }
    }

    @Override
    protected void doPost(HttpServletRequest request, HttpServletResponse response)
            throws IOException{
        //Проверка сессии
        HttpSession session = request.getSession(false);
        if (session == null || session.getAttribute("user") == null) {
            response.sendRedirect(request.getContextPath() + "/login.jsp");
            return;
        }
        User user = (User) session.getAttribute("user");

        String currentAction = request.getPathInfo();
        if (currentAction == null){
            currentAction = "";
        }

        switch (currentAction){
            case "/create":
                createAnOrder(request, response, user);
                break;
            default:
                response.sendError(HttpServletResponse.SC_NOT_FOUND);
        }
    }

    private void getAllOrderInfo(HttpServletRequest request, HttpServletResponse response)
            throws IOException, ServletException {
        int orderId = Integer.parseInt(request.getParameter("id"));
        Order order = orderDao.getOrderByOrderId(orderId);
        List<OrderItem> orderItems = orderDao.getOrderItems(orderId);
        request.setAttribute("order", order);
        request.setAttribute("orderItems", orderItems);
        request.getRequestDispatcher("/order_info.jsp").forward(request, response);
    }

    private void getHistoryOfOrders(HttpServletRequest request, HttpServletResponse response, User user)
            throws IOException, ServletException {
        List<Order> orders = orderDao.getOrderHistoryByUserId(user.getId());
        request.setAttribute("orders", orders);
        request.getRequestDispatcher("/orders.jsp").forward(request, response);
    }


    private void createAnOrder(HttpServletRequest request, HttpServletResponse response, User user)
            throws IOException {
        List<Cart> allCart = cartDAO.getCartByUserId(user.getId());
        if (allCart.isEmpty()){
            response.sendRedirect(request.getContextPath() + "/cart?error=empty");
            return;
        }
        Order order = new Order();
        order.setUserId(user.getId());
        order.setStatus("ACTIVE");

        //Добавляем в БД
        if (orderDao.createOrder(order, allCart)){
            response.sendRedirect(request.getContextPath() + "/orders");
        } else{
            response.sendRedirect(request.getContextPath() + "/cart?error=1");
        }
    }

}

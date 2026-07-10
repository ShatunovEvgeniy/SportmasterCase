package com.example.controller;

import com.example.beans.Cart;
import com.example.beans.User;
import com.example.dao.CartDAO;
import com.example.dao.Impl.CartDaoImpl;
import jakarta.servlet.ServletException;
import jakarta.servlet.annotation.WebServlet;
import jakarta.servlet.http.HttpServlet;
import jakarta.servlet.http.HttpServletRequest;
import jakarta.servlet.http.HttpServletResponse;
import jakarta.servlet.http.HttpSession;

import java.io.IOException;
import java.util.List;

@WebServlet("/cart/*")
public class CartServlet extends HttpServlet {
    private CartDAO cartDao;

    @Override
    public void init(){
        cartDao = new CartDaoImpl();
    }

    @Override
    protected void doGet(HttpServletRequest request, HttpServletResponse response)
            throws IOException, ServletException {
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
            case "":
                getAllCart(request, response, user);
                break;
            default:
                response.sendError(HttpServletResponse.SC_NOT_FOUND);
        }
    }

    @Override
    protected void doPost(HttpServletRequest request, HttpServletResponse response)
            throws IOException {
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
            case "/add":
                addToCart(request, response, user);
                break;
            case "/delete":
                deleteFromCart(request, response, user);
                break;
            case "/clean":
                cleanAllCart(request, response, user);
                break;
            case "/modify":
                changeQuantity(request, response, user);
                break;
            default:
                response.sendError(HttpServletResponse.SC_NOT_FOUND);
        }
    }

    private void getAllCart(HttpServletRequest request, HttpServletResponse response, User user)
        throws IOException, ServletException{
        List<Cart> allCart = cartDao.getCartByUserId(user.getId());
        double total = 0;
        for (Cart item : allCart){
            total += item.getProduct().getPrice() * item.getQuantity();
        }
        request.setAttribute("allCart", allCart);
        request.setAttribute("total", total);
        request.getRequestDispatcher("/cart.jsp").forward(request, response);
    }

    public void addToCart(HttpServletRequest request, HttpServletResponse response, User user)
            throws IOException{
        int productId = Integer.parseInt(request.getParameter("productId"));
        Cart cartItem = new Cart();
        cartItem.setUserId(user.getId());
        cartItem.setProductId(productId);
        cartItem.setQuantity(1);
        if (cartDao.addToCart(cartItem)){
            response.sendRedirect(request.getContextPath() + "/cart");
        } else{
            response.sendRedirect(request.getContextPath() + "/catalog?error=1");
        }
    }

    public void deleteFromCart(HttpServletRequest request, HttpServletResponse response, User user)
            throws IOException{
        int productId = Integer.parseInt(request.getParameter("productId"));
        if(cartDao.deleteFromCart(user.getId(), productId)){
            response.sendRedirect(request.getContextPath() + "/cart");
        } else{
            response.sendRedirect(request.getContextPath() + "/cart?error=1");
        }
    }

    public void cleanAllCart(HttpServletRequest request, HttpServletResponse response, User user)
            throws IOException{
        if(cartDao.clearCart(user.getId())){
            response.sendRedirect(request.getContextPath() + "/cart");
        } else{
            response.sendRedirect(request.getContextPath() + "/cart?error=1");
        }
    }

    public void changeQuantity(HttpServletRequest request, HttpServletResponse response, User user)
            throws IOException{
        int productId = Integer.parseInt(request.getParameter("productId"));
        int quantity = Integer.parseInt(request.getParameter("quantity"));
        if (cartDao.updateCartItem(user.getId(), productId, quantity)){
            response.sendRedirect(request.getContextPath() + "/cart");
        } else{
            response.sendRedirect(request.getContextPath() + "/cart?error=1");
        }
    }
}

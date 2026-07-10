package com.example.controller;

import com.example.beans.User;
import com.example.dao.Impl.UserDaoImpl;
import com.example.dao.UserDAO;
import com.example.util.SafePasswords;
import jakarta.servlet.annotation.WebServlet;
import jakarta.servlet.http.HttpServlet;
import jakarta.servlet.http.HttpServletRequest;
import jakarta.servlet.http.HttpServletResponse;
import jakarta.servlet.http.HttpSession;

import java.io.IOException;

@WebServlet("/auth/*")
public class AuthServlet extends HttpServlet {

    private UserDAO userDAO;
    @Override
    public void init(){
        userDAO = new UserDaoImpl();
    }

    @Override
    protected void doPost(HttpServletRequest request, HttpServletResponse response)
            throws IOException {
        //Все, что после /auth
        String currentAction = request.getPathInfo();
        if (currentAction == null){
            currentAction = "";
        }
        switch (currentAction){
            case "/registration":
                registration(request, response);
                break;
            case "/login":
                login(request, response);
                break;
            default:
                response.sendError(HttpServletResponse.SC_NOT_FOUND);
        }
    }

    @Override
    protected void doGet(HttpServletRequest request, HttpServletResponse response)
            throws IOException {
        String currentAction = request.getPathInfo();
        if (currentAction == null){
            currentAction = "";
        }

        switch (currentAction){
            case "/logout":
                logout(request, response);
                break;
            default:
                response.sendError(HttpServletResponse.SC_NOT_FOUND);
        }
    }

    //registration
    private void registration(HttpServletRequest request, HttpServletResponse response)
            throws IOException{
        String name = request.getParameter("name");
        String email = request.getParameter(("email"));
        String password = request.getParameter("password");
        String hashedPassword = SafePasswords.hashPassword(password);
        User user = new User();
        user.setName(name);
        user.setEmail(email);
        user.setPassword(hashedPassword);
        user.setRole("USER");

       //Добавляем в БД
        if (userDAO.register(user)){
            response.sendRedirect(request.getContextPath() + "/login.jsp");
        } else{
            response.sendRedirect(request.getContextPath() + "/registration.jsp?error=duplicate");
        }
    }

    //login
    private void login(HttpServletRequest request, HttpServletResponse response)
            throws IOException{
        String email = request.getParameter(("email"));
        String password = request.getParameter("password");
        User user = userDAO.getByEmail(email);

        if (user != null && SafePasswords.checkPassword(password, user.getPassword())){
            //Создаем сессию
            HttpSession session = request.getSession(true);
            session.setAttribute("user", user);
            response.sendRedirect(request.getContextPath() + "/catalog");
        } else{
            response.sendRedirect(request.getContextPath() + "/login.jsp?error=1");
        }
    }

    //logout
    private void logout(HttpServletRequest request, HttpServletResponse response)
            throws IOException{
        HttpSession session = request.getSession(false);
        if (session != null){
            session.invalidate();
        }
        response.sendRedirect(request.getContextPath() + "/login.jsp");
    }
}

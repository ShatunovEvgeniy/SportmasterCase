package com.example.controller;

import com.example.beans.AiSummary;
import com.example.beans.Category;
import com.example.beans.Product;
import com.example.dao.CategoryDAO;
import com.example.dao.Impl.CategoryDaoImpl;
import com.example.dao.Impl.ProductDaoImpl;
import com.example.dao.Impl.SummaryDaoImpl;
import com.example.dao.ProductDAO;
import com.example.dao.SummaryDAO;
import jakarta.servlet.ServletException;
import jakarta.servlet.annotation.WebServlet;
import jakarta.servlet.http.HttpServlet;
import jakarta.servlet.http.HttpServletRequest;
import jakarta.servlet.http.HttpServletResponse;

import java.io.IOException;
import java.util.List;

@WebServlet("/catalog/*")
public class ProductServlet  extends HttpServlet {

    private ProductDAO productDAO;
    private CategoryDAO categoryDAO;
    private SummaryDAO summaryDAO;
    @Override
    public void init(){
        productDAO = new ProductDaoImpl();
        categoryDAO = new CategoryDaoImpl();
        summaryDAO = new SummaryDaoImpl();
    }

    @Override
    protected void doGet(HttpServletRequest request, HttpServletResponse response)
        throws ServletException, IOException {
        String currentAction = request.getPathInfo();
        if (currentAction == null){
            currentAction = "";
        }
        switch (currentAction){
            case "":
                //Вывод списка товаров в каталоге
                getAllProductsFromCatalog(request, response);
                break;
            case "/category":
                //Вывод товаров из категории в каталоге
                getProductsFromOneCategory(request, response);
                break;
            case "/product_info":
                getProductInfo(request, response);
                break;
            default:
                response.sendError(HttpServletResponse.SC_NOT_FOUND);
        }
    }

    private void getAllProductsFromCatalog(HttpServletRequest request, HttpServletResponse response)
        throws ServletException, IOException{
        List<Product> products = productDAO.getAllProducts();
        for (Product product : products) {
            summaryDAO.fillRatingInfo(product);
        }
        List<Category> categories = categoryDAO.getAllCategories();
        request.setAttribute("categories", categories);
        request.setAttribute("products", products);
        request.getRequestDispatcher("/catalog.jsp").forward(request, response);
    }

    private void getProductsFromOneCategory(HttpServletRequest request, HttpServletResponse response)
            throws ServletException, IOException{
        String categoryIdStr = request.getParameter("categoryId");
        if (categoryIdStr == null || categoryIdStr.isEmpty()) {
            getAllProductsFromCatalog(request, response);
            return;
        }

        int categoryId = Integer.parseInt(request.getParameter("categoryId"));
        List<Product> products = productDAO.getProductsByCategoryId(categoryId);
        for (Product product : products) {
            summaryDAO.fillRatingInfo(product);
        }
        List<Category> categories = categoryDAO.getAllCategories(); //для сохранения работающего списка
        request.setAttribute("categories", categories);
        request.setAttribute("products", products);
        request.setAttribute("selectedCategoryId", categoryId);
        request.getRequestDispatcher("/catalog.jsp").forward(request, response);

    }

    private void getProductInfo(HttpServletRequest request, HttpServletResponse response)
            throws ServletException, IOException{
        int productId = Integer.parseInt(request.getParameter("id"));
        Product product = productDAO.getProductById(productId);
        if (product == null){
            response.sendError(HttpServletResponse.SC_NOT_FOUND);
            return;
        }
        AiSummary summary = summaryDAO.getSummary(product.getModelId());
        request.setAttribute("product", product);
        request.setAttribute("summary", summary);
        request.getRequestDispatcher("/product_info.jsp").forward(request, response);
    }
}

package com.example.util;

import org.mindrot.jbcrypt.BCrypt;

import javax.crypto.Cipher;
import javax.crypto.SecretKey;
import javax.crypto.spec.SecretKeySpec;

public class SafePasswords {
    //Хеширование паролей
    public static String hashPassword (String initPassword){
        return BCrypt.hashpw(initPassword, BCrypt.gensalt());
    }

    //Сравнение изначального пароля и хешированного пароля
    public static boolean checkPassword(String initPassword, String hashedPassword){
        try{
            return BCrypt.checkpw(initPassword, hashedPassword);
        }catch (Exception e){
            return false;
        }
    }
}

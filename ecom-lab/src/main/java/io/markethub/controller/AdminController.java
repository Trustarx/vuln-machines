package io.markethub.controller;

import io.jsonwebtoken.Claims;
import io.markethub.repository.UserRepository;
import io.markethub.service.JwtService;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.*;

import java.util.HashMap;
import java.util.Map;

@RestController
@RequestMapping("/api/admin")
public class AdminController {

    @Autowired private JwtService jwt;
    @Autowired private UserRepository users;

    /**
     * Admin-only endpoint. JWT must validate AND payload must have role=ADMIN.
     * Hit this with a forged or mass-assignment-obtained admin token.
     */
    @GetMapping("/flag")
    public ResponseEntity<?> flag(@RequestHeader(value = "Authorization", required = false) String auth) {
        Claims claims = parseAuth(auth);
        if (claims == null) return ResponseEntity.status(401).body(err("invalid token"));
        if (!"ADMIN".equalsIgnoreCase(String.valueOf(claims.get("role")))) {
            return ResponseEntity.status(403).body(err("admin only"));
        }
        Map<String,Object> body = new HashMap<>();
        body.put("flag", "FLAG{markethub_admin_endpoint_reached}");
        body.put("authenticated_as", claims.getSubject());
        body.put("role", claims.get("role"));
        return ResponseEntity.ok(body);
    }

    @GetMapping("/users")
    public ResponseEntity<?> listUsers(@RequestHeader(value = "Authorization", required = false) String auth) {
        Claims claims = parseAuth(auth);
        if (claims == null) return ResponseEntity.status(401).body(err("invalid token"));
        if (!"ADMIN".equalsIgnoreCase(String.valueOf(claims.get("role")))) {
            return ResponseEntity.status(403).body(err("admin only"));
        }
        return ResponseEntity.ok(users.findAll());
    }

    private Claims parseAuth(String auth) {
        if (auth == null || !auth.startsWith("Bearer ")) return null;
        try {
            return jwt.verify(auth.substring("Bearer ".length()));
        } catch (Exception e) {
            return null;
        }
    }

    private static Map<String,String> err(String msg) {
        Map<String,String> m = new HashMap<>();
        m.put("error", msg);
        return m;
    }
}

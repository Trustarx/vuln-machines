package io.markethub.controller;

import io.markethub.model.User;
import io.markethub.repository.UserRepository;
import io.markethub.service.JwtService;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.*;

import java.util.HashMap;
import java.util.Map;
import java.util.Optional;

@RestController
@RequestMapping("/api/auth")
public class AuthController {

    @Autowired private UserRepository users;
    @Autowired private JwtService jwt;

    // ── VULN: Path 3 — mass assignment ─────────────────────────
    // The full `User` object is bound from the request body. Any attacker
    // can include "role":"ADMIN" in the JSON and become an admin.
    @PostMapping("/register")
    public ResponseEntity<?> register(@RequestBody User input) {
        if (input.getUsername() == null || input.getPassword() == null) {
            return ResponseEntity.badRequest().body(err("username and password required"));
        }
        if (users.findByUsername(input.getUsername()).isPresent()) {
            return ResponseEntity.status(409).body(err("username taken"));
        }
        input.setId(null);
        // role is whatever the client sent (default BUYER in entity, but
        // the client can override it). This is the bug.
        User saved = users.save(input);
        String token = jwt.issue(saved.getUsername(), saved.getRole());
        Map<String,Object> body = new HashMap<>();
        body.put("token", token);
        body.put("user", publicUser(saved));
        return ResponseEntity.ok(body);
    }

    @PostMapping("/login")
    public ResponseEntity<?> login(@RequestBody Map<String,String> body) {
        Optional<User> u = users.findByUsername(body.get("username"));
        if (u.isEmpty() || !u.get().getPassword().equals(body.get("password"))) {
            return ResponseEntity.status(401).body(err("invalid credentials"));
        }
        String token = jwt.issue(u.get().getUsername(), u.get().getRole());
        Map<String,Object> resp = new HashMap<>();
        resp.put("token", token);
        resp.put("user", publicUser(u.get()));
        return ResponseEntity.ok(resp);
    }

    private static Map<String,Object> publicUser(User u) {
        Map<String,Object> m = new HashMap<>();
        m.put("id", u.getId());
        m.put("username", u.getUsername());
        m.put("email", u.getEmail());
        m.put("role", u.getRole());
        return m;
    }

    private static Map<String,String> err(String msg) {
        Map<String,String> m = new HashMap<>();
        m.put("error", msg);
        return m;
    }
}

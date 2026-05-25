package io.markethub.model;

import javax.persistence.*;
import com.fasterxml.jackson.annotation.JsonIgnore;

@Entity
@Table(name = "users")
public class User {
    @Id
    @GeneratedValue(strategy = GenerationType.IDENTITY)
    private Long id;

    @Column(unique = true, nullable = false)
    private String username;

    @Column(nullable = false)
    private String email;

    // ── Plaintext for the lab — would be hashed in real life ──
    @Column(nullable = false)
    private String password;

    // Role accepted from request body — Path 3 mass assignment bug
    @Column(nullable = false)
    private String role = "BUYER";

    @Column(name = "reset_token")
    private String resetToken;

    public Long getId() { return id; }
    public void setId(Long id) { this.id = id; }
    public String getUsername() { return username; }
    public void setUsername(String u) { this.username = u; }
    public String getEmail() { return email; }
    public void setEmail(String e) { this.email = e; }
    public String getPassword() { return password; }
    public void setPassword(String p) { this.password = p; }
    public String getRole() { return role; }
    public void setRole(String r) { this.role = r; }
    public String getResetToken() { return resetToken; }
    public void setResetToken(String t) { this.resetToken = t; }
}

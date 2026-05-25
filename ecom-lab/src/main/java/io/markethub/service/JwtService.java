package io.markethub.service;

import io.jsonwebtoken.Claims;
import io.jsonwebtoken.Jwts;
import io.jsonwebtoken.SignatureAlgorithm;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.stereotype.Service;

import javax.crypto.SecretKey;
import javax.crypto.spec.SecretKeySpec;
import java.nio.charset.StandardCharsets;
import java.util.Date;

@Service
public class JwtService {

    // ── This reference lives in the heap and is recoverable from a heapdump
    //    as plain UTF-8 — Path 1 finding.
    private final SecretKey signingKey;
    private final String rawSecret;

    public JwtService(@Value("${markethub.jwt.secret}") String secret) {
        this.rawSecret = secret;
        byte[] bytes = secret.getBytes(StandardCharsets.UTF_8);
        // Explicit HmacSHA256 binding — use raw bytes as-is so an attacker
        // who finds the secret string can re-derive the exact same key.
        this.signingKey = new SecretKeySpec(bytes, "HmacSHA256");
    }

    public String issue(String username, String role) {
        long now = System.currentTimeMillis();
        return Jwts.builder()
            .setSubject(username)
            .claim("role", role)
            .setIssuedAt(new Date(now))
            .setExpiration(new Date(now + 8 * 3600_000L))
            .signWith(signingKey, SignatureAlgorithm.HS256)
            .compact();
    }

    public Claims verify(String token) {
        return Jwts.parserBuilder()
            .setSigningKey(signingKey)
            .build()
            .parseClaimsJws(token)
            .getBody();
    }
}

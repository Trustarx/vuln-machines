package io.markethub.controller;

import io.markethub.repository.ProductRepository;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.jdbc.core.JdbcTemplate;
import org.springframework.web.bind.annotation.*;

import java.util.List;
import java.util.Map;

@RestController
@RequestMapping("/api/products")
public class ProductController {

    @Autowired private ProductRepository products;
    @Autowired private JdbcTemplate jdbc;

    @GetMapping
    public Object list() {
        return products.findAll();
    }

    // ── VULN: Path 2 — SQL injection ───────────────────────────
    // Raw string concatenation into a native query via JdbcTemplate.
    // UNION-based attack works because JdbcTemplate.queryForList just
    // returns whatever columns the query produces.
    @GetMapping("/search")
    public Object search(@RequestParam(name = "q", defaultValue = "") String q) {
        String sql = "SELECT id, name, sku, price FROM products " +
                     "WHERE name LIKE '%" + q + "%' OR description LIKE '%" + q + "%'";
        try {
            List<Map<String,Object>> rows = jdbc.queryForList(sql);
            return rows;
        } catch (Exception e) {
            return Map.of(
                "query", sql,
                "error", e.getMessage()
            );
        }
    }
}

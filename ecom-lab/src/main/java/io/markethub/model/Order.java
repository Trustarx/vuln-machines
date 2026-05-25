package io.markethub.model;

import javax.persistence.*;
import java.math.BigDecimal;

@Entity
@Table(name = "orders")
public class Order {
    @Id
    @GeneratedValue(strategy = GenerationType.IDENTITY)
    private Long id;

    @Column(name = "user_id")
    private Long userId;

    private BigDecimal total;
    private String status;

    @Column(name = "created_at")
    private String createdAt;

    public Long getId() { return id; }
    public void setId(Long id) { this.id = id; }
    public Long getUserId() { return userId; }
    public void setUserId(Long u) { this.userId = u; }
    public BigDecimal getTotal() { return total; }
    public void setTotal(BigDecimal t) { this.total = t; }
    public String getStatus() { return status; }
    public void setStatus(String s) { this.status = s; }
    public String getCreatedAt() { return createdAt; }
    public void setCreatedAt(String c) { this.createdAt = c; }
}

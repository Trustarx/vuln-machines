package io.markethub.model;

import javax.persistence.*;
import java.math.BigDecimal;

@Entity
@Table(name = "products")
public class Product {
    @Id
    @GeneratedValue(strategy = GenerationType.IDENTITY)
    private Long id;

    private String name;
    private String sku;
    private String description;
    private BigDecimal price;
    private Integer stock;

    public Long getId() { return id; }
    public void setId(Long id) { this.id = id; }
    public String getName() { return name; }
    public void setName(String n) { this.name = n; }
    public String getSku() { return sku; }
    public void setSku(String s) { this.sku = s; }
    public String getDescription() { return description; }
    public void setDescription(String d) { this.description = d; }
    public BigDecimal getPrice() { return price; }
    public void setPrice(BigDecimal p) { this.price = p; }
    public Integer getStock() { return stock; }
    public void setStock(Integer s) { this.stock = s; }
}

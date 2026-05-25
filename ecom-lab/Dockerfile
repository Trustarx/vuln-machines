# ── Build stage ──────────────────────────────────────────────
FROM maven:3.9-eclipse-temurin-17 AS build
WORKDIR /build
COPY pom.xml .
# Cache dependencies
RUN mvn -B -q dependency:go-offline
COPY src ./src
RUN mvn -B -q -DskipTests package

# ── Runtime stage ────────────────────────────────────────────
FROM eclipse-temurin:17-jre
WORKDIR /app

# Pre-create invoice dir + plant the flag file the path-traversal path reads
RUN mkdir -p /app/invoices /app/private
COPY --from=build /build/target/markethub-1.0.0.jar app.jar

# Static invoice file so the download endpoint has something legitimate to serve
RUN echo "INVOICE 1001 — Acme Office Supplies — Total: \$1,234.56" > /app/invoices/INV-1001.pdf
RUN echo "INVOICE 1002 — Globex Logistics — Total: \$8,765.43"   > /app/invoices/INV-1002.pdf

# Private file the traversal path reads
RUN echo "FLAG{markethub_path_traversal_invoice_download}" > /app/private/flag.txt

EXPOSE 8080
CMD ["java", "-Xmx256m", "-XX:+HeapDumpOnOutOfMemoryError", "-jar", "app.jar"]

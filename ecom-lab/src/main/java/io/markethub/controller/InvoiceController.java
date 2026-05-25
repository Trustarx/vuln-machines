package io.markethub.controller;

import org.springframework.beans.factory.annotation.Value;
import org.springframework.core.io.FileSystemResource;
import org.springframework.core.io.Resource;
import org.springframework.http.MediaType;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.*;

import java.io.File;
import java.util.Map;

@RestController
@RequestMapping("/api/invoices")
public class InvoiceController {

    @Value("${markethub.invoices.dir}")
    private String invoicesDir;

    // ── VULN: Path 4 — path traversal ──────────────────────────
    // The `file` parameter is concatenated to the invoices directory with
    // no normalisation or allow-list. `?file=../private/flag.txt` escapes
    // the directory and reads any file the JVM can access.
    @GetMapping("/download")
    public ResponseEntity<?> download(@RequestParam("file") String file) {
        File target = new File(invoicesDir + "/" + file);
        if (!target.exists() || target.isDirectory()) {
            return ResponseEntity.status(404)
                .body(Map.of("error", "not found", "path", target.getAbsolutePath()));
        }
        Resource resource = new FileSystemResource(target);
        return ResponseEntity.ok()
            .contentType(MediaType.APPLICATION_OCTET_STREAM)
            .header("Content-Disposition", "attachment; filename=\"" + target.getName() + "\"")
            .body(resource);
    }
}

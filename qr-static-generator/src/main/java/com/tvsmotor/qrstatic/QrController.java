package com.tvsmotor.qrstatic;

import org.springframework.core.io.ClassPathResource;
import org.springframework.core.io.Resource;
import org.springframework.http.CacheControl;
import org.springframework.http.HttpHeaders;
import org.springframework.http.HttpStatus;
import org.springframework.http.MediaType;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.CrossOrigin;
import org.springframework.web.bind.annotation.PostMapping;
import org.springframework.web.bind.annotation.RequestParam;
import org.springframework.web.bind.annotation.RestController;

import java.awt.Color;
import java.awt.Font;
import java.io.InputStream;

/**
 * Single endpoint that turns a URL into a styled QR SVG.
 *
 * Everything except the URL is locked to the values below, matching the
 * parent project's defaults for the "squared" style with the default TVS logo.
 */
@RestController
@CrossOrigin(origins = "*")
public class QrController {

    // ---- Locked visual settings (not editable by the user) ----
    private static final int    SIZE            = 600;
    private static final double LOGO_SCALE      = 0.15;        // honored by classic; squared uses its own fixed fraction
    private static final String FG_COLOR_HEX    = "#000000";
    private static final String BG_COLOR_HEX    = "#ffffff";
    private static final String CORNER_COLOR    = "#000000";
    private static final String QR_STYLE        = "squared";   // squared | classic
    private static final String DEFAULT_LOGO    = "TVS_Logo.svg";
    private static final int    CORNER_RADIUS   = Math.max(20, SIZE / 20);

    private final QrService qrService;

    public QrController(QrService qrService) {
        this.qrService = qrService;
    }

    @PostMapping(value = "/api/generate", produces = "image/svg+xml")
    public ResponseEntity<String> generate(@RequestParam("url") String url) throws Exception {
        if (url == null || url.isBlank()) {
            return ResponseEntity.badRequest()
                    .contentType(MediaType.TEXT_PLAIN)
                    .body("URL is required");
        }

        String content = url.trim();

        try (InputStream logoStream = openDefaultLogo()) {
            String svg;
            if ("squared".equalsIgnoreCase(QR_STYLE)) {
                svg = qrService.generateQrSvgWithSquaredBoxes(
                        content, SIZE, logoStream,
                        FG_COLOR_HEX, BG_COLOR_HEX, CORNER_COLOR,
                        LOGO_SCALE, CORNER_RADIUS,
                        null, new Font("Nunito Sans", Font.BOLD, 20), Color.BLACK);
            } else {
                svg = qrService.generateQrSvgWithColoredCornersAndLogo(
                        content, SIZE, logoStream,
                        FG_COLOR_HEX, BG_COLOR_HEX, CORNER_COLOR,
                        LOGO_SCALE, CORNER_RADIUS,
                        null, new Font("Nunito Sans", Font.BOLD, 20), Color.BLACK);
            }

            HttpHeaders headers = new HttpHeaders();
            headers.setContentType(MediaType.parseMediaType("image/svg+xml"));
            headers.setCacheControl(CacheControl.noCache().getHeaderValue());
            return new ResponseEntity<>(svg, headers, HttpStatus.OK);
        }
    }

    private InputStream openDefaultLogo() throws Exception {
        Resource logo = new ClassPathResource(DEFAULT_LOGO);
        return logo.exists() ? logo.getInputStream() : null;
    }
}

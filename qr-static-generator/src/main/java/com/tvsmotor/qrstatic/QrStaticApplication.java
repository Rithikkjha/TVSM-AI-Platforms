package com.tvsmotor.qrstatic;

import org.springframework.boot.SpringApplication;
import org.springframework.boot.autoconfigure.SpringBootApplication;

/**
 * Minimal standalone QR generator.
 *
 * No database, no auth, no cloud storage — just static QR generation.
 * The only user input is a URL; every visual option is locked server-side.
 */
@SpringBootApplication
public class QrStaticApplication {
    public static void main(String[] args) {
        SpringApplication.run(QrStaticApplication.class, args);
    }
}

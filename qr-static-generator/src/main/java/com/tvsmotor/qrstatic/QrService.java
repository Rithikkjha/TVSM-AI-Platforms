package com.tvsmotor.qrstatic;

import com.google.zxing.*;
import com.google.zxing.client.j2se.MatrixToImageConfig;
import com.google.zxing.client.j2se.MatrixToImageWriter;
import com.google.zxing.common.BitMatrix;
import com.google.zxing.qrcode.QRCodeWriter;
import com.google.zxing.qrcode.decoder.ErrorCorrectionLevel;
import org.springframework.stereotype.Service;

import javax.imageio.ImageIO;
import java.awt.*;
import java.awt.geom.Rectangle2D;
import java.awt.geom.RoundRectangle2D;
import java.awt.image.BufferedImage;
import java.io.ByteArrayInputStream;
import java.io.ByteArrayOutputStream;
import java.io.InputStream;
import java.util.Base64;
import java.util.HashMap;
import java.util.Map;
import java.nio.charset.StandardCharsets;


import static org.apache.catalina.manager.JspHelper.escapeXml;

@Service
public class QrService {

    /** Generate basic QR BitMatrix with high error correction. */
    private BitMatrix createMatrix(String content, int size) throws WriterException {
        Map<EncodeHintType,Object> hints = new HashMap<>();
        hints.put(EncodeHintType.ERROR_CORRECTION, ErrorCorrectionLevel.H); // H = 30% redundancy to tolerate logo
        hints.put(EncodeHintType.MARGIN, 1); // small margin
        QRCodeWriter writer = new QRCodeWriter();
        return writer.encode(content, BarcodeFormat.QR_CODE, size, size, hints);
    }

    /**
     * Generate PNG bytes of a QR code with optional centered logo (InputStream), custom colors and corner radius.
     */
    public byte[] generateQrPng(String content,
                                int size,
                                InputStream logoStream,
                                Color fg,
                                Color bg,
                                double logoScaleFraction,
                                int cornerRadiusPx) {

        try {
            BitMatrix matrix = createMatrix(content, size);

            int onColor = fg.getRGB();
            int offColor = bg.getRGB();
            MatrixToImageConfig config = new MatrixToImageConfig(onColor, offColor);

            BufferedImage qrImage = MatrixToImageWriter.toBufferedImage(matrix, config);

            if (logoStream == null) {
                try (ByteArrayOutputStream os = new ByteArrayOutputStream()) {
                    ImageIO.write(qrImage, "PNG", os);
                    return os.toByteArray();
                }
            }

            BufferedImage logo = ImageIO.read(logoStream);
            if (logo == null) {
                try (ByteArrayOutputStream os = new ByteArrayOutputStream()) {
                    ImageIO.write(qrImage, "PNG", os);
                    return os.toByteArray();
                }
            }

            // ---- Make logo square ----
            logo = cropTransparentEdges(logo);
            int squareSize = Math.max(logo.getWidth(), logo.getHeight());
            BufferedImage squareLogo = new BufferedImage(squareSize, squareSize, BufferedImage.TYPE_INT_ARGB);
            Graphics2D lg = squareLogo.createGraphics();
            lg.setComposite(AlphaComposite.Clear);
            lg.fillRect(0, 0, squareSize, squareSize);
            lg.setComposite(AlphaComposite.SrcOver);
            int x = (squareSize - logo.getWidth()) / 2;
            int y = (squareSize - logo.getHeight()) / 2;
            lg.drawImage(logo, x, y, null);
            lg.dispose();
            logo = squareLogo;

            int logoMaxSize = (int) (size * logoScaleFraction);
            int logoW = logoMaxSize;
            int logoH = logoMaxSize;
            double aspect = (double) logoW / logoH;
            int targetW = logoMaxSize;
            int targetH = (int) Math.round(logoMaxSize / aspect);
            if (targetH > logoMaxSize) {
                targetH = logoMaxSize;
                targetW = (int) Math.round(logoMaxSize * aspect);
            }

            BufferedImage combined = new BufferedImage(size, size, BufferedImage.TYPE_INT_ARGB);
            Graphics2D g = combined.createGraphics();
            g.setRenderingHint(RenderingHints.KEY_ANTIALIASING, RenderingHints.VALUE_ANTIALIAS_ON);
            g.setRenderingHint(RenderingHints.KEY_INTERPOLATION, RenderingHints.VALUE_INTERPOLATION_BICUBIC);
            g.setRenderingHint(RenderingHints.KEY_RENDERING, RenderingHints.VALUE_RENDER_QUALITY);

            g.setColor(bg);
            g.fillRect(0, 0, size, size);

            g.drawImage(qrImage, 0, 0, null);

            int centerX = (size - targetW) / 2;
            int centerY = (size - targetH) / 2;

            int haloPadding = Math.max(8, targetW / 10);
            int haloW = targetW + haloPadding;
            int haloH = targetH + haloPadding;
            int haloX = (size - haloW) / 2;
            int haloY = (size - haloH) / 2;

            g.setComposite(AlphaComposite.getInstance(AlphaComposite.SRC_OVER, 1f));
            g.setColor(Color.WHITE);
            RoundRectangle2D rounded = new RoundRectangle2D.Float(haloX, haloY, haloW, haloH, cornerRadiusPx, cornerRadiusPx);
            g.fill(rounded);

            g.setColor(new Color(220, 220, 220));
            g.setStroke(new BasicStroke(Math.max(2, haloW / 80f)));
            g.draw(rounded);

            g.drawImage(logo, centerX, centerY, targetW, targetH, null);

            g.dispose();

            try (ByteArrayOutputStream out = new ByteArrayOutputStream()) {
                ImageIO.write(combined, "PNG", out);
                return out.toByteArray();
            }
        } catch (Exception e) {
            throw new RuntimeException("QR generation failed", e);
        }
    }

    private BufferedImage cropTransparentEdges(BufferedImage image) {
        int minX = image.getWidth();
        int minY = image.getHeight();
        int maxX = -1;
        int maxY = -1;

        for (int y = 0; y < image.getHeight(); y++) {
            for (int x = 0; x < image.getWidth(); x++) {
                int alpha = (image.getRGB(x, y) >> 24) & 0xff;
                if (alpha > 0) {
                    if (x < minX) minX = x;
                    if (y < minY) minY = y;
                    if (x > maxX) maxX = x;
                    if (y > maxY) maxY = y;
                }
            }
        }

        if (maxX < minX || maxY < minY) {
            return image; // Fully transparent
        }

        return image.getSubimage(minX, minY, (maxX - minX + 1), (maxY - minY + 1));
    }

    public byte[] generateQrWithColoredCorners(
            String content,
            int size,
            InputStream logoStream,
            Color fg,
            Color bg,
            Color cornerColor,
            double logoScaleFraction,
            int cornerRadiusPx,
            String labelText,
            Font labelFont,
            Color labelColor) {

        try {
            Map<EncodeHintType, Object> hints = new HashMap<>();
            hints.put(EncodeHintType.MARGIN, 4);

            BitMatrix fullMatrix = new MultiFormatWriter().encode(content, BarcodeFormat.QR_CODE, 0, 0, hints);

            int left = fullMatrix.getWidth();
            int right = 0;
            int top = fullMatrix.getHeight();
            int bottom = 0;

            for (int y = 0; y < fullMatrix.getHeight(); y++) {
                for (int x = 0; x < fullMatrix.getWidth(); x++) {
                    if (fullMatrix.get(x, y)) {
                        if (x < left) left = x;
                        if (x > right) right = x;
                        if (y < top) top = y;
                        if (y > bottom) bottom = y;
                    }
                }
            }

            int matrixWidth = right - left + 1;
            int matrixHeight = bottom - top + 1;

            BitMatrix croppedMatrix = new BitMatrix(matrixWidth, matrixHeight);
            for (int y = 0; y < matrixHeight; y++) {
                for (int x = 0; x < matrixWidth; x++) {
                    if (fullMatrix.get(x + left, y + top)) {
                        croppedMatrix.set(x, y);
                    }
                }
            }

            double moduleSize = (double) size / matrixWidth;

            int labelHeight = 30;
            if (labelText != null && !labelText.isEmpty()) {
                labelHeight = labelFont.getSize() + 10;
            }

            BufferedImage qrImage = new BufferedImage(size, size + labelHeight, BufferedImage.TYPE_INT_ARGB);
            Graphics2D g = qrImage.createGraphics();

            g.setRenderingHint(RenderingHints.KEY_ANTIALIASING, RenderingHints.VALUE_ANTIALIAS_OFF);
            g.setRenderingHint(RenderingHints.KEY_STROKE_CONTROL, RenderingHints.VALUE_STROKE_PURE);

            g.setColor(bg);
            g.fillRect(0, 0, size, size + labelHeight);

            for (int y = 0; y < matrixHeight; y++) {
                for (int x = 0; x < matrixWidth; x++) {
                    boolean inTopLeft = (x < 7 && y < 7);
                    boolean inTopRight = (x >= matrixWidth - 7 && y < 7);
                    boolean inBottomLeft = (x < 7 && y >= matrixHeight - 7);

                    Color moduleColor;
                    if (inTopLeft || inTopRight || inBottomLeft) {
                        int localX = inTopRight ? x - (matrixWidth - 7) : x;
                        int localY = (inTopRight || inTopLeft) ? y : y - (matrixHeight - 7);

                        if (isFinderOuter(localX, localY) || isFinderCenter(localX, localY)) {
                            moduleColor = cornerColor;
                        } else if (isFinderInner(localX, localY)) {
                            moduleColor = bg;
                        } else {
                            moduleColor = croppedMatrix.get(x, y) ? fg : bg;
                        }
                    } else {
                        moduleColor = croppedMatrix.get(x, y) ? fg : bg;
                    }

                    g.setColor(moduleColor);
                    g.fill(new Rectangle2D.Double(x * moduleSize, y * moduleSize, moduleSize, moduleSize));
                }
            }

            if (logoStream != null) {
                BufferedImage logo = ImageIO.read(logoStream);
                if (logo != null) {
                    int maxDim = Math.max(logo.getWidth(), logo.getHeight());
                    BufferedImage squareLogo = new BufferedImage(maxDim, maxDim, BufferedImage.TYPE_INT_ARGB);
                    Graphics2D lg = squareLogo.createGraphics();
                    lg.setComposite(AlphaComposite.Clear);
                    lg.fillRect(0, 0, maxDim, maxDim);
                    lg.setComposite(AlphaComposite.Src);
                    lg.drawImage(logo, (maxDim - logo.getWidth()) / 2, (maxDim - logo.getHeight()) / 2, null);
                    lg.dispose();

                    int logoMaxSize = (int) (size * logoScaleFraction);
                    BufferedImage scaledLogo = new BufferedImage(logoMaxSize, logoMaxSize, BufferedImage.TYPE_INT_ARGB);
                    Graphics2D sg = scaledLogo.createGraphics();
                    sg.setRenderingHint(RenderingHints.KEY_INTERPOLATION, RenderingHints.VALUE_INTERPOLATION_BICUBIC);
                    sg.setRenderingHint(RenderingHints.KEY_ANTIALIASING, RenderingHints.VALUE_ANTIALIAS_ON);
                    sg.setRenderingHint(RenderingHints.KEY_RENDERING, RenderingHints.VALUE_RENDER_QUALITY);
                    sg.drawImage(squareLogo, 0, 0, logoMaxSize, logoMaxSize, null);
                    sg.dispose();

                    float alpha = 1.0f;
                    BufferedImage transparentLogo = new BufferedImage(logoMaxSize, logoMaxSize, BufferedImage.TYPE_INT_ARGB);
                    Graphics2D tg = transparentLogo.createGraphics();
                    tg.setComposite(AlphaComposite.getInstance(AlphaComposite.SRC_OVER, alpha));
                    tg.drawImage(scaledLogo, 0, 0, null);
                    tg.dispose();

                    int haloX = (size - logoMaxSize) / 2 - 4;
                    int haloY = (size - logoMaxSize) / 2 - 4;
                    int haloW = logoMaxSize + 8;
                    int haloH = logoMaxSize + 8;

                    g.setColor(Color.WHITE);
                    g.fill(new RoundRectangle2D.Float(haloX, haloY, haloW, haloH, cornerRadiusPx, cornerRadiusPx));

                    g.drawImage(transparentLogo, (size - logoMaxSize) / 2, (size - logoMaxSize) / 2, null);
                }
            }

            if (labelText != null && !labelText.isEmpty()) {
                g.setColor(labelColor);
                g.setFont(labelFont);

                FontMetrics fm = g.getFontMetrics();
                int textWidth = fm.stringWidth(labelText);
                int x = (size - textWidth) / 2;
                int y = size + (labelHeight + fm.getAscent()) / 2 - 4;

                g.drawString(labelText, x, y);
            }

            g.dispose();

            try (ByteArrayOutputStream os = new ByteArrayOutputStream()) {
                ImageIO.write(qrImage, "PNG", os);
                return os.toByteArray();
            }

        } catch (Exception e) {
            throw new RuntimeException("QR generation failed", e);
        }
    }

    private boolean isFinderOuter(int x, int y) {
        return (x == 0 || x == 6 || y == 0 || y == 6);
    }

    private boolean isFinderInner(int x, int y) {
        return (x > 0 && x < 6 && y > 0 && y < 6) && !(x >= 2 && x <= 4 && y >= 2 && y <= 4);
    }

    private boolean isFinderCenter(int x, int y) {
        return (x >= 2 && x <= 4 && y >= 2 && y <= 4);
    }

    public String generateQrSvgWithColoredCornersAndLogo(
            String content,
            int size,
            InputStream logoStream,
            String fgColorHex,
            String bgColorHex,
            String cornerColorHex,
            double logoScaleFraction,
            int cornerRadiusPx,
            String labelText,
            Font labelFont,
            Color labelColor) throws Exception {

        Map<EncodeHintType, Object> hints = new HashMap<>();
        hints.put(EncodeHintType.ERROR_CORRECTION, ErrorCorrectionLevel.H);
        hints.put(EncodeHintType.MARGIN, 0);

        BitMatrix fullMatrix = new MultiFormatWriter().encode(content, BarcodeFormat.QR_CODE, 0, 0, hints);

        int margin = 20;

        // Crop quiet zone
        int left = fullMatrix.getWidth();
        int right = 0;
        int top = fullMatrix.getHeight();
        int bottom = 0;
        for (int y = 0; y < fullMatrix.getHeight(); y++) {
            for (int x = 0; x < fullMatrix.getWidth(); x++) {
                if (fullMatrix.get(x, y)) {
                    if (x < left) left = x;
                    if (x > right) right = x;
                    if (y < top) top = y;
                    if (y > bottom) bottom = y;
                }
            }
        }

        int matrixWidth = right - left + 1;
        int matrixHeight = bottom - top + 1;

        BitMatrix croppedMatrix = new BitMatrix(matrixWidth, matrixHeight);
        for (int y = 0; y < matrixHeight; y++) {
            for (int x = 0; x < matrixWidth; x++) {
                if (fullMatrix.get(x + left, y + top)) {
                    croppedMatrix.set(x, y);
                }
            }
        }

        double moduleSize = (double) size / matrixWidth;

        // Extra height for label (keep as before)
        int labelHeight = (labelText != null && !labelText.isBlank()) ? 30 : 0;
        int totalHeight = size + labelHeight;

        StringBuilder svg = new StringBuilder();
        svg.append(String.format(
                "<svg xmlns='http://www.w3.org/2000/svg' width='%d' height='%d' viewBox='0 0 %d %d'>",
                size + 2 * margin, totalHeight + 2 * margin, size + 2 * margin, totalHeight + 2 * margin));

        // ---- keep these vars (as you had) ----
        int rectWidth  = size + 2 * margin;
        int rectHeight = size + labelHeight + 2 * margin;
        // for border add  stroke='%s' stroke-width='4'
        svg.append(String.format(
                "<rect x='1' y='1' width='%d' height='%d' rx='%d' ry='%d' fill='%s' />",
                rectWidth, rectHeight, cornerRadiusPx, cornerRadiusPx, bgColorHex, "#CCCCCC"
        ));

        // Draw modules
        for (int y = 0; y < matrixHeight; y++) {
            for (int x = 0; x < matrixWidth; x++) {
                boolean inTopLeft = (x < 7 && y < 7);
                boolean inTopRight = (x >= matrixWidth - 7 && y < 7);
                boolean inBottomLeft = (x < 7 && y >= matrixHeight - 7);

                String moduleColor;

                if (inTopLeft || inTopRight || inBottomLeft) {
                    int localX = inTopRight ? x - (matrixWidth - 7) : x;
                    int localY = (inTopRight || inTopLeft) ? y : y - (matrixHeight - 7);

                    if (isFinderOuter(localX, localY) || isFinderCenter(localX, localY)) {
                        moduleColor = cornerColorHex;
                    } else if (isFinderInner(localX, localY)) {
                        moduleColor = bgColorHex;
                    } else {
                        moduleColor = croppedMatrix.get(x, y) ? fgColorHex : bgColorHex;
                    }
                } else {
                    moduleColor = croppedMatrix.get(x, y) ? fgColorHex : bgColorHex;
                }

                if (moduleColor.equals(bgColorHex)) continue;

                double rectX = x * moduleSize + margin;
                double rectY = y * moduleSize + margin;

                svg.append(String.format(
                        "<rect x='%.2f' y='%.2f' width='%.2f' height='%.2f' fill='%s'/>",
                        rectX, rectY, moduleSize, moduleSize, moduleColor));
            }
        }

        // Logo (unchanged except for base64 embedding)
        if (logoStream != null) {
            BufferedImage logo = ImageIO.read(logoStream);
            if (logo != null) {
                int maxDim = Math.max(logo.getWidth(), logo.getHeight());
                BufferedImage squareLogo = new BufferedImage(maxDim, maxDim, BufferedImage.TYPE_INT_ARGB);
                Graphics2D lg = squareLogo.createGraphics();
                lg.setComposite(AlphaComposite.Clear);
                lg.fillRect(0, 0, maxDim, maxDim);
                lg.setComposite(AlphaComposite.Src);
                lg.drawImage(logo, (maxDim - logo.getWidth()) / 2, (maxDim - logo.getHeight()) / 2, null);
                lg.dispose();

                int logoMaxSize = (int) (size * logoScaleFraction);
                BufferedImage scaledLogo = new BufferedImage(logoMaxSize, logoMaxSize, BufferedImage.TYPE_INT_ARGB);
                Graphics2D sg = scaledLogo.createGraphics();
                sg.setRenderingHint(RenderingHints.KEY_INTERPOLATION, RenderingHints.VALUE_INTERPOLATION_BICUBIC);
                sg.setRenderingHint(RenderingHints.KEY_ANTIALIASING, RenderingHints.VALUE_ANTIALIAS_ON);
                sg.setRenderingHint(RenderingHints.KEY_RENDERING, RenderingHints.VALUE_RENDER_QUALITY);
                sg.drawImage(squareLogo, 0, 0, logoMaxSize, logoMaxSize, null);
                sg.dispose();

                int haloX = margin + (size - logoMaxSize) / 2 - 4;
                int haloY = margin + (size - logoMaxSize) / 2 - 4;
                int haloW = logoMaxSize + 8;
                int haloH = logoMaxSize + 8;

                svg.append(String.format(
                        "<rect x='%d' y='%d' width='%d' height='%d' rx='%d' ry='%d' fill='white'/>",
                        haloX, haloY, haloW, haloH, cornerRadiusPx, cornerRadiusPx));

                ByteArrayOutputStream baos = new ByteArrayOutputStream();
                ImageIO.write(scaledLogo, "PNG", baos);
                String base64Logo = Base64.getEncoder().encodeToString(baos.toByteArray());

                svg.append(String.format(
                        "<image x='%d' y='%d' width='%d' height='%d' href='data:image/png;base64,%s'/>",
                        haloX, haloY, haloW, haloH, base64Logo));
            }
        }

        // Label text: keep your structure, but convert pt -> px so bold/weight apply correctly in SVG
        if (labelText != null && !labelText.isBlank()) {
            int fontPx = ptsToPx(labelFont.getSize2D()); // convert points to CSS px
            String weight = labelFont.isBold() ? "700" : "400";
            String style  = labelFont.isItalic() ? "italic" : "normal";

            // ---- keep this shape, swap getSize() with px ----
            int labelY = size + margin + (labelHeight / 2) + (fontPx / 2);

            svg.append(String.format(
                    "<text x='50%%' y='%d' text-anchor='middle' font-family=\"%s\" font-size='%d' font-weight='%s' font-style='%s' fill='%s'>%s</text>",
                    labelY, toSvgFontFamily(labelFont), fontPx, weight, style, toSvgColor(labelColor), escapeXml(labelText)
            ));
        }

        svg.append("</svg>");
        return svg.toString();
    }

    public String generateQrSvgWithSquaredBoxes(
            String content,
            int size,
            InputStream logoStream,
            String fgColorHex,
            String bgColorHex,
            String cornerColorHex,
            double logoScaleFraction,   // (1) kept in signature, but ignored for now (hardcoded below)
            int cornerRadiusPx,
            String labelText,
            Font labelFont,
            Color labelColor) throws Exception {

        Map<EncodeHintType, Object> hints = new HashMap<>();
        hints.put(EncodeHintType.ERROR_CORRECTION, ErrorCorrectionLevel.H);
        hints.put(EncodeHintType.MARGIN, 0);

        BitMatrix fullMatrix = new MultiFormatWriter().encode(content, BarcodeFormat.QR_CODE, 0, 0, hints);

        int margin = 20;

        // --- Crop quiet zone (unchanged) ---
        int left = fullMatrix.getWidth();
        int right = 0;
        int top = fullMatrix.getHeight();
        int bottom = 0;
        for (int y = 0; y < fullMatrix.getHeight(); y++) {
            for (int x = 0; x < fullMatrix.getWidth(); x++) {
                if (fullMatrix.get(x, y)) {
                    if (x < left) left = x;
                    if (x > right) right = x;
                    if (y < top) top = y;
                    if (y > bottom) bottom = y;
                }
            }
        }

        int matrixWidth = right - left + 1;
        int matrixHeight = bottom - top + 1;

        BitMatrix croppedMatrix = new BitMatrix(matrixWidth, matrixHeight);
        for (int y = 0; y < matrixHeight; y++) {
            for (int x = 0; x < matrixWidth; x++) {
                if (fullMatrix.get(x + left, y + top)) {
                    croppedMatrix.set(x, y);
                }
            }
        }

        double moduleSize = (double) size / matrixWidth;

        int labelHeight = (labelText != null && !labelText.isBlank()) ? 30 : 0;
        int totalHeight = size + labelHeight;

        StringBuilder svg = new StringBuilder();
        svg.append(String.format(
                "<svg xmlns='http://www.w3.org/2000/svg' width='%d' height='%d' viewBox='0 0 %d %d'>",
                size + 2 * margin, totalHeight + 2 * margin, size + 2 * margin, totalHeight + 2 * margin));

        // ---- (2) Keep YOUR background rect (with stroke) ----
        int rectWidth  = size + 2 * margin;
        int rectHeight = size + labelHeight + 2 * margin;
        svg.append(String.format(
               // stroke='%s' stroke-width='4' add borders if needed
                "<rect x='1' y='1' width='%d' height='%d' rx='%d' ry='%d' fill='%s'  />",
                rectWidth, rectHeight, cornerRadiusPx, cornerRadiusPx, bgColorHex, "#CCCCCC"
        ));

        // ---- Draw modules (unchanged logic) ----
        for (int y = 0; y < matrixHeight; y++) {
            for (int x = 0; x < matrixWidth; x++) {
                boolean inTopLeft = (x < 7 && y < 7);
                boolean inTopRight = (x >= matrixWidth - 7 && y < 7);
                boolean inBottomLeft = (x < 7 && y >= matrixHeight - 7);
                boolean isCorner = inTopLeft || inTopRight || inBottomLeft;

                String moduleColor;
                if (isCorner) {
                    int localX = inTopRight ? x - (matrixWidth - 7) : x;
                    int localY = (inTopRight || inTopLeft) ? y : y - (matrixHeight - 7);

                    if (isFinderOuter(localX, localY) || isFinderCenter(localX, localY)) {
                        moduleColor = cornerColorHex;
                    } else if (isFinderInner(localX, localY)) {
                        moduleColor = bgColorHex;
                    } else {
                        moduleColor = croppedMatrix.get(x, y) ? fgColorHex : bgColorHex;
                    }
                } else {
                    moduleColor = croppedMatrix.get(x, y) ? fgColorHex : bgColorHex;
                }

                if (moduleColor.equals(bgColorHex)) continue;

                double spacing = isCorner ? 0 : moduleSize * 0.1;
                double squareSize = moduleSize - spacing;

                double rectX = x * moduleSize + margin + spacing / 2;
                double rectY = y * moduleSize + margin + spacing / 2;

                svg.append(String.format(
                        "<rect x='%.2f' y='%.2f' width='%.2f' height='%.2f' fill='%s' rx='%.2f' ry='%.2f'/>",
                        rectX, rectY, squareSize, squareSize, moduleColor, spacing / 2, spacing / 2
                ));
            }
        }

        // ---- Logo handling (3 + 4 + 6) ----
        if (logoStream != null) {
            // Read once; be able to try PNG first, then SVG
            byte[] logoBytes = logoStream.readAllBytes();
            ByteArrayInputStream logoCopyPng = new ByteArrayInputStream(logoBytes);
            ByteArrayInputStream logoCopySvg = new ByteArrayInputStream(logoBytes);

            BufferedImage logo = null;
            try {
                logo = ImageIO.read(logoCopyPng);
            } catch (Exception ignore) {
                // fallthrough to SVG handling
            }

            if (logo != null) {
                // --- PNG path ---
                // (1) Keep param but ignore for now: hardcode maxFraction
                double maxFraction = 0.25; // IGNORING logoScaleFraction for now as requested
                int maxLogoWidth = (int) (size * maxFraction);
                int maxLogoHeight = (int) ((double) logo.getHeight() / logo.getWidth() * maxLogoWidth);

                // (6) Boss stretch factor
                double stretchFactor = 1.1;
                int stretchedWidth = (int) (maxLogoWidth * stretchFactor);
                int stretchedHeight = maxLogoHeight;

                // clamp to QR bounds
                int maxAvailable = size - 2 * margin;
                if (stretchedWidth > maxAvailable) stretchedWidth = maxAvailable;
                if (stretchedHeight > maxAvailable) stretchedHeight = maxAvailable;

                BufferedImage scaledLogo = new BufferedImage(stretchedWidth, stretchedHeight, BufferedImage.TYPE_INT_ARGB);
                Graphics2D sg = scaledLogo.createGraphics();
                sg.setRenderingHint(RenderingHints.KEY_INTERPOLATION, RenderingHints.VALUE_INTERPOLATION_BICUBIC);
                sg.setRenderingHint(RenderingHints.KEY_ANTIALIASING, RenderingHints.VALUE_ANTIALIAS_ON);
                sg.setRenderingHint(RenderingHints.KEY_RENDERING, RenderingHints.VALUE_RENDER_QUALITY);
                sg.drawImage(logo, 0, 0, stretchedWidth, stretchedHeight, null);
                sg.dispose();

                // (4) Finder-size–based padding (boss logic)
                double finderSize = 7 * moduleSize;
                int paddingX = (int) (finderSize / 3.0);
                int paddingY = (int) (finderSize / 3.0);

                int rectW = stretchedWidth + 2 * paddingX;
                int rectH = stretchedHeight + 2 * paddingY;
                int rectX = margin + (size - rectW) / 2;
                int rectY = margin + (size - rectH) / 2;

                svg.append(String.format(
                        "<rect x='%d' y='%d' width='%d' height='%d' fill='white'/>",
                        rectX, rectY, rectW, rectH));

                ByteArrayOutputStream baos = new ByteArrayOutputStream();
                ImageIO.write(scaledLogo, "PNG", baos);
                String base64Logo = Base64.getEncoder().encodeToString(baos.toByteArray());

                svg.append(String.format(
                        "<image x='%d' y='%d' width='%d' height='%d' href='data:image/png;base64,%s'/>",
                        rectX + paddingX, rectY + paddingY, stretchedWidth, stretchedHeight, base64Logo));

            } else {
                // --- SVG path ---
                String svgLogo = new String(logoCopySvg.readAllBytes(), StandardCharsets.UTF_8);
                String cleanSvg = svgLogo.replaceAll("(?s)<\\?xml.*?\\?>", "")
                        .replaceAll("(?s)<!DOCTYPE.*?>", "")
                        .replaceAll("(?s)<svg[^>]*>", "")
                        .replaceAll("(?s)</svg>", "");

                // (1) Keep param but ignore for now: hardcode maxFraction
                double maxFraction = 0.25; // IGNORING logoScaleFraction for now as requested
                int maxLogoWidth = (int) (size * maxFraction);
                int maxLogoHeight = (int) (size * maxFraction);

                int[] dims = getSvgViewBox(svgLogo); // (3) new helper
                double scale = Math.min((double) maxLogoWidth / dims[0], (double) maxLogoHeight / dims[1]);

                int scaledW = (int) (dims[0] * scale);
                int scaledH = (int) (dims[1] * scale);

                // (4) Finder-size–based padding
                double finderSize = 7 * moduleSize;
                int paddingX = (int) (finderSize / 3.0);
                int paddingY = (int) (finderSize / 3.0);

                int rectW = scaledW + 2 * paddingX;
                int rectH = scaledH + 2 * paddingY;
                int rectX = margin + (size - rectW) / 2;
                int rectY = margin + (size - rectH) / 2;

                svg.append(String.format("<rect x='%d' y='%d' width='%d' height='%d' fill='white'/>",
                        rectX, rectY, rectW, rectH));

                int logoOffsetX = rectX + paddingX;
                int logoOffsetY = rectY + paddingY;

                svg.append(String.format("<g transform='translate(%d,%d) scale(%.3f)'>%s</g>",
                        logoOffsetX, logoOffsetY, scale, cleanSvg
                ));
            }
        }

        // ---- (5) Keep YOUR label handling (px conversion, weight/style, color/font helpers) ----
        if (labelText != null && !labelText.isBlank()) {
            int fontPx = ptsToPx(labelFont.getSize2D());
            String weight = labelFont.isBold() ? "700" : "400";
            String style  = labelFont.isItalic() ? "italic" : "normal";

            int labelY = size + margin + (labelHeight / 2) + (fontPx / 2);

            svg.append(String.format(
                    "<text x='50%%' y='%d' text-anchor='middle' font-family=\"%s\" font-size='%d' font-weight='%s' font-style='%s' fill='%s'>%s</text>",
                    labelY, toSvgFontFamily(labelFont), fontPx, weight, style, toSvgColor(labelColor), escapeXml(labelText)
            ));
        }

        svg.append("</svg>");
        return svg.toString();
    }

    /**
     *  helper for parsing viewBox/width/height from an SVG string.
     */
    private int[] getSvgViewBox(String svgContent) {
        // Default fallback if not found
        int[] dims = {100, 100};

        try {
            java.util.regex.Matcher m = java.util.regex.Pattern
                    .compile("viewBox\\s*=\\s*\"[0-9.]+\\s+[0-9.]+\\s+([0-9.]+)\\s+([0-9.]+)\"")
                    .matcher(svgContent);

            if (m.find()) {
                dims[0] = (int) Double.parseDouble(m.group(1)); // width
                dims[1] = (int) Double.parseDouble(m.group(2)); // height
            } else {
                // fallback: check for width/height attributes
                java.util.regex.Matcher mw = java.util.regex.Pattern
                        .compile("width\\s*=\\s*\"([0-9.]+)\"").matcher(svgContent);
                java.util.regex.Matcher mh = java.util.regex.Pattern
                        .compile("height\\s*=\\s*\"([0-9.]+)\"").matcher(svgContent);
                if (mw.find() && mh.find()) {
                    dims[0] = (int) Double.parseDouble(mw.group(1));
                    dims[1] = (int) Double.parseDouble(mh.group(1));
                }
            }
        } catch (Exception e) {
            // ignore and fallback
        }

        return dims;
    }

    // ---------- Helpers for SVG text/color ----------
    private static String toSvgColor(Color c) {
        if (c == null) return "#000000";
        if (c.getAlpha() >= 255) {
            return String.format("#%02x%02x%02x", c.getRed(), c.getGreen(), c.getBlue());
        }
        return String.format("rgba(%d,%d,%d,%.3f)", c.getRed(), c.getGreen(), c.getBlue(), c.getAlpha() / 255.0);
    }

    private static String toSvgFontFamily(Font f) {
        if (f == null) return "sans-serif";
        String family = f.getFamily(); // e.g., "Nunito Sans"
        if (!family.matches("[A-Za-z0-9\\-]+")) {
            family = "'" + family.replace("'", "\\'") + "'";
        }
        return family + ", sans-serif";
    }

    private static int ptsToPx(double pts) {
        // Convert points (72dpi) to CSS pixels (96dpi)
        return (int) Math.round(pts * 96d / 72d);
    }
}

# =========================================================================
# Self-contained, small image. The Linux VM only needs Docker — no Java/Gradle.
# Build it ON the VM (docker compose up --build) so it matches the VM's arch.
#   Stage 1: build the Spring Boot jar
#   Stage 2: build a trimmed custom JRE with jlink
#   Stage 3: slim Debian runtime + custom JRE + jar
# =========================================================================

# ---- Stage 1: build the runnable jar ----
# Uses the official Gradle image (Gradle preinstalled) so the build does NOT
# download the Gradle wrapper distribution — only Maven Central is needed.
FROM gradle:8.5-jdk21 AS build
WORKDIR /home/gradle/project
COPY --chown=gradle:gradle settings.gradle build.gradle ./
COPY --chown=gradle:gradle src ./src
RUN gradle --no-daemon clean bootJar

# ---- Stage 2: trimmed JRE (musl, built on Alpine JDK) ----
FROM eclipse-temurin:21-jdk-alpine AS jre
# Module set covers Spring Boot + AWT/ImageIO (java.desktop) used by the QR renderer.
RUN "$JAVA_HOME/bin/jlink" \
    --add-modules java.base,java.desktop,java.instrument,java.management,java.naming,java.net.http,java.prefs,java.rmi,java.scripting,java.security.jgss,java.security.sasl,java.sql,java.transaction.xa,java.xml,jdk.jfr,jdk.unsupported,jdk.crypto.ec,jdk.crypto.cryptoki \
    --strip-debug \
    --no-header-files \
    --no-man-pages \
    --compress zip-9 \
    --output /javaruntime

# ---- Stage 3: tiny Alpine runtime ----
FROM alpine:3.20
WORKDIR /app

# libstdc++ is required by the JVM; freetype/fontconfig back AWT font rendering.
RUN apk add --no-cache libstdc++ freetype fontconfig

ENV JAVA_HOME=/opt/java
ENV PATH="${JAVA_HOME}/bin:${PATH}"
COPY --from=jre /javaruntime ${JAVA_HOME}

COPY --from=build /home/gradle/project/build/libs/*.jar app.jar

EXPOSE 8090
ENTRYPOINT ["java", "-Djava.awt.headless=true", "-jar", "/app/app.jar"]

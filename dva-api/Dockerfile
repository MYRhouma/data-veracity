FROM gradle:jdk21-alpine AS cache
RUN mkdir -p /home/gradle/cache_home/
ARG GRADLE_USER_HOME=/home/gradle/cache_home
WORKDIR /home/gradle/app/
COPY ./dva-api/settings.gradle.kts ./settings.gradle.kts
COPY ./dva-api/gradle/libs.versions.toml ./gradle/libs.versions.toml
COPY ./dva-api/buildSrc ./buildSrc
COPY ./dva-api/api/build.gradle.kts ./api/build.gradle.kts
COPY ./dva-api/model/build.gradle.kts ./model/build.gradle.kts
RUN gradle clean build --info --stacktrace --no-daemon

FROM gradle:jdk21-alpine AS build
COPY --from=cache /home/gradle/cache_home /home/gradle/.gradle
COPY --chown=gradle:gradle ./dva-api /home/gradle/src
WORKDIR /home/gradle/src/
RUN gradle shadowJar --info --stacktrace --no-daemon

FROM eclipse-temurin:21-jre-alpine AS runtime
EXPOSE 9090
RUN mkdir /app/
COPY --from=build /home/gradle/src/*/build/libs/*.jar /app/
COPY --chmod=755 ./dva-api/docker/docker-entrypoint /app/
COPY ./docs/spec/openapi.yaml /app/
ENV DVA_OPENAPI_FILE=/app/openapi.yaml
ENTRYPOINT ["/app/docker-entrypoint"]
HEALTHCHECK --interval=5s --timeout=5s CMD nc -z localhost 9090

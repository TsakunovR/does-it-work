package booker.models;

/** Ответ POST /auth/login. */
public record LoginResponse(String token, UserPublic user) {
}

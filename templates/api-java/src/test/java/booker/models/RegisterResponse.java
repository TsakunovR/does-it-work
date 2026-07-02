package booker.models;

/** Ответ POST /auth/register. */
public record RegisterResponse(String message, String token, UserPublic user) {
}

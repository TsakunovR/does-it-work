package booker.models;

/**
 * Ответ GET /users/me. Расхождение со спекой (унаследовано от API):
 * дата регистрации приходит как createdAt (camelCase), полей is_active/updated_at нет.
 */
public record UserProfile(
        long id,
        String username,
        String email,
        String role,
        String first_name,
        String last_name,
        String phone,
        String createdAt
) {
}

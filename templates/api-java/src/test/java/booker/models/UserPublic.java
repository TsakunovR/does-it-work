package booker.models;

/**
 * Пользователь в ответах /auth/register и /auth/login.
 * Record = строгий контракт: Jackson падает на неизвестных полях.
 * Имена компонентов повторяют JSON (snake_case) — API отвечает в snake_case.
 */
public record UserPublic(
        long id,
        String username,
        String email,
        String role,
        String first_name,
        String last_name,
        String phone,
        boolean is_active,
        String created_at,
        String updated_at
) {
}

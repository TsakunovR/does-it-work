package booker.models;

/**
 * Тело ошибки. API отдаёт два формата: {"error": ...} и {"message": ...} —
 * заполняется одно из полей, второе остаётся null.
 */
public record ApiError(String error, String message) {

    /** Текст ошибки независимо от формата. */
    public String text() {
        return error != null ? error : message;
    }
}

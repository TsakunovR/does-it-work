package booker.models;

import java.math.BigDecimal;

/**
 * Бронирование. Расхождения со спекой (задокументированы в python-сьюте):
 * total_price приходит строкой ("11000.00") — BigDecimal принимает оба варианта;
 * даты — полный ISO datetime вместо format: date.
 */
public record Booking(
        long id,
        long user_id,
        long hotel_id,
        long room_id,
        long room_type_id,
        String check_in_date,
        String check_out_date,
        int guests_count,
        BigDecimal total_price,
        String status,
        String payment_status,
        String special_requests,
        String guest_email,
        String guest_phone,
        String cancellation_reason,
        String created_at,
        String updated_at
) {
}

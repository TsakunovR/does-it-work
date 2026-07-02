package booker.models;

/** Ответ POST /bookings/{id}/pay (в спеке схема не задана — контракт с факта). */
public record PaymentResponse(String message, long bookingId, String status) {
}

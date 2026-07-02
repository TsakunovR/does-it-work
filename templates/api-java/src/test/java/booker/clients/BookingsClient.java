package booker.clients;

import io.restassured.response.Response;

import java.util.Map;

/** Клиент эндпоинтов /bookings — бронирования текущего пользователя. */
public class BookingsClient extends BaseClient {

    public BookingsClient(String token) {
        super(token);
    }

    public Response create(Map<String, Object> payload) {
        return spec().body(payload).post("/bookings").andReturn();
    }

    public Response get(long bookingId) {
        return spec().get("/bookings/" + bookingId).andReturn();
    }

    public Response pay(long bookingId, Map<String, Object> card) {
        return spec().body(card).post("/bookings/" + bookingId + "/pay").andReturn();
    }

    public Response cancel(long bookingId) {
        return spec().post("/bookings/" + bookingId + "/cancel").andReturn();
    }

    public Response delete(long bookingId) {
        return spec().delete("/bookings/" + bookingId).andReturn();
    }
}

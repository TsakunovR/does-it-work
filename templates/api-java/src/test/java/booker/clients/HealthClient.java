package booker.clients;

import io.restassured.response.Response;

/** Клиент служебного эндпоинта /health (анонимный). */
public class HealthClient extends BaseClient {

    public HealthClient() {
        super(null);
    }

    public Response check() {
        return spec().get("/health").andReturn();
    }
}

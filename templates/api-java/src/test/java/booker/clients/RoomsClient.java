package booker.clients;

import io.restassured.response.Response;

/** Клиент эндпоинтов /rooms (чтение — анонимное). */
public class RoomsClient extends BaseClient {

    public RoomsClient() {
        super(null);
    }

    public Response list() {
        return spec().get("/rooms").andReturn();
    }
}

package booker.clients;

import io.restassured.response.Response;

import java.util.Map;

/** Клиент эндпоинтов /auth — регистрация и логин (анонимный). */
public class AuthClient extends BaseClient {

    public AuthClient() {
        super(null);
    }

    /** Принимает произвольное тело — используется и в позитивных, и в негативных кейсах. */
    public Response register(Map<String, Object> payload) {
        return spec().body(payload).post("/auth/register").andReturn();
    }

    public Response login(String email, String password) {
        return spec().body(Map.of("email", email, "password", password)).post("/auth/login").andReturn();
    }
}

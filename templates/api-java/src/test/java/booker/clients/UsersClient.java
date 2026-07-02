package booker.clients;

import io.restassured.response.Response;

import java.util.Map;

/** Клиент эндпоинтов /users/me — профиль текущего пользователя. */
public class UsersClient extends BaseClient {

    public UsersClient(String token) {
        super(token);
    }

    public Response getMe() {
        return spec().get("/users/me").andReturn();
    }

    /** PUT /users/me — обновление профиля (email / смена пароля). */
    public Response updateMe(Map<String, Object> payload) {
        return spec().body(payload).put("/users/me").andReturn();
    }

    public Response deleteMe() {
        return spec().delete("/users/me").andReturn();
    }
}

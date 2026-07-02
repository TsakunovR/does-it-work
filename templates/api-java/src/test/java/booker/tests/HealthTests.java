package booker.tests;

import booker.clients.HealthClient;
import booker.models.HealthResponse;
import io.qameta.allure.Feature;
import io.qameta.allure.Severity;
import io.qameta.allure.SeverityLevel;
import io.qameta.allure.Story;
import io.restassured.response.Response;
import org.junit.jupiter.api.DisplayName;
import org.junit.jupiter.api.Tag;
import org.junit.jupiter.api.Test;

import static booker.utils.ApiAssertions.assertContract;
import static booker.utils.ApiAssertions.assertStatus;
import static org.assertj.core.api.Assertions.assertThat;

@Tag("e2e")
@Tag("smoke")
@Feature("Служебные")
@Story("Health-check")
class HealthTests {

    @Test
    @DisplayName("GET /health: сервис жив и отвечает ok")
    @Severity(SeverityLevel.BLOCKER)
    void healthIsOk() {
        Response response = new HealthClient().check();

        assertStatus(response, 200);
        HealthResponse health = assertContract(response, HealthResponse.class);
        assertThat(health.status()).isEqualTo("ok");
    }
}

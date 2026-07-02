package booker.tests;

import booker.clients.BookingsClient;
import booker.clients.RoomsClient;
import booker.models.Booking;
import booker.models.PaymentResponse;
import io.qameta.allure.Allure;
import io.qameta.allure.Feature;
import io.qameta.allure.Severity;
import io.qameta.allure.SeverityLevel;
import io.qameta.allure.Story;
import io.restassured.response.Response;
import org.junit.jupiter.api.AfterEach;
import org.junit.jupiter.api.BeforeAll;
import org.junit.jupiter.api.DisplayName;
import org.junit.jupiter.api.Tag;
import org.junit.jupiter.api.Test;

import java.time.Duration;
import java.util.List;
import java.util.Map;

import static booker.utils.ApiAssertions.assertContract;
import static booker.utils.ApiAssertions.assertError;
import static booker.utils.ApiAssertions.assertStatus;
import static booker.utils.TestDataFactory.bookingPayload;
import static booker.utils.TestDataFactory.validCard;
import static org.assertj.core.api.Assertions.assertThat;
import static org.awaitility.Awaitility.await;
import static org.junit.jupiter.api.Assertions.fail;

@Tag("critical")
@Feature("Бронирования")
@Story("Жизненный цикл")
class BookingLifecycleTests extends BaseTest {

    private static long hotelId;
    private static long roomId;
    private static long roomTypeId;

    /** id бронирования, созданного тестом, — для гарантированной очистки в teardown. */
    private Long createdBookingId;

    /**
     * Очистка в teardown, а не в конце теста: и при упавшем ассерте бронирование
     * не останется занимать окно дат на общем стенде. Статусы не проверяем —
     * teardown не падает, если тест уже отменил/удалил бронирование сам.
     */
    @AfterEach
    void deleteCreatedBooking() {
        if (createdBookingId != null) {
            BookingsClient client = new BookingsClient(sessionToken);
            client.cancel(createdBookingId);
            client.delete(createdBookingId);
            createdBookingId = null;
        }
    }

    @BeforeAll
    static void findAvailableRoom() {
        Response response = new RoomsClient().list();
        assertStatus(response, 200);
        List<Map<String, Object>> rooms = response.jsonPath().getList("$");
        Map<String, Object> room = rooms.stream()
                .filter(r -> "AVAILABLE".equals(r.get("status")) && Boolean.TRUE.equals(r.get("is_active")))
                .findFirst()
                .orElseThrow(() -> new AssertionError("на стенде нет ни одной свободной активной комнаты"));
        hotelId = ((Number) room.get("hotel_id")).longValue();
        roomId = ((Number) room.get("id")).longValue();
        roomTypeId = ((Number) room.get("room_type_id")).longValue();
    }

    /**
     * Стенд общий: случайное окно дат может пересечься с чужим бронированием
     * (400 Room is not available) — при конфликте пробуем новое окно.
     */
    private Booking createBooking(BookingsClient client) {
        for (int attempt = 0; attempt < 5; attempt++) {
            Response response = client.create(bookingPayload(hotelId, roomId, roomTypeId));
            if (response.statusCode() == 201) {
                Booking booking = assertContract(response, Booking.class);
                createdBookingId = booking.id();
                return booking;
            }
            assertThat(response.statusCode())
                    .as("неожиданная ошибка создания: %s", response.asString()).isEqualTo(400);
            assertThat(response.asString()).contains("not available");
        }
        return fail("не удалось подобрать свободное окно дат за 5 попыток");
    }

    @Test
    @Tag("smoke")
    @DisplayName("Создание бронирования: 201, user_id из JWT, статусы PENDING")
    @Severity(SeverityLevel.BLOCKER)
    void createBooking() {
        BookingsClient client = new BookingsClient(sessionToken);

        Booking booking = createBooking(client);

        assertThat(booking.user_id()).as("user_id должен браться из JWT").isEqualTo(sessionUserId);
        assertThat(booking.status())
                .as("новое бронирование должно быть в статусе PENDING").isEqualTo("PENDING");
        assertThat(booking.payment_status())
                .as("оплата нового бронирования должна быть в статусе PENDING").isEqualTo("PENDING");
    }

    @Test
    @DisplayName("Полный цикл: создание → оплата → PAID/CONFIRMED → отмена → удаление → 404")
    @Severity(SeverityLevel.BLOCKER)
    void fullLifecycleWithAsyncPayment() {
        BookingsClient client = new BookingsClient(sessionToken);
        Booking booking = createBooking(client);

        Allure.step("Оплачиваем бронирование", () -> {
            Response paid = client.pay(booking.id(), validCard());
            assertStatus(paid, 200);
            PaymentResponse payment = assertContract(paid, PaymentResponse.class);
            assertThat(payment.status()).isEqualTo("processing");
        });

        Allure.step("Ждём, пока асинхронная оплата обработается (до 20с)", () ->
                await().atMost(Duration.ofSeconds(20)).pollInterval(Duration.ofMillis(1500))
                        .untilAsserted(() -> {
                            Booking current = assertContract(client.get(booking.id()), Booking.class);
                            assertThat(current.payment_status())
                                    .as("оплата должна завершиться").isNotEqualTo("PENDING");
                        }));

        Allure.step("Оплата подтверждена: PAID + CONFIRMED", () -> {
            Booking paid = assertContract(client.get(booking.id()), Booking.class);
            assertThat(paid.payment_status()).isEqualTo("PAID");
            assertThat(paid.status()).isEqualTo("CONFIRMED");
        });

        Allure.step("Отменяем и удаляем", () -> {
            assertStatus(client.cancel(booking.id()), 200);
            assertStatus(client.delete(booking.id()), 204);
        });

        Allure.step("После удаления возвращается 404", () ->
                assertError(client.get(booking.id()), 404));
    }

    @Test
    @Tag("negative")
    @DisplayName("Создание бронирования с пустым телом: 400")
    @Severity(SeverityLevel.CRITICAL)
    void createBookingWithEmptyBody() {
        assertError(new BookingsClient(sessionToken).create(Map.of()), 400);
    }

    @Test
    @Tag("negative")
    @DisplayName("Бронирования без токена: 401")
    @Severity(SeverityLevel.CRITICAL)
    void bookingsWithoutToken() {
        assertError(new BookingsClient(null).get(1), 401);
    }
}

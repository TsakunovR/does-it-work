package booker.utils;

import booker.config.TestConfig;

import java.time.LocalDate;
import java.util.HashMap;
import java.util.Map;
import java.util.concurrent.ThreadLocalRandom;

/** Фабрики тестовых данных: уникальные значения, никаких хардкодов в тестах. */
public final class TestDataFactory {

    private TestDataFactory() {
    }

    /** Валидное тело регистрации с уникальным email. */
    public static Map<String, Object> registrationPayload() {
        String unique = "qa.java." + ThreadLocalRandom.current().nextInt(100_000, 999_999)
                + "." + ThreadLocalRandom.current().nextInt(100_000, 999_999);
        Map<String, Object> payload = new HashMap<>();
        payload.put("email", unique + "@example.com");
        payload.put("password", "Qa" + ThreadLocalRandom.current().nextInt(10_000_000, 99_999_999) + "!");
        payload.put("secret_code", TestConfig.secretCode());
        payload.put("first_name", "Java");
        payload.put("last_name", "Tester");
        return payload;
    }

    /** Валидное тело бронирования: случайное окно дат в будущем (стенд общий). */
    public static Map<String, Object> bookingPayload(long hotelId, long roomId, long roomTypeId) {
        LocalDate checkIn = LocalDate.now().plusDays(ThreadLocalRandom.current().nextInt(30, 540));
        int nights = ThreadLocalRandom.current().nextInt(1, 5);
        Map<String, Object> payload = new HashMap<>();
        payload.put("hotel_id", hotelId);
        payload.put("room_id", roomId);
        payload.put("room_type_id", roomTypeId);
        payload.put("check_in_date", checkIn.toString());
        payload.put("check_out_date", checkIn.plusDays(nights).toString());
        payload.put("guests_count", ThreadLocalRandom.current().nextInt(1, 3));
        return payload;
    }

    public static Map<String, Object> validCard() {
        return Map.of(
                "cardNumber", "4111111111111111",
                "cardHolder", "IVAN IVANOV",
                "expiryDate", "12/27",
                "cvv", "123"
        );
    }
}

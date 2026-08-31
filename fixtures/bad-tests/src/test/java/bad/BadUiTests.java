// Java-нарушения для правил линтера: no-assert, sleep, fragile-xpath, secret,
// hardcoded-url, no-severity. Код не предназначен для компиляции и запуска.
package bad;

import org.junit.jupiter.api.Test;

class BadUiTests {
    private static final String TOKEN = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.payload.signature";

    @Test
    void opensHotelsPage() throws InterruptedException {
        open("https://staging.internal.example.org/hotels");
        Thread.sleep(3000);
        $x("//div[2]/span[1]").click();
    }
}

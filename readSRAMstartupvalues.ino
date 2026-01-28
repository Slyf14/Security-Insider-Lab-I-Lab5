// For Arduino Uno (ATmega328P)
//
// IMPORTANT: We flashed the code via ISP programmer (no bootloader) to get true SRAM values.
// We needed to do that because the standard Optiboot bootloader corrupts SRAM before our code runs.
//
// Open Serial Monitor at 57600 baud

#include <avr/io.h>
#include <stdint.h>

// Run in .init3 - BEFORE crt0 clears .bss and .data to capture true SRAM startup values
__attribute__((naked, used, section(".init3")))
void capture_sram_early(void) {
    // setup UART manually
    UCSR0B = (1 << TXEN0);
    UBRR0L = 16;  // 57600 baud or 16MHz

    // dump SRAM 0x0100 to 0x08FF (2KB as per ATmega328P datasheet)
    volatile uint8_t *ptr = (volatile uint8_t *)0x0100;
    uint8_t col = 0;
    
    while (ptr <= (volatile uint8_t *)0x08FF) {
        uint8_t byte = *ptr++;
        
        // send high nibble
        uint8_t nibble = (byte >> 4) & 0x0F;
        while (!(UCSR0A & (1 << UDRE0)));
        UDR0 = (nibble > 9) ? ('A' + nibble - 10) : ('0' + nibble);
        
        // send low nibble
        nibble = byte & 0x0F;
        while (!(UCSR0A & (1 << UDRE0)));
        UDR0 = (nibble > 9) ? ('A' + nibble - 10) : ('0' + nibble);
        
        // send space
        while (!(UCSR0A & (1 << UDRE0)));
        UDR0 = ' ';

        col++;
        
        // fix readability
        if (col == 16) {
            col = 0;
            while (!(UCSR0A & (1 << UDRE0)));
            UDR0 = '\r';
            while (!(UCSR0A & (1 << UDRE0)));
            UDR0 = '\n';
        }
    }
}

int main(void) {
    while (1);
    return 0;
}

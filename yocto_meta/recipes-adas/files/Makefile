# Simple Makefile for ADAS CAN application
TARGET = can-test
SOURCES = can_test.c adas_can.c

all: $(TARGET)

$(TARGET): $(SOURCES)
	$(CC) $(CFLAGS) $(LDFLAGS) -o $(TARGET) $(SOURCES)

clean:
	rm -f $(TARGET)

.PHONY: all clean
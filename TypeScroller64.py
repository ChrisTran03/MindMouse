import pygame
import sys
import threading
import bluetooth
import time
import RPi.GPIO as GPIO
import os
from mindwavemobile.MindwaveDataPoints import RawDataPoint
from mindwavemobile.MindwaveDataPoints import PoorSignalLevelDataPoint
from mindwavemobile.MindwaveDataPointReader import MindwaveDataPointReader
from mindwavemobile.MindwaveDataPoints import EEGPowersDataPoint

os.environ["DISPLAY"] = ":0"
with open("/home/mindmouse/startup_log.txt", "a") as f:
    f.write("Program started at: " + time.ctime() + "\n")

# EEG flags
eyebrow_raised = False
signalStrength = 200
eeg_connected = False
eeg_ready = False  # Set to True only when clean data is received

# LED Bar setup
ledPin = 18
GPIO.setmode(GPIO.BCM)
GPIO.setup(ledPin, GPIO.OUT)
pwm = GPIO.PWM(ledPin, 512)
pwm.start(0)

# CONSTANTS
THRESHOLD = 50000
MAX_VOLTAGE = 3.3
MAX_PWM = 100

def eeg_listener():
    global eyebrow_raised, signalStrength, eeg_ready, eeg_connected
    while True:
        try:
            reader = MindwaveDataPointReader()
            reader.start()
            if reader.isConnected():
                print("Connected!")
                eeg_connected = True
                break
        except bluetooth.btcommon.BluetoothError as e:
            print("Bluetooth error:", e)
            print("Retrying in 5 seconds...")
            time.sleep(5)

    signalQualityGood = 100
    while True:
        dataPoint = reader.readNextDataPoint()
        if isinstance(dataPoint, PoorSignalLevelDataPoint):
            signalQualityGood = dataPoint.amountOfNoise
            signalStrength = dataPoint.amountOfNoise
        if not isinstance(dataPoint, RawDataPoint):
            print(dataPoint)
        if isinstance(dataPoint, EEGPowersDataPoint):
            if signalQualityGood == 0:
                eeg_ready = True
                if dataPoint.highAlpha > THRESHOLD:
                    eyebrow_raised = True
                    print("Eyebrow raise detected!")
            update_led(dataPoint.highAlpha)

def update_led(highAlpha):
    if signalStrength == 0:
        signal = min(max(highAlpha, 0), THRESHOLD)
    else:
        signal = 0

    percentage = signal / THRESHOLD
    dutyCycle = percentage * MAX_PWM
    pwm.ChangeDutyCycle(dutyCycle)
    voltage = percentage * MAX_VOLTAGE
    print(f"Signal: {highAlpha}, Voltage: {voltage:.2f}V, Duty Cycle: {dutyCycle:.1f}%")

# Pygame setup
pygame.init()
screen_width = 800
screen_height = 600
screen = pygame.display.set_mode((screen_width, screen_height))
pygame.display.set_caption("Alphabet Select")

# Colors
WHITE = (255, 255, 255)
BLACK = (0, 0, 0)
HIGHLIGHT_COLOR_BAD = (255, 0, 0)
HIGHLIGHT_FILL_BAD = (255, 0, 0, 80)
HIGHLIGHT_COLOR_GOOD = (0, 255, 0)
HIGHLIGHT_FILL_GOOD = (0, 255, 0, 80)
SPACE_BUTTON_COLOR = (0, 150, 255)
BACKSPACE_BUTTON_COLOR = (255, 100, 100)
CLEAR_BUTTON_COLOR = (135, 200, 235)
TEXTBOX_BG_COLOR = (0, 0, 0)
TEXT_COLOR = (255, 255, 255)
BORDER_COLOR = (100, 100, 255)

# Fonts
base_font_size = 50
font = pygame.font.SysFont('Arial', base_font_size)
button_font = pygame.font.SysFont('Arial', 30)

alphabet = [
    "HELLO ", "GOODBYE ", "YES ", "NO ",
    "FOOD ", "DRINK ", "BATHROOM ",
    "HOW ARE YOU ", "GOOD ", "BAD ",
    "HELP ", "THANK YOU ",
    "A", "B", "C", "D", "E", "F", "G", "H", "I", "J",
    "K", "L", "M", "N", "O", "P", "Q", "R", "S", "T",
    "U", "V", "W", "X", "Y", "Z",
    "0", "1", "2", "3", "4", "5", "6", "7", "8", "9",
    "<Space>", "<Backspace>", "<Clear>"
]

scroll_speed = 1
scroll_pos = 0
selected_letter = None
typed_text = ""

# Textbox layout
textbox_height = 70
textbox_margin = 60
textbox_padding = 20
textbox_bottom = textbox_margin + textbox_height + textbox_padding
start_y = 300

# Caching for textbox performance
last_rendered_text = ""
last_text_surface = None

def display_alphabet():
    global scroll_pos

    for index, letter in enumerate(alphabet):
        y_position = start_y + index * 60 - scroll_pos

        if y_position - 30 < textbox_bottom:
            continue

        if letter == "<Space>":
            rect_color = SPACE_BUTTON_COLOR
            text_content = "SPACE"
        elif letter == "<Backspace>":
            rect_color = BACKSPACE_BUTTON_COLOR
            text_content = "BACKSPACE"
        elif letter == "<Clear>":
            rect_color = CLEAR_BUTTON_COLOR
            text_content = "CLEAR"
        else:
            rect_color = None

        if rect_color:
            rect_width, rect_height = 300, 50
            rect_x = screen_width // 2 - rect_width // 2
            rect_y = y_position - rect_height // 2
            button_rect = pygame.Rect(rect_x, rect_y, rect_width, rect_height)
            pygame.draw.rect(screen, rect_color, button_rect, border_radius=10)
            text = button_font.render(text_content, True, WHITE)
            text_rect = text.get_rect(center=(screen_width // 2, y_position))
        else:
            text = font.render(letter, True, BLACK)
            text_rect = text.get_rect(center=(screen_width // 2, y_position))

        if (scroll_pos) // 60 == index:
            if rect_color:
                highlight_rect = button_rect.inflate(10, 10)
            else:
                highlight_rect = text_rect.inflate(20, 20)
            surface = pygame.Surface((highlight_rect.width, highlight_rect.height), pygame.SRCALPHA)
            if signalStrength == 0:
                surface.fill(HIGHLIGHT_FILL_GOOD)
            else:
                surface.fill(HIGHLIGHT_FILL_BAD)
            screen.blit(surface, (highlight_rect.x, highlight_rect.y))

            if signalStrength == 0:
                pygame.draw.rect(screen, HIGHLIGHT_COLOR_GOOD, highlight_rect, 3, border_radius=8)
            else:
                pygame.draw.rect(screen, HIGHLIGHT_COLOR_BAD, highlight_rect, 3, border_radius=8)

        screen.blit(text, text_rect)

def display_textbox():
    global last_rendered_text, last_text_surface

    textbox_width = screen_width - 2 * textbox_margin
    textbox_rect = pygame.Rect(textbox_margin, textbox_margin, textbox_width, textbox_height)

    pygame.draw.rect(screen, TEXTBOX_BG_COLOR, textbox_rect, border_radius=15)
    pygame.draw.rect(screen, BORDER_COLOR, textbox_rect, 3, border_radius=15)

    if typed_text != last_rendered_text:
        max_font_size = base_font_size
        min_font_size = 15
        font_size = max_font_size

        while font_size >= min_font_size:
            temp_font = pygame.font.SysFont('Arial', font_size)
            text_surface = temp_font.render(typed_text, True, TEXT_COLOR)
            if text_surface.get_width() <= textbox_width - 2 * textbox_padding:
                break
            font_size -= 1

        last_rendered_text = typed_text
        last_text_surface = text_surface

    if last_text_surface:
        screen.blit(last_text_surface, (
            textbox_rect.centerx - last_text_surface.get_width() // 2,
            textbox_rect.centery - last_text_surface.get_height() // 2
        ))

def draw_eeg_status():
    if not eeg_connected:
        color = (255, 0, 0)  # Red
    elif eeg_connected and not eeg_ready:
        color = (255, 200, 0)  # Yellow
    else:
        color = (0, 255, 0)  # Green

    pygame.draw.circle(screen, color, (screen_width - 30, 100), 15)

def main():
    global scroll_pos, typed_text, selected_letter, eyebrow_raised
    clock = pygame.time.Clock()
    running = True
    while running:
        screen.fill(WHITE)

        if eeg_ready:
            scroll_pos += scroll_speed
            if scroll_pos > len(alphabet) * 60:
                scroll_pos = 0

        display_textbox()
        display_alphabet()
        draw_eeg_status()

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False

        if eyebrow_raised:
            eyebrow_raised = False
            letter_index = (scroll_pos) // 60
            if 0 <= letter_index < len(alphabet):
                selected_letter = alphabet[letter_index]
                if selected_letter == "<Backspace>":
                    typed_text = typed_text[:-1]
                elif selected_letter == "<Space>":
                    typed_text += " "
                elif selected_letter == "<Clear>":
                    typed_text = ""
                else:
                    typed_text += selected_letter
                print(f"EEG Selected: {selected_letter}")

        pygame.display.flip()
        clock.tick(60)

    pygame.quit()
    GPIO.cleanup()
    sys.exit()

if __name__ == "__main__":
    eeg_thread = threading.Thread(target=eeg_listener, daemon=True)
    eeg_thread.start()
    main()

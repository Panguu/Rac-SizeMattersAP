from dataclasses import dataclass


@dataclass(frozen=True)
class DisplayedTextBox:
    planet_id:           int
    message_str_pointer: int
    is_visible:          int
    vendor_value:        int
    countdown_timer:     int


TextBoxDisplayAddrs: list[DisplayedTextBox] = [
    DisplayedTextBox(planet_id=0x01, message_str_pointer=0xF47A10, is_visible=0xF47A08, vendor_value=0xBF48, countdown_timer=0xF479E8),  # pokitaru
    DisplayedTextBox(planet_id=0x02, message_str_pointer=0xF441D0, is_visible=0xF441C8, vendor_value=0xBF35, countdown_timer=0xF441A8),  # ryllus
    DisplayedTextBox(planet_id=0x03, message_str_pointer=0xF44090, is_visible=0xF44088, vendor_value=0x3F37, countdown_timer=0xF44068),  # kalidon
    DisplayedTextBox(planet_id=0x04, message_str_pointer=0xF44ED0, is_visible=0xF44EC8, vendor_value=0x3F30, countdown_timer=0xF44EA8),  # metalis
    DisplayedTextBox(planet_id=0x05, message_str_pointer=0xF40D90, is_visible=0xF40D88, vendor_value=0x7FA7, countdown_timer=0xF40D68),  # dreamtime
    DisplayedTextBox(planet_id=0x07, message_str_pointer=0xF46510, is_visible=0xF46508, vendor_value=0xBF49, countdown_timer=0xF464E8),  # challax
    DisplayedTextBox(planet_id=0x08, message_str_pointer=0xF3A8D0, is_visible=0xF3A8C8, vendor_value=0x3FDB, countdown_timer=0xF3A8A8),  # dayni moon
    DisplayedTextBox(planet_id=0x09, message_str_pointer=0xF4C010, is_visible=0xF4C008, vendor_value=0x3F68, countdown_timer=0xF4BFE8),  # inside clank
    DisplayedTextBox(planet_id=0x0A, message_str_pointer=0xF47A10, is_visible=0xF47A08, vendor_value=0xBF4C, countdown_timer=0xF479E8),  # quodrona
    DisplayedTextBox(planet_id=0x17, message_str_pointer=0xF4FE10, is_visible=0xF4FE08, vendor_value=0x3F37, countdown_timer=0xF4FDE8),  # outpost omega 2
]

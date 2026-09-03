import hashlib
import zlib
import os

import Utils
from worlds.Files import APDeltaPatch

NA10CHECKSUM = '337bd6f1a1163df31bf2633665589ab0'
ROM_PLAYER_LIMIT = 65535
ROM_NAME = 0x10
bit_positions = [0x01, 0x02, 0x04, 0x08, 0x10, 0x20, 0x40, 0x80]
candle_shop = bit_positions[5]
arrow_shop = bit_positions[4]
potion_shop = bit_positions[1]
shield_shop = bit_positions[6]
ring_shop = bit_positions[7]
take_any = bit_positions[2]
first_quest_dungeon_items_early = 0x18910
first_quest_dungeon_items_late = 0x18C10
cave_room_timer_fix = 0x046CE
locked_door_phasing_fix = 0x15283
candle_flame_invulnerability_fix = 0x1F90D
like_like_rupee_fix = 0x11D44
fast_text_delay = 0x04864
low_health_beep = 0x1ED39
manual_save_input = 0x140EA
save_hearts_hook = 0x14B76
save_hearts_code = 0x145E0
bait_fix_hook = 0x04CF2
bait_fix_code = 0x04D1A
manual_save_text_y = 0x1775B
manual_save_hud_ptrs = 0x1A042
manual_save_attr_ptrs = 0x1A058
manual_save_inventory_ppu = 0x1A326
manual_save_box_buffers = 0x1A333
manual_save_map_attrs = 0x1A398
manual_save_text_code = 0x1AF80
full_health_after_load_hook = 0x0A645
full_health_after_load_code = 0x0A840
full_health_after_death_mode8_hook = 0x14B8C
full_health_after_death_transition_hook = 0x14D77
full_health_after_death_marker_code = 0x145F4
full_health_after_death_refill_code = 0x15362
full_health_after_death_load_hook = 0x0A61E
full_health_after_death_load_code = 0x0AFA0
alttp_sword_sprite_table = 0x071BB
alttp_sword_swing_code = 0x1BD10
alttp_sword_draw_hook = 0x1F7C6
alttp_sword_hitbox = 0x0761B
alttp_sword_position = 0x076B0
alttp_sword_dungeon_weapon = 0x1F7DC
alttp_sword_dungeon_beam_hook = 0x1F3B2
alttp_sword_dungeon_beam_code = 0x1BE50
game_mode = 0x12
sword = 0x0657
bombs = 0x0658
arrow = 0x0659
bow = 0x065A
candle = 0x065B
recorder = 0x065C
food = 0x065D
potion = 0x065E
magical_rod = 0x065F
raft = 0x0660
book_of_magic = 0x0661
ring = 0x0662
stepladder = 0x0663
magical_key = 0x0664
power_bracelet = 0x0665
letter = 0x0666
heart_containers = 0x066F
triforce_fragments = 0x0671
boomerang = 0x0674
magical_boomerang = 0x0675
magical_shield = 0x0676
rupees_to_add = 0x067D

def apply_cave_room_timer_fix(rom_data: bytearray) -> None:
    """Reset the cave room timer to eliminate random cave-entry delays."""

    expected = bytes.fromhex(
        "A9 00 "
        "9D 85 04 "
        "A9 81 "
        "9D BF 04 "
        "A9 40 "
        "85 AC "
        "A9 40 "
        "8D 51 03 "
        "8D 52 03"
    )

    patched = bytes.fromhex(
        "A9 00 "
        "9D 85 04 "
        "85 29 "
        "A9 81 "
        "9D BF 04 "
        "A9 40 "
        "85 AC "
        "8D 51 03 "
        "8D 52 03"
    )

    actual = bytes(
        rom_data[cave_room_timer_fix:cave_room_timer_fix + len(expected)]
    )

    if actual != expected:
        raise RuntimeError(
            f"Unexpected TLoZ cave room timer code at "
            f"{cave_room_timer_fix:#06x}: {actual.hex(' ')}"
        )

    rom_data[
        cave_room_timer_fix:cave_room_timer_fix + len(patched)
    ] = patched

def apply_locked_door_phasing_fix(rom_data: bytearray) -> None:
    """Prevent phasing through locked doors while shutters are opening."""

    expected = bytes.fromhex("D0 19")
    patched = bytes.fromhex("D0 C0")

    actual = bytes(
        rom_data[
            locked_door_phasing_fix:
            locked_door_phasing_fix + len(expected)
        ]
    )

    if actual != expected:
        raise RuntimeError(
            f"Unexpected TLoZ locked-door branch at "
            f"{locked_door_phasing_fix:#06x}: {actual.hex(' ')}"
        )

    rom_data[
        locked_door_phasing_fix:
        locked_door_phasing_fix + len(patched)
    ] = patched

def apply_candle_flame_fix(rom_data: bytearray) -> None:
    """Prevent Link from being hurt by his own candle or rod flame."""

    expected = bytes.fromhex("A9 0E")
    patched = bytes.fromhex("A9 00")

    actual = bytes(
        rom_data[
            candle_flame_invulnerability_fix:
            candle_flame_invulnerability_fix + len(expected)
        ]
    )

    if actual != expected:
        raise RuntimeError(
            f"Unexpected TLoZ candle flame hitbox code at "
            f"{candle_flame_invulnerability_fix:#06x}: {actual.hex(' ')}"
        )

    rom_data[
        candle_flame_invulnerability_fix:
        candle_flame_invulnerability_fix + len(patched)
    ] = patched

def apply_like_like_rupee_fix(rom_data: bytearray) -> None:
    """Make Like Likes consume rupees instead of removing the Magical Shield."""

    expected = bytes.fromhex("A9 00 8D 76 06")
    patched = bytes.fromhex("A9 01 8D 7E 06")

    actual = bytes(
        rom_data[like_like_rupee_fix:like_like_rupee_fix + len(expected)]
    )

    if actual != expected:
        raise RuntimeError(
            f"Unexpected TLoZ Like Like shield code at "
            f"{like_like_rupee_fix:#06x}: {actual.hex(' ')}"
        )

    rom_data[
        like_like_rupee_fix:like_like_rupee_fix + len(patched)
    ] = patched

def apply_manual_save(rom_data: bytearray) -> None:
    """Apply Redux-style manual saving with saved-heart preservation."""

    manual_expected = bytes.fromhex(
        "A5 FB 29 88 C9 88"
    )
    manual_patched = bytes.fromhex(
        "A5 FA 29 88 C9 88"
    )

    save_hook_expected = bytes.fromhex(
        "A4 13 B9 E9 8A 85 12 "
        "AD 6F 06 29 F0 09 02 8D 6F 06 "
        "A9 FF 8D 70 06 20 A3 EB"
    )
    save_hook_patched = bytes.fromhex(
        "A4 13 B9 E9 8A 85 12 "
        "20 D0 85 EA EA EA EA EA EA EA "
        "A9 FF 8D 70 06 20 A3 EB"
    )

    save_code = bytes.fromhex(
        "AD 6F 06 "
        "29 0F "
        "C9 02 "
        "B0 0A "
        "AD 6F 06 "
        "29 F0 "
        "09 02 "
        "8D 6F 06 "
        "60"
    )
    bait_hook_expected = bytes.fromhex(
        "A9 04 8D 02 06"
    )
    bait_hook_patched = bytes.fromhex(
        "4C 0A 8D EA EA"
    )
    bait_code = bytes.fromhex(
        "A9 00 8D 5D 06 "
        "A9 04 8D 02 06 "
        "4C E7 8C"
    )
    save_text_patches = [
        (
            manual_save_text_y,
            bytes.fromhex("A9 36"),
            bytes.fromhex("A9 3E"),
        ),
        (
            manual_save_hud_ptrs,
            bytes.fromhex(
                "23 A3 37 A3 02 A2 48 A3 50 A3 60 A3"
            ),
            bytes.fromhex(
                "70 AF 36 A3 02 A2 23 A3 40 A3 51 A3"
            ),
        ),
        (
            manual_save_attr_ptrs,
            bytes.fromhex("B0 A3 B9 A3"),
            bytes.fromhex("82 AF B9 A3"),
        ),
        (
            manual_save_inventory_ppu,
            bytes.fromhex("29 84"),
            bytes.fromhex("29 51"),
        ),
        (
            manual_save_box_buffers,
            bytes.fromhex(
                "29 C7 04 69 6A 6A 6B "
                "29 CF 01 69 "
                "29 D0 4B 6A "
                "29 DB 01 6B FF "
                "29 E7 C2 6C "
                "29 EA C2 6C "
                "29 EF C4 6C "
                "29 FB C4 6C FF "
                "2A 27 04 6E 6A 6A 6D FF "
                "2A 42 0C 1E 1C 0E 24 0B 24 0B 1E 1D 1D 18 17 FF "
                "2A 64 08 0F 18 1B 24 1D 11 12 1C"
            ),
            bytes.fromhex(
                "29 C5 03 69 6A 6B "
                "29 CF 01 69 "
                "29 D0 4B 6A "
                "29 DB 01 6B FF "
                "29 E5 06 6C 0B 6E 6A 6A 6B FF "
                "2A 27 01 6C "
                "2A 0A C2 6C "
                "29 EF C4 6C "
                "29 FB C4 6C FF "
                "2A 05 03 6E 6A 6B "
                "2A 47 04 6E 6A 6A 6D "
                "2A 6F 01 6E "
                "2A 70 4B 6A "
                "2A 7B 01 6D FF"
            ),
        ),
        (
            manual_save_map_attrs,
            bytes.fromhex(
                "2A 8C 10 F5 F5 FD F5 F5 FD F5 F5 FD F5 F5 F5 FD F5 F5 F5 FF "
                "2B AC 10 F5 FE F5 F5 F5 FE F5 F5 F5 F5 FE F5 F5 F5 FE F5 FF "
                "2B D9 43 05 2B DC 4B 00 FF "
                "2B E9 56 55 FF"
            ),
            bytes.fromhex(
                "2A 8C 10 FD F5 FD F5 F5 FD F5 F5 F5 F5 F5 F5 FD F5 F5 FD FF "
                "2B AC 10 FE FE F5 F5 F5 F5 FE F5 F5 F5 FE F5 F5 F5 FE FE FF "
                "2B D9 43 05 2B DC 4B 00 FF "
                "2B E9 56 55 FF"
            ),
        ),
    ]
    save_text_code = bytes.fromhex(
        "29 63 04 1E 19 2B 0A "
        "29 83 07 1D 18 24 1C 0A 1F 0E FF "
        "2B D0 0B 55 55 00 00 55 55 55 00 05 05 05 "
        "2B DB 4C 00 FF"
    )

    manual_actual = bytes(
        rom_data[
            manual_save_input:
            manual_save_input + len(manual_expected)
        ]
    )
    save_hook_actual = bytes(
        rom_data[
            save_hearts_hook:
            save_hearts_hook + len(save_hook_expected)
        ]
    )
    save_code_actual = bytes(
        rom_data[
            save_hearts_code:
            save_hearts_code + len(save_code)
        ]
    )
    bait_hook_actual = bytes(
        rom_data[
            bait_fix_hook:
            bait_fix_hook + len(bait_hook_expected)
        ]
    )
    bait_code_actual = bytes(
        rom_data[
            bait_fix_code:
            bait_fix_code + len(bait_code)
        ]
    )
    save_text_actuals = [
        (offset, expected, patched, bytes(rom_data[offset:offset + len(expected)]))
        for offset, expected, patched in save_text_patches
    ]
    save_text_code_actual = bytes(
        rom_data[
            manual_save_text_code:
            manual_save_text_code + len(save_text_code)
        ]
    )

    # Validate everything before modifying the ROM.
    if manual_actual != manual_expected:
        raise RuntimeError(
            f"Unexpected TLoZ manual-save input code at "
            f"{manual_save_input:#06x}: {manual_actual.hex(' ')}"
        )
    if save_hook_actual != save_hook_expected:
        raise RuntimeError(
            f"Unexpected TLoZ save-hearts hook at "
            f"{save_hearts_hook:#06x}: {save_hook_actual.hex(' ')}"
        )
    if save_code_actual != bytes([0xFF]) * len(save_code):
        raise RuntimeError(
            f"Unexpected data in TLoZ save-hearts code area at "
            f"{save_hearts_code:#06x}"
        )
    if bait_hook_actual != bait_hook_expected:
        raise RuntimeError(
            f"Unexpected TLoZ Bait fix hook at "
            f"{bait_fix_hook:#06x}: {bait_hook_actual.hex(' ')}"
        )
    if bait_code_actual != bytes([0xFF]) * len(bait_code):
        raise RuntimeError(
            f"Unexpected data in TLoZ Bait fix code area at "
            f"{bait_fix_code:#06x}"
        )
    for offset, expected, _, actual in save_text_actuals:
        if actual != expected:
            raise RuntimeError(
                f"Unexpected TLoZ manual-save text data at "
                f"{offset:#06x}: {actual.hex(' ')}"
            )
    if save_text_code_actual != bytes([0xFF]) * len(save_text_code):
        raise RuntimeError(
            f"Unexpected data in TLoZ manual-save text area at "
            f"{manual_save_text_code:#06x}"
        )

    rom_data[
        manual_save_input:
        manual_save_input + len(manual_patched)
    ] = manual_patched
    rom_data[
        save_hearts_hook:
        save_hearts_hook + len(save_hook_patched)
    ] = save_hook_patched
    rom_data[
        save_hearts_code:
        save_hearts_code + len(save_code)
    ] = save_code
    rom_data[
        bait_fix_hook:
        bait_fix_hook + len(bait_hook_patched)
    ] = bait_hook_patched
    rom_data[
        bait_fix_code:
        bait_fix_code + len(bait_code)
    ] = bait_code
    for offset, _, patched, _ in save_text_actuals:
        rom_data[offset:offset + len(patched)] = patched
    rom_data[
        manual_save_text_code:
        manual_save_text_code + len(save_text_code)
    ] = save_text_code

def apply_full_health_after_load(rom_data: bytearray) -> None:
    """Apply Redux-style full health when loading a save file."""

    hook_expected = bytes.fromhex(
        "4C A1 EB"
    )
    hook_patched = bytes.fromhex(
        "4C 30 A8"
    )

    code = bytes.fromhex(
        "AD 6F 06 "
        "29 F0 "
        "8D 6F 06 "
        "4A 4A 4A 4A "
        "6D 6F 06 "
        "8D 6F 06 "
        "4C A1 EB"
    )

    hook_actual = bytes(
        rom_data[
            full_health_after_load_hook:
            full_health_after_load_hook + len(hook_expected)
        ]
    )
    code_actual = bytes(
        rom_data[
            full_health_after_load_code:
            full_health_after_load_code + len(code)
        ]
    )

    # Validate everything before modifying the ROM.
    if hook_actual != hook_expected:
        raise RuntimeError(
            f"Unexpected TLoZ full-health load hook at "
            f"{full_health_after_load_hook:#06x}: {hook_actual.hex(' ')}"
        )

    if code_actual != bytes([0xFF]) * len(code):
        raise RuntimeError(
            f"Unexpected data in TLoZ full-health load code area at "
            f"{full_health_after_load_code:#06x}"
        )

    rom_data[
        full_health_after_load_hook:
        full_health_after_load_hook + len(hook_patched)
    ] = hook_patched

    rom_data[
        full_health_after_load_code:
        full_health_after_load_code + len(code)
    ] = code

def apply_full_health_after_death(rom_data: bytearray) -> None:
    """Refill health after continuing or retrying from a Game Over."""

    mode8_expected = bytes.fromhex(
        "20 A3 EB C0 02"
    )
    mode8_patched = bytes.fromhex(
        "20 52 93 C0 02"
    )

    death_transition_expected = bytes.fromhex(
        "20 A3 EB A9 08 85 12"
    )
    death_transition_patched = bytes.fromhex(
        "20 E4 85 A9 08 85 12"
    )

    load_expected = bytes.fromhex(
        "A9 00 "
        "8D 2E 05 "
        "85 AC "
        "8D 6C 06"
    )
    load_patched = bytes.fromhex(
        "20 90 AF "
        "EA EA EA EA EA EA EA"
    )

    # Call the original EndGameMode first, then mark that Mode 8
    # was reached through an actual death.
    marker_code = bytes.fromhex(
        "20 A3 EB "
        "A9 01 "
        "85 E5 "
        "60"
    )

    # Mode 8 selections:
    #   Y = 0: Continue -> refill immediately and clear marker.
    #   Y = 1: Save     -> clear marker without refilling.
    #   Y = 2: Retry    -> change marker to 2 so the refill can happen
    #                     after the saved Items block is loaded again.
    refill_code = bytes.fromhex(
        "A5 E5 "
        "F0 1E "
        "C0 02 "
        "F0 1E "
        "A9 00 "
        "85 E5 "
        "C0 01 "
        "F0 12 "
        "AD 6F 06 "
        "29 F0 "
        "8D 6F 06 "
        "4A 4A 4A 4A "
        "0D 6F 06 "
        "8D 6F 06 "
        "20 A3 EB "
        "60 "
        "A9 02 "
        "85 E5 "
        "D0 F6"
    )

    # This replaces the normal post-file-load state reset. It performs
    # the same reset first, then checks for the Retry marker. If present,
    # the saved heart value has now been restored, so refill from its
    # maximum-heart nibble and consume the marker.
    load_code = bytes.fromhex(
        "A9 00 "
        "8D 2E 05 "
        "85 AC "
        "8D 6C 06 "
        "A5 E5 "
        "C9 02 "
        "D0 16 "
        "A9 00 "
        "85 E5 "
        "AD 6F 06 "
        "29 F0 "
        "8D 6F 06 "
        "4A 4A 4A 4A "
        "0D 6F 06 "
        "8D 6F 06 "
        "A9 00 "
        "60"
    )

    mode8_actual = bytes(
        rom_data[
            full_health_after_death_mode8_hook:
            full_health_after_death_mode8_hook + len(mode8_expected)
        ]
    )
    death_transition_actual = bytes(
        rom_data[
            full_health_after_death_transition_hook:
            full_health_after_death_transition_hook + len(death_transition_expected)
        ]
    )
    marker_actual = bytes(
        rom_data[
            full_health_after_death_marker_code:
            full_health_after_death_marker_code + len(marker_code)
        ]
    )
    refill_actual = bytes(
        rom_data[
            full_health_after_death_refill_code:
            full_health_after_death_refill_code + len(refill_code)
        ]
    )
    load_actual = bytes(
        rom_data[
            full_health_after_death_load_hook:
            full_health_after_death_load_hook + len(load_expected)
        ]
    )
    load_code_actual = bytes(
        rom_data[
            full_health_after_death_load_code:
            full_health_after_death_load_code + len(load_code)
        ]
    )

    # Validate everything before modifying the ROM.
    if mode8_actual != mode8_expected:
        raise RuntimeError(
            f"Unexpected TLoZ Game Over Mode 8 hook at "
            f"{full_health_after_death_mode8_hook:#06x}: {mode8_actual.hex(' ')}"
        )

    if death_transition_actual != death_transition_expected:
        raise RuntimeError(
            f"Unexpected TLoZ death transition hook at "
            f"{full_health_after_death_transition_hook:#06x}: "
            f"{death_transition_actual.hex(' ')}"
        )

    if marker_actual != bytes([0xFF]) * len(marker_code):
        raise RuntimeError(
            f"Unexpected data in TLoZ death marker code area at "
            f"{full_health_after_death_marker_code:#06x}"
        )

    if refill_actual != bytes([0xFF]) * len(refill_code):
        raise RuntimeError(
            f"Unexpected data in TLoZ death refill code area at "
            f"{full_health_after_death_refill_code:#06x}"
        )

    if load_actual != load_expected:
        raise RuntimeError(
            f"Unexpected TLoZ post-file-load hook at "
            f"{full_health_after_death_load_hook:#06x}: {load_actual.hex(' ')}"
        )

    if load_code_actual != bytes([0xFF]) * len(load_code):
        raise RuntimeError(
            f"Unexpected data in TLoZ post-file-load code area at "
            f"{full_health_after_death_load_code:#06x}"
        )

    rom_data[
        full_health_after_death_mode8_hook:
        full_health_after_death_mode8_hook + len(mode8_patched)
    ] = mode8_patched

    rom_data[
        full_health_after_death_transition_hook:
        full_health_after_death_transition_hook + len(death_transition_patched)
    ] = death_transition_patched

    rom_data[
        full_health_after_death_marker_code:
        full_health_after_death_marker_code + len(marker_code)
    ] = marker_code

    rom_data[
        full_health_after_death_refill_code:
        full_health_after_death_refill_code + len(refill_code)
    ] = refill_code

    rom_data[
        full_health_after_death_load_hook:
        full_health_after_death_load_hook + len(load_patched)
    ] = load_patched

    rom_data[
        full_health_after_death_load_code:
        full_health_after_death_load_code + len(load_code)
    ] = load_code

def apply_alttp_sword_swing(rom_data: bytearray) -> None:
    """Apply the ALttP-style sword swing from Zelda Redux."""

    sprite_expected = bytes.fromhex("20 82 3C")
    sprite_patched = bytes.fromhex("20 82 48")

    swing_code = bytes.fromhex(
        "A5 98 95 98 20 13 70 B5 AC C9 02 D0 04 E0 0D F0 "
        "0C 98 18 65 00 A8 A9 00 95 84 4C 6C BD BD D0 03 "
        "C9 08 D0 05 B9 B1 BD 95 98 98 0A 0A 0A 7D D0 03 "
        "69 FF A8 A5 70 18 79 71 BD 95 70 85 00 A5 84 18 "
        "79 91 BD 95 84 85 01 A5 10 F0 04 C6 01 C6 01 B9 "
        "B5 BD 29 C0 0D 57 06 18 69 FF 20 8D 79 B9 B5 BD "
        "29 06 4A 85 0C B9 B5 BD 29 01 85 0F A9 05 4C AC "
        "FF F8 FA FE FE 00 03 05 08 08 06 01 01 FF FD FB "
        "F8 FB F9 F6 F6 F7 F9 FB FF 05 07 0A 0A 09 06 04 "
        "01 F9 F7 F6 F6 F7 F9 FB 01 0A 0C 0D 0D 0C 0A 09 "
        "02 0C 09 03 03 00 FA F8 F7 FA FD 03 03 05 0A 0C "
        "0E 01 02 08 04 04 04 40 40 40 44 44 02 C4 C4 C0 "
        "C0 C0 84 84 03 84 84 03 03 03 04 04 00 44 44 02 "
        "02 02 C4 C4 80"
    )
    sprite_actual = bytes(
        rom_data[alttp_sword_sprite_table:alttp_sword_sprite_table + 3]
    )
    code_actual = bytes(
        rom_data[
            alttp_sword_swing_code:
            alttp_sword_swing_code + len(swing_code)
        ]
    )

    draw_hook_expected = bytes.fromhex(
        "A5 98 95 98 20 13 70 98 18 65 00 A8"
    )
    draw_hook_patched = bytes.fromhex(
        "A9 06 20 AC FF 20 00 BD B5 84 D0 44"
    )
    draw_hook_actual = bytes(
        rom_data[
            alttp_sword_draw_hook:
            alttp_sword_draw_hook + len(draw_hook_expected)
        ]
    )

    hitbox_expected = bytes.fromhex(
        "85 07 A5 98 29 0C F0 09 A9 0C 85 0D A9 10 4C 58 7D "
        "A9 10 85 0D A9 0C 85 0E 20 D6 7D A5 06 F0 C9 4C AF 7D"
    )
    hitbox_patched = bytes.fromhex(
        "85 07 A4 00 B9 98 00 29 0C F0 06 A9 0C A0 10 D0 04 "
        "A9 10 A0 0C 85 0D 84 0E 20 D6 7D A5 06 F0 C9 4C AF 7D"
    )
    hitbox_actual = bytes(
        rom_data[
            alttp_sword_hitbox:
            alttp_sword_hitbox + len(hitbox_expected)
        ]
    )

    position_expected = bytes.fromhex(
        "A4 00 A5 98 29 0C F0 11 B9 70 00 18 69 06 85 04 "
        "B9 84 00 18 69 08 4C FD 7D B9 70 00 18 69 08 85 "
        "04 B9 84 00 18 69 06 4C E7 7B"
    )
    position_patched = bytes.fromhex(
        "A4 00 B9 98 00 29 0C F0 07 A9 08 48 A9 06 D0 05 "
        "A9 09 48 A9 08 18 79 70 00 85 04 68 18 79 84 00 "
        "4C E7 7B EA EA EA EA EA EA EA"
    )
    position_actual = bytes(
        rom_data[
            alttp_sword_position:
            alttp_sword_position + len(position_expected)
        ]
    )

    dungeon_weapon_expected = bytes.fromhex(
        "A5 84 18 79 64 F7 95 84 85 01 B5 AC 29 0F A8 A9 "
        "08 88 F0 02 B5 98"
    )
    dungeon_weapon_patched = bytes.fromhex(
        "A5 84 18 79 64 F7 95 84 85 01 A5 10 F0 04 C6 01 "
        "C6 01 B5 98 EA EA"
    )
    dungeon_weapon_actual = bytes(
        rom_data[
            alttp_sword_dungeon_weapon:
            alttp_sword_dungeon_weapon + len(dungeon_weapon_expected)
        ]
    )

    dungeon_beam_hook_expected = bytes.fromhex(
        "29 03 F0 07 A5 01 18 69 03 85 01"
    )
    dungeon_beam_hook_patched = bytes.fromhex(
        "A9 06 20 AC FF 20 40 BE EA EA EA"
    )
    dungeon_beam_code = bytes.fromhex(
        "B5 98 29 03 F0 02 A9 03 18 65 01 85 01 A5 10 F0 "
        "04 C6 01 C6 01 A9 05 4C AC FF"
    )

    dungeon_beam_hook_actual = bytes(
        rom_data[
            alttp_sword_dungeon_beam_hook:
            alttp_sword_dungeon_beam_hook + len(dungeon_beam_hook_expected)
        ]
    )
    dungeon_beam_code_actual = bytes(
        rom_data[
            alttp_sword_dungeon_beam_code:
            alttp_sword_dungeon_beam_code + len(dungeon_beam_code)
        ]
    )

    # Validate everything before modifying the ROM.
    if sprite_actual != sprite_expected:
        raise RuntimeError(
            f"Unexpected TLoZ sword sprite table at {alttp_sword_sprite_table:#06x}: "
            f"{sprite_actual.hex(' ')}"
        )
    if code_actual != bytes([0xFF]) * len(swing_code):
        raise RuntimeError(
            f"Unexpected data in TLoZ ALttP sword code area at "
            f"{alttp_sword_swing_code:#06x}"
        )
    if draw_hook_actual != draw_hook_expected:
        raise RuntimeError(
            f"Unexpected TLoZ sword draw hook at "
            f"{alttp_sword_draw_hook:#06x}: "
            f"{draw_hook_actual.hex(' ')}"
        )
    if hitbox_actual != hitbox_expected:
        raise RuntimeError(
            f"Unexpected TLoZ sword hitbox routine at "
            f"{alttp_sword_hitbox:#06x}: "
            f"{hitbox_actual.hex(' ')}"
        )
    if position_actual != position_expected:
        raise RuntimeError(
            f"Unexpected TLoZ sword positioning routine at "
            f"{alttp_sword_position:#06x}: "
            f"{position_actual.hex(' ')}"
        )
    if dungeon_weapon_actual != dungeon_weapon_expected:
        raise RuntimeError(
            f"Unexpected TLoZ dungeon weapon draw routine at "
            f"{alttp_sword_dungeon_weapon:#06x}: "
            f"{dungeon_weapon_actual.hex(' ')}"
        )
    if dungeon_beam_hook_actual != dungeon_beam_hook_expected:
        raise RuntimeError(
            f"Unexpected TLoZ dungeon beam draw hook at "
            f"{alttp_sword_dungeon_beam_hook:#06x}: "
            f"{dungeon_beam_hook_actual.hex(' ')}"
        )
    if dungeon_beam_code_actual != bytes([0xFF]) * len(dungeon_beam_code):
        raise RuntimeError(
            f"Unexpected data in TLoZ dungeon beam code area at "
            f"{alttp_sword_dungeon_beam_code:#06x}"
        )

    rom_data[
        alttp_sword_sprite_table:alttp_sword_sprite_table + 3
    ] = sprite_patched
    rom_data[
        alttp_sword_swing_code:
        alttp_sword_swing_code + len(swing_code)
    ] = swing_code
    rom_data[
        alttp_sword_draw_hook:
        alttp_sword_draw_hook + len(draw_hook_patched)
    ] = draw_hook_patched
    rom_data[
        alttp_sword_hitbox:
        alttp_sword_hitbox + len(hitbox_patched)
    ] = hitbox_patched
    rom_data[
        alttp_sword_position:
        alttp_sword_position + len(position_patched)
    ] = position_patched
    rom_data[
        alttp_sword_dungeon_weapon:
        alttp_sword_dungeon_weapon + len(dungeon_weapon_patched)
    ] = dungeon_weapon_patched
    rom_data[
        alttp_sword_dungeon_beam_hook:
        alttp_sword_dungeon_beam_hook + len(dungeon_beam_hook_patched)
    ] = dungeon_beam_hook_patched
    rom_data[
        alttp_sword_dungeon_beam_code:
        alttp_sword_dungeon_beam_code + len(dungeon_beam_code)
    ] = dungeon_beam_code

def apply_visible_secrets(rom_data: bytearray) -> None:
    """Apply Redux-style visible bombable walls and burnable trees."""

    patches = [
        (
            "graphics hook 1",
            0x0c061,
            bytes.fromhex("20 91 80"),
            bytes.fromhex("20 E0 AB"),
        ),
        (
            "graphics hook 2",
            0x0c074,
            bytes.fromhex("20 80 80"),
            bytes.fromhex("20 E0 AB"),
        ),
        (
            "graphics loader",
            0x0ebf0,
            bytes.fromhex(
            "FF FF FF FF FF FF FF FF FF FF FF FF FF FF FF FF "
            "FF FF FF FF FF FF FF FF FF FF FF FF FF FF FF FF "
            "FF FF FF FF FF FF FF FF FF FF FF FF FF FF"
        ),
            bytes.fromhex(
            "A9 15 8D 06 20 A9 40 8D 06 20 A0 C0 A2 00 A5 10 "
            "D0 0E BD 10 AC 8D 07 20 E8 88 D0 F6 20 91 80 60 "
            "BD D0 AC 8D 07 20 E8 88 D0 F6 20 80 80 60"
        ),
        ),
        (
            "graphics assets",
            0x0ec20,
            bytes.fromhex(
            "FF FF FF FF FF FF FF FF FF FF FF FF FF FF FF FF "
            "FF FF FF FF FF FF FF FF FF FF FF FF FF FF FF FF "
            "FF FF FF FF FF FF FF FF FF FF FF FF FF FF FF FF "
            "FF FF FF FF FF FF FF FF FF FF FF FF FF FF FF FF "
            "FF FF FF FF FF FF FF FF FF FF FF FF FF FF FF FF "
            "FF FF FF FF FF FF FF FF FF FF FF FF FF FF FF FF "
            "FF FF FF FF FF FF FF FF FF FF FF FF FF FF FF FF "
            "FF FF FF FF FF FF FF FF FF FF FF FF FF FF FF FF "
            "FF FF FF FF FF FF FF FF FF FF FF FF FF FF FF FF "
            "FF FF FF FF FF FF FF FF FF FF FF FF FF FF FF FF "
            "FF FF FF FF FF FF FF FF FF FF FF FF FF FF FF FF "
            "FF FF FF FF FF FF FF FF FF FF FF FF FF FF FF FF "
            "FF FF FF FF FF FF FF FF FF FF FF FF FF FF FF FF "
            "FF FF FF FF FF FF FF FF FF FF FF FF FF FF FF FF "
            "FF FF FF FF FF FF FF FF FF FF FF FF FF FF FF FF "
            "FF FF FF FF FF FF FF FF FF FF FF FF FF FF FF FF "
            "FF FF FF FF FF FF FF FF FF FF FF FF FF FF FF FF "
            "FF FF FF FF FF FF FF FF FF FF FF FF FF FF FF FF "
            "FF FF FF FF FF FF FF FF FF FF FF FF FF FF FF FF "
            "FF FF FF FF FF FF FF FF FF FF FF FF FF FF FF FF "
            "FF FF FF FF FF FF FF FF FF FF FF FF FF FF FF FF "
            "FF FF FF FF FF FF FF FF FF FF FF FF FF FF FF FF "
            "FF FF FF FF FF FF FF FF FF FF FF FF FF FF FF FF "
            "FF FF FF FF FF FF FF FF FF FF FF FF FF FF FF FF"
        ),
            bytes.fromhex(
            "E0 9C 80 C0 40 80 80 00 01 20 18 00 80 00 00 00 "
            "00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 "
            "8F 38 01 03 03 01 00 00 00 05 18 00 00 00 01 00 "
            "00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 "
            "E0 F9 F8 73 73 02 26 24 01 02 02 84 84 A4 48 49 "
            "20 10 10 47 CF CF 87 67 45 20 86 88 10 10 08 00 "
            "8C E4 70 38 3C 70 70 E4 01 01 80 40 40 84 85 09 "
            "E6 46 02 08 9C 1C 8C 64 08 88 54 12 20 21 01 01 "
            "00 05 17 1B 3F 3E 7F 6F FF FA E8 E0 C0 C8 80 82 "
            "3F 7B 7F 4F 16 07 07 00 C0 90 80 A0 E8 FB F7 E0 "
            "00 00 00 90 C0 A0 80 C0 FF 3F 0F 07 07 23 07 03 "
            "48 C0 00 A0 00 80 C0 00 03 43 03 07 17 BF C0 03 "
            "00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 "
            "FF DF FF FD BF FF FB FF 00 00 00 00 00 00 00 00 "
            "00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 "
            "FF DF FF FD BF FF FB FF 00 00 00 00 00 00 00 00 "
            "18 18 18 18 18 18 19 5E EF EF EF EF EF EF EE A9 "
            "38 1C 1B 18 18 18 18 18 C7 EB EC EF EF EF EF EF "
            "00 00 01 FF FF 02 04 04 FF FF FE 00 FE FD FB FB "
            "04 04 02 FF FF 01 00 00 FB FB FD FE 00 FE FF FF "
            "00 80 00 FF FF 80 80 40 FF 7F FF 00 FF 7F 7F BF "
            "40 80 80 FF FF 00 80 00 BF 7F 7F FF 00 FF 7F FF "
            "18 18 18 18 18 D8 38 1C F7 F7 F7 F7 F7 37 D7 E3 "
            "7A 98 18 18 18 18 18 18 95 77 F7 F7 F7 F7 F7 F7"
        ),
        ),
        (
            "bombed wall graphic",
            0x10f18,
            bytes.fromhex("A9 24"),
            bytes.fromhex("A9 54"),
        ),
        (
            "collision helper",
            0x13f10,
            bytes.fromhex(
            "FF FF FF FF FF FF FF FF FF FF FF FF FF FF FF FF "
            "FF FF FF FF FF FF FF FF FF FF FF FF FF FF FF FF "
            "FF FF FF FF FF FF FF"
        ),
            bytes.fromhex(
            "20 16 BF B0 03 4C 59 F1 4C 29 F1 20 16 BF B0 03 "
            "4C 0B EF 4C EA EE 20 00 EE C9 54 90 04 C9 60 90 "
            "04 CD 4A 03 60 38 60"
        ),
        ),
        (
            "dungeon right wall",
            0x16022,
            bytes.fromhex("DF DF DF DF F5 F5 DF DF DF DF F5 F5"),
            bytes.fromhex("DF 5E DF DF F5 F5 5F DF DF DF F5 F5"),
        ),
        (
            "dungeon left wall",
            0x1605e,
            bytes.fromhex("F5 F5 DE DE DE DE F5 F5 DE DE DE DE"),
            bytes.fromhex("F5 F5 DE DE DE 58 F5 F5 DE DE 59 DE"),
        ),
        (
            "dungeon bottom wall",
            0x1609a,
            bytes.fromhex("DD DD F5 DD DD F5 DD DD F5 DD DD F5"),
            bytes.fromhex("DD DD F5 5B DD F5 5D DD F5 DD DD F5"),
        ),
        (
            "dungeon top wall",
            0x160d7,
            bytes.fromhex("DC DC F5 DC DC F5 DC DC F5 DC DC F5"),
            bytes.fromhex("DC DC F5 DC 5A F5 DC 5C F5 DC DC F5"),
        ),
        (
            "secret lookup hook",
            0x16ae0,
            bytes.fromhex("BD 76 A9"),
            bytes.fromhex("20 40 AC"),
        ),
        (
            "bombed wall property",
            0x16bfd,
            bytes.fromhex("C9 27"),
            bytes.fromhex("C9 57"),
        ),
        (
            "alternate tile table",
            0x16c40,
            bytes.fromhex("FF FF FF FF FF FF"),
            bytes.fromhex("C8 58 5C BC C0 C0"),
        ),
        (
            "quest tile logic",
            0x16c50,
            bytes.fromhex(
            "FF FF FF FF FF FF FF FF FF FF FF FF FF FF FF FF "
            "FF FF FF FF FF FF FF FF FF FF FF FF FF FF FF FF "
            "FF FF FF FF"
        ),
            bytes.fromhex(
            "A4 EB B9 FE 6A 30 0E 0A 30 02 10 14 A4 16 B9 2D "
            "06 F0 0D D0 07 A4 16 B9 2D 06 D0 04 BD 76 A9 60 "
            "BD 30 AC 60"
        ),
        ),
        (
            "collision hook 1",
            0x1ef13,
            bytes.fromhex("20 00 EE CD 4A 03 B0 DF"),
            bytes.fromhex("A9 04 20 AC FF 4C 0B BF"),
        ),
        (
            "collision hook 2",
            0x1f131,
            bytes.fromhex("20 00 EE CD 4A 03 90 30"),
            bytes.fromhex("A9 04 20 AC FF 4C 00 BF"),
        ),
    ]

    # Validate every region before modifying any part of the ROM.
    for name, offset, expected, _ in patches:
        actual = bytes(rom_data[offset:offset + len(expected)])
        if actual != expected:
            raise RuntimeError(
                f"Unexpected TLoZ Visible Secrets {name} at "
                f"{offset:#06x}: {actual.hex(' ')}"
            )

    for _, offset, _, patched in patches:
        rom_data[offset:offset + len(patched)] = patched

class TLoZDeltaPatch(APDeltaPatch):
    hash = NA10CHECKSUM
    game = "The Legend of Zelda"
    patch_file_ending = ".aptloz"
    result_file_ending = ".nes"

    @classmethod
    def get_source_data(cls) -> bytes:
        return get_base_rom_bytes()

def get_base_rom_bytes(file_name: str = "") -> bytes:
    base_rom_bytes = getattr(get_base_rom_bytes, "base_rom_bytes", None)
    if not base_rom_bytes:
        file_name = get_base_rom_path()
        base_rom_bytes = bytes(Utils.read_snes_rom(open(file_name, "rb")))

        basemd5 = hashlib.md5()
        basemd5.update(base_rom_bytes)
        if NA10CHECKSUM != basemd5.hexdigest():
            raise Exception('Supplied Base Rom does not match known MD5 for NA (1.0) release. '
                            'Get the correct game and version, then dump it')
        get_base_rom_bytes.base_rom_bytes = base_rom_bytes
    return base_rom_bytes

def get_base_rom_path() -> str:
    from . import TLoZWorld
    return TLoZWorld.settings.rom_file

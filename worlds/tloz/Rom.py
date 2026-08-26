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
fast_text_delay = 0x04864
low_health_beep = 0x1ED39
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

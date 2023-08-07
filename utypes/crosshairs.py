import re
from typing import NamedTuple

import numpy as np


__all__ = ('Crosshair',)


DICTIONARY = "ABCDEFGHJKLMNOPQRSTUVWXYZabcdefhijkmnopqrstuvwxyz23456789"
DICTIONARY_LENGTH = len(DICTIONARY)
CODE_PATTERN = re.compile(r"CSGO(-[{%s}]{5}){5}$" % DICTIONARY)


class Crosshair(NamedTuple):
    gap: float  # -5.0 - 5.0
    outline_thickness: float  # 0.0 - 3.0
    red: int  # 0 - 255
    green: int  # 0 - 255
    blue: int  # 0 - 255
    alpha: int  # 0 - 255
    dynamic_splitdist: int  # 0 - 16
    fixed_gap: float  # -5.0 - 5.0
    color: int  # 0 - 5
    draw_outline: bool
    dynamic_splitalpha_innermod: float  # 0.0 - 1.0
    dynamic_splitalpha_outermod: float  # 0.3 - 1.0
    dynamic_maxdist_split_ratio: float  # 0.0 - 1.0
    thickness: float  # 0.1 - 6.0
    style: int  # 0 - 5
    dot: bool
    gap_use_weapon_value: bool
    use_alpha: bool
    t: bool
    size: float  # 0.0 - 10.0

    @property
    def commands(self) -> list[str]:
        return [
            f"cl_crosshairgap {self.gap}",
            f"cl_crosshair_outlinethickness {self.outline_thickness}",
            f"cl_crosshaircolor_r {self.red}",
            f"cl_crosshaircolor_g {self.green}",
            f"cl_crosshaircolor_b {self.blue}",
            f"cl_crosshairalpha {self.alpha}",
            f"cl_crosshair_dynamic_splitdist {self.dynamic_splitdist}",
            f"cl_fixedcrosshairgap {self.fixed_gap}",
            f"cl_crosshaircolor {self.color}",
            f"cl_crosshair_drawoutline {self.draw_outline}",
            f"cl_crosshair_dynamic_splitalpha_innermod {self.dynamic_splitalpha_innermod}",
            f"cl_crosshair_dynamic_splitalpha_outermod {self.dynamic_splitalpha_outermod}",
            f"cl_crosshair_dynamic_maxdist_splitratio {self.dynamic_maxdist_split_ratio}",
            f"cl_crosshairthickness {self.thickness}",
            f"cl_crosshairstyle {self.style}",
            f"cl_crosshairdot {int(self.dot)}",
            f"cl_crosshairgap_useweaponvalue {int(self.gap_use_weapon_value)}",
            f"cl_crosshairusealpha {int(self.use_alpha)}",
            f"cl_crosshair_t {int(self.t)}",
            f"cl_crosshairsize {self.size}"
        ]

    @staticmethod
    def decode(code: str):
        if not CODE_PATTERN.match(code):
            return

        char_list = list(code[5:].replace('-', ''))

        num = 0
        for c in reversed(char_list):
            num = num * DICTIONARY_LENGTH + DICTIONARY.index(c)

        hexnum = hex(num)[2:]
        bytes_array = bytearray(int(hexnum[i:i + 2], 16)
                                for i in range(0, len(hexnum), 2))

        return Crosshair(**Crosshair._sort_bytes(bytes_array))

    @staticmethod
    def _sort_bytes(bytes_array):
        return {
            "gap": np.int8(np.uint8(bytes_array[2])) / 10,
            "outline_thickness": bytes_array[3] / 2,
            "red": bytes_array[4],
            "green": bytes_array[5],
            "blue": bytes_array[6],
            "alpha": bytes_array[7],
            "dynamic_splitdist": bytes_array[8],
            "fixed_gap": np.int8(np.uint8(bytes_array[9])) / 10,
            "color": bytes_array[10] & 7,
            "draw_outline": int((bytes_array[10] & 8) == 8),
            "dynamic_splitalpha_innermod": (bytes_array[10] >> 4) / 10,
            "dynamic_splitalpha_outermod": (bytes_array[11] & 0xf) / 10,
            "dynamic_maxdist_split_ratio": (bytes_array[11] >> 4) / 10,
            "thickness": bytes_array[12] / 10,
            "style": (bytes_array[13] & 0xf) >> 1,
            "dot": int(((bytes_array[13] >> 4) & 1) == 1),
            "gap_use_weapon_value": int(((bytes_array[13] >> 4) & 2) == 2),
            "use_alpha": int(((bytes_array[13] >> 4) & 4) == 4),
            "t": int(((bytes_array[13] >> 4) & 8) == 8),
            "size": bytes_array[14] / 10,
        }

    def encode(self) -> str:
        num = self._concat_bytes(self._get_bytes())

        code = ""
        for _ in range(25):
            num, r = divmod(num, DICTIONARY_LENGTH)
            code += DICTIONARY[r]

        return f"CSGO-{code[:5]}-{code[5:10]}-{code[10:15]}-{code[15:20]}-{code[20:]}"

    def _get_bytes(self):
        bytes_array = [
            0,
            1,
            int(self.gap * 10) & 0xff,
            int(self.outline_thickness * 2),
            self.red,
            self.green,
            self.blue,
            self.alpha,
            self.dynamic_splitdist,
            int(self.fixed_gap * 10) & 0xff,
            (self.color & 7) | (int(self.draw_outline) << 3) | (int(self.dynamic_splitalpha_innermod * 10) << 4),
            int(self.dynamic_splitalpha_outermod * 10) | (int(self.dynamic_maxdist_split_ratio * 10) << 4),
            int(self.thickness * 10),
            (self.style << 1) |
            (int(self.dot) << 4) |
            (int(self.gap_use_weapon_value) << 5) |
            (int(self.use_alpha) << 6) |
            (int(self.t) << 7),
            int(self.size * 10),
            0,
            0,
            0
        ]
        bytes_array[0] = sum(bytes_array) & 0xff

        return bytes_array

    @staticmethod
    def _concat_bytes(bytes_array) -> int:
        num_hex = ''
        for i in bytes_array:
            num_hex += f'{i:02x}'

        return int(num_hex, 16)

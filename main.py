from glyphsLib import GSFont

from utils import read_side_bearings, dist_between_rankings


font = GSFont('3type-sy-9169字符_2.glyphs')
sb_data = read_side_bearings(font, weights=('ExtraLight','Regular','Heavy'))
score = dist_between_rankings(sb_data, 'lsb')

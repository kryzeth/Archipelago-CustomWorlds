from typing import ClassVar

from BaseClasses import Item, ItemClassification, Location, MultiWorld, Region
from rule_builder.rules import And, Has
from worlds.AutoWorld import World

GAME_NAME = "World of Warcraft - airbreather Variant"


class WoWAirbreatherQuestRegion(Region):
    quest_name: str
    completion_event: Item
    loc: Location

    def __init__(self, quest_name: str, player: int, multiworld: MultiWorld, hint: str | None = None):
        super().__init__(f"Quest: {quest_name}", player, multiworld, hint)
        self.quest_name = quest_name

        self.completion_event = Item(f"Completed Quest: {quest_name}", ItemClassification.progression, None, player)

        loc_name = f"Complete Quest: {quest_name}"
        loc_id = WoWAirbreatherWorld.location_name_to_id[loc_name]
        self.loc = Location(player, loc_name, loc_id, self)
        self.locations.append(self.loc)

        # use a fake location to track dependencies
        fake_loc = Location(player, f"_{loc_name}", parent=self)
        fake_loc.place_locked_item(self.completion_event)
        self.locations.append(fake_loc)

    def has_completed_quest(self):
        return Has(self.completion_event.name)


class WoWAirbreatherLevelRegion(Region):
    level: int
    completion_event: Item
    loc: Location

    def __init__(self, level: int, player: int, multiworld: MultiWorld, hint: str | None = None):
        super().__init__(f"Reach Level {level}", player, multiworld, hint)
        self.level = level

        if level == 1:
            return

        self.completion_event = Item(f"Reached Level {level}", ItemClassification.progression, None, player)

        loc_name = f"Reach Level {level}"
        loc_id = WoWAirbreatherWorld.location_name_to_id[loc_name]
        self.loc = Location(player, loc_name, loc_id, self)
        self.locations.append(self.loc)

        # use a fake location to track dependencies
        fake_loc = Location(player, f"_{loc_name}", parent=self)
        fake_loc.place_locked_item(self.completion_event)
        self.locations.append(fake_loc)

    def has_reached_level(self):
        return Has(self.completion_event.name)


class WoWAirbreatherWorld(World):
    game = GAME_NAME

    item_name_to_id: ClassVar[dict[str, int]] = {
        "Progressive Level Cap": 1,
        "Unlock Quest: Kobold Camp Cleanup [7]": 2,
        "Unlock Quest: Investigate Echo Ridge [15]": 3,
        "Unlock Quest: Skirmish at Echo Ridge [21]": 4,
        "Unlock Quest: Report to Goldshire [54]": 5,
        "Unlock Quest: Eagan Peltskinner [5261]": 6,
        "Unlock Quest: Wolves Across the Border [33]": 7,
        "Unlock Quest: Milly Osworth [3903]": 8,
        "Unlock Quest: Milly's Harvest [3904]": 9,
        "Unlock Quest: Grape Manifest [3905]": 10,
        "Unlock Quest: Brotherhood of Thieves [18]": 11,
        "Unlock Quest: Bounty on Garrick Padfoot [6]": 12,
        "Unlock Quest: Tainted Letter [3105]": 13,
        "Unlock Quest: The Stolen Tome [1598]": 14,
        "Spell: Summon Imp": 99999,
        "1 Gold": 99998,
    }
    location_name_to_id : ClassVar[dict[str, int]] = {
        "Complete Quest: A Threat Within [783]": 1,
        "Complete Quest: Kobold Camp Cleanup [7]": 2,
        "Complete Quest: Investigate Echo Ridge [15]": 3,
        "Complete Quest: Skirmish at Echo Ridge [21]": 4,
        "Complete Quest: Report to Goldshire [54]": 5,
        "Complete Quest: Eagan Peltskinner [5261]": 6,
        "Complete Quest: Wolves Across the Border [33]": 7,
        "Complete Quest: Milly Osworth [3903]": 8,
        "Complete Quest: Milly's Harvest [3904]": 9,
        "Complete Quest: Grape Manifest [3905]": 10,
        "Complete Quest: Brotherhood of Thieves [18]": 11,
        "Complete Quest: Bounty on Garrick Padfoot [6]": 12,
        "Complete Quest: Tainted Letter [3105]": 13,
        "Complete Quest: The Stolen Tome [1598]": 14,
        "Reach Level 1": 99001,
        "Reach Level 2": 99002,
        "Reach Level 3": 99003,
        "Reach Level 4": 99004,
        "Reach Level 5": 99005,
        "Reach Level 6": 99006,
        "Reach Level 7": 99007,
    }

    def __init__(self, multiworld, player):
        super().__init__(multiworld, player)

    def generate_early(self):
        pass

    def create_item(self, name: str):
        item_id = WoWAirbreatherWorld.item_name_to_id[name]
        classification = \
            ItemClassification.progression if 1 <= item_id <= 14 \
            else ItemClassification.filler

        return Item(name, classification, item_id, self.player)

    def create_items(self):
        new_items = [self.create_item(item_name)
                     for item_name in WoWAirbreatherWorld.item_name_to_id]
        for _ in range(2, 8):
            item = self.create_item("Progressive Level Cap")
            item.classification |= ItemClassification.deprioritized
            new_items.append(item)

        while len(new_items) < 21:
            item = self.create_item("1 Gold")
            new_items.append(item)

        self.multiworld.itempool += new_items

    def __quest_region(self, quest_name: str) -> WoWAirbreatherQuestRegion:
        reg = WoWAirbreatherQuestRegion(quest_name, self.player, self.multiworld)
        self.multiworld.regions.append(reg)
        return reg

    def __level_region(self, level: int) -> WoWAirbreatherLevelRegion:
        reg = WoWAirbreatherLevelRegion(level, self.player, self.multiworld)
        self.multiworld.regions.append(reg)
        return reg

    def create_regions(self):
        level1_region = self.__level_region(1)
        self.origin_region_name = level1_region.name
        level2_region = self.__level_region(2)
        level1_region.connect(level2_region, rule=Has("Progressive Level Cap", 1))
        prev_level_region = level2_region
        for lvl in range(3, 8):
            next_region = self.__level_region(lvl)
            prev_level_region.connect(next_region, rule=And(
                prev_level_region.has_reached_level(),
                Has("Progressive Level Cap", lvl - 1),
            ))
            prev_level_region = next_region

        # goal: complete the Report to Goldshire quest
        goldshire_quest_region = self.__quest_region("Report to Goldshire [54]")
        self.set_completion_rule(goldshire_quest_region.has_completed_quest())

        # that quest has a straight line of prerequisites
        skirmish_quest_region = self.__quest_region("Skirmish at Echo Ridge [21]")
        skirmish_quest_region.connect(goldshire_quest_region, rule=And(
            skirmish_quest_region.has_completed_quest(),
            Has("Unlock Quest: Report to Goldshire [54]")
        ))

        investigate_quest_region = self.__quest_region("Investigate Echo Ridge [15]")
        investigate_quest_region.connect(skirmish_quest_region, rule=And(
            investigate_quest_region.has_completed_quest(),
            Has("Unlock Quest: Skirmish at Echo Ridge [21]")
        ))

        cleanup_quest_region = self.__quest_region("Kobold Camp Cleanup [7]")
        cleanup_quest_region.connect(investigate_quest_region, rule=And(
            cleanup_quest_region.has_completed_quest(),
            Has("Unlock Quest: Investigate Echo Ridge [15]")
        ))

        initial_quest_region = self.__quest_region("A Threat Within [783]")
        initial_quest_region.connect(cleanup_quest_region, rule=And(
            initial_quest_region.has_completed_quest(),
            Has("Unlock Quest: Kobold Camp Cleanup [7]")
        ))

        level1_region.connect(initial_quest_region)

        # Grape Manifest ends an optional quest line
        grape_quest_region = self.__quest_region("Grape Manifest [3905]")

        harvest_quest_region = self.__quest_region("Milly's Harvest [3904]")
        harvest_quest_region.connect(grape_quest_region, rule=And(
            harvest_quest_region.has_completed_quest(),
            Has("Unlock Quest: Grape Manifest [3905]")
        ))

        milly_quest_region = self.__quest_region("Milly Osworth [3903]")
        milly_quest_region.connect(harvest_quest_region, rule=And(
            milly_quest_region.has_completed_quest(),
            Has("Unlock Quest: Milly's Harvest [3904]")
        ))

        wolves_quest_region = self.__quest_region("Wolves Across the Border [33]")
        wolves_quest_region.connect(milly_quest_region, rule=And(
            wolves_quest_region.has_completed_quest(),
            Has("Progressive Level Cap", 1),
            Has("Unlock Quest: Milly Osworth [3903]")
        ))

        eagan_quest_region = self.__quest_region("Eagan Peltskinner [5261]")
        eagan_quest_region.connect(wolves_quest_region, rule=And(
            eagan_quest_region.has_completed_quest(),
            Has("Unlock Quest: Wolves Across the Border [33]")
        ))

        initial_quest_region.connect(eagan_quest_region, rule=And(
            initial_quest_region.has_completed_quest(),
            Has("Unlock Quest: Eagan Peltskinner [5261]")
        ))

        # Bounty on Garrick Padfoot ends an optional quest line
        garrick_quest_region = self.__quest_region("Bounty on Garrick Padfoot [6]")

        brotherhood_quest_region = self.__quest_region("Brotherhood of Thieves [18]")
        brotherhood_quest_region.connect(garrick_quest_region, rule=And(
            brotherhood_quest_region.has_completed_quest(),
            Has("Unlock Quest: Bounty on Garrick Padfoot [6]")
        ))

        initial_quest_region.connect(brotherhood_quest_region, rule=And(
            initial_quest_region.has_completed_quest(),
            Has("Progressive Level Cap", 1),
            Has("Unlock Quest: Brotherhood of Thieves [18]")
        ))

        # Tainted Letter ends an optional quest line
        warlock_letter_region = self.__quest_region("Tainted Letter [3105]")

        cleanup_quest_region.connect(warlock_letter_region, rule=And(
            cleanup_quest_region.has_completed_quest(),
            Has("Unlock Quest: Tainted Letter [3105]")
        ))

        stolen_tome_region = self.__quest_region("The Stolen Tome [1598]")
        level1_region.connect(stolen_tome_region, rule=Has("Unlock Quest: The Stolen Tome [1598]"))

    def get_filler_item_name(self):
        assert "1 Gold" in self.item_name_to_id
        return "1 Gold"

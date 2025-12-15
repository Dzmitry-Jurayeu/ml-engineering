import requests
import os
import pandas as pd

APP_ID = os.getenv("APP_ID")
GENERAL_COLUMNS = ["tank_id", "nation", "tier", "type", "name", ]
PREMIUM_COLUMNS = ["tank_id", "nation", "tier", "type", "name", "default_profile.firepower", "default_profile.hp",
                   "default_profile.hull_hp", "default_profile.hull_weight", "default_profile.maneuverability",
                   "default_profile.max_weight", "default_profile.protection", "default_profile.shot_efficiency",
                   "default_profile.signal_range", "default_profile.speed_backward", "default_profile.speed_forward",
                   "default_profile.weight", "default_profile.armor.hull.front", "default_profile.armor.hull.rear",
                   "default_profile.armor.hull.sides", "default_profile.armor.turret.front",
                   "default_profile.armor.turret.rear", "default_profile.armor.turret.sides",
                   "default_profile.engine.fire_chance", "default_profile.engine.power", "default_profile.gun.aim_time",
                   "default_profile.gun.caliber", "default_profile.gun.clip_capacity",
                   "default_profile.gun.clip_reload_time", "default_profile.gun.dispersion",
                   "default_profile.gun.fire_rate", "default_profile.gun.move_down_arc",
                   "default_profile.gun.move_up_arc", "default_profile.gun.reload_time",
                   "default_profile.gun.traverse_speed", "default_profile.suspension.load_limit",
                   "default_profile.suspension.traverse_speed", "default_profile.turret.hp",
                   "default_profile.turret.traverse_left_arc", "default_profile.turret.traverse_right_arc",
                   "default_profile.turret.traverse_speed", "default_profile.turret.view_range", ]


def get_tanks_data():
    general_data = []
    premium_data = []
    url = f"https://papi.tanksblitz.ru/wotb/encyclopedia/vehicles/?application_id={APP_ID}"
    response = requests.get(url)
    for i in response.json().get("data").values():
        if i.get("is_premium"):
            temp_data = {}
            for col in PREMIUM_COLUMNS:
                temp = i
                splitted_col = col.split(".")
                for part_col in splitted_col:
                    temp = temp.get(part_col)
                temp_data[col] = temp
            premium_data.append(temp_data)
        else:
            temp = {k: v for k, v in i.items() if k in GENERAL_COLUMNS}
            general_data.append(temp)
    general_df = pd.DataFrame(general_data, columns=GENERAL_COLUMNS)
    premium_df = pd.DataFrame(premium_data, columns=PREMIUM_COLUMNS)
    tank_drop_ids = [21793, 64769, 64273, 64801]
    premium_df = premium_df[~premium_df.tank_id.isin(tank_drop_ids)]

    return general_df, premium_df


def get_user_data(user_id):
    columns = ["user_id", "tank_id"]
    user_tanks_columns = ["spotted", "hits", "frags", "max_xp", "wins", "losses", "capture_points", "battles",
                          "damage_dealt", "damage_received", "max_frags", "shots", "frags8p", "xp", "win_and_survived",
                          "survived_battles", "dropped_capture_points"]
    tanks_columns = ["battle_life_time", "mark_of_mastery"]
    columns = columns + user_tanks_columns + tanks_columns

    user_df = pd.DataFrame()
    url = f"https://papi.tanksblitz.ru/wotb/tanks/stats/?application_id={APP_ID}&account_id={user_id}"
    data = requests.get(url).json()
    data = data.get("data").get(f"{user_id}")
    if data != None:
        for el in data:
            full_data = {"user_id": [user_id]}
            full_data["tank_id"] = el.get("tank_id")
            full_data["battle_life_time"] = [el.get("battle_life_time")]
            full_data["mark_of_mastery"] = [el.get("mark_of_mastery")]
            for k, v in el.get("all").items():
                full_data[k] = [v]
            temp_df = pd.DataFrame(full_data, columns=columns)
            user_df = pd.concat([user_df, temp_df], ignore_index=True)
    return user_df

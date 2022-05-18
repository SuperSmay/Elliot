import sqlite3
import json
import Interaction
import pathlib

database_name = 'Elliot.sqlite'
database_path = pathlib.Path(database_name)

Interaction.ensure_table_exists()

with open('interactionCountDict', 'r') as file:

    interaction_count_dict = json.load(file)

for user_id, interactions in interaction_count_dict.items():
    if not Interaction.is_user_known(user_id):
        Interaction.initialize_user(user_id)
    for interaction, counts in interactions.items():
        Interaction.update_columns([interaction])
        with sqlite3.connect(database_path) as con:
            cur = con.cursor()
            cur.execute(f"UPDATE interactions SET {interaction}_give = (?) WHERE user_id = {user_id}", [counts['give']])
            cur.execute(f"UPDATE interactions SET {interaction}_receive = (?) WHERE user_id = {user_id}", [counts['receive']])
            
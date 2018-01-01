import hlt
import logging
from collections import OrderedDict

game = hlt.Game("Psyqo-v2")
logging.info("Starting Psyqo-v2")

while True:
    game_map = game.update_map()
    command_queue = []

    team_ships = game_map.get_me().all_ships()

    for ship in team_ships:
        shipid = ship.id

        if ship.docking_status != ship.DockingStatus.UNDOCKED:
            #if it is docked then skip it
            continue

        #get a list of entities in relation to our ship, then order it by that distance
        entities_by_distance = game_map.nearby_entities_by_distance(ship)
        entities_by_distance = OrderedDict(sorted(entities_by_distance.items(), key=lambda t: t[0]))

        #iterate over the entities by distance
        #we make sure its a planet, and that its unowned
        #if that's the case then build a list in order of the distance
        closest_empty_planets = [entities_by_distance[distance][0] for distance in entities_by_distance if
                                 isinstance(entities_by_distance[distance][0], hlt.entity.Planet) and not
                                 entities_by_distance[distance][0].is_owned()]

        #if the entity is a ship, but not ours
        closest_enemy_ships = [entities_by_distance[distance][0] for distance in entities_by_distance if
                                 isinstance(entities_by_distance[distance][0], hlt.entity.Ship) and not
                                 entities_by_distance[distance][0] not in team_ships]

        #if there's at least 1 empty planet, then run towards that planet
        if len(closest_empty_planets) > 0:
            target_planet = closest_empty_planets[0]
            #IF TURN 1 = 3 SHIPS AND ALL EMPTY PLANETS
            if ship.can_dock(target_planet):
                command_queue.append(ship.dock(target_planet))
            else:
                navigate_command = ship.navigate(
                    ship.closest_point_to(target_planet),
                    game_map,
                    speed=int(hlt.constants.MAX_SPEED),
                    ignore_ships=False
                )

                if navigate_command:
                    command_queue.append(navigate_command)

        elif len(closest_enemy_ships) > 0:
            #logging.info("Number of enemy ships: " + str(len(closest_enemy_ships)))
            target_ship = closest_enemy_ships[0]
            navigate_command = ship.navigate(
                ship.closest_point_to(target_ship),
                game_map,
                speed=int(hlt.constants.MAX_SPEED),
                ignore_ships=False
            )

            if navigate_command:
                command_queue.append(navigate_command)

    game.send_command_queue(command_queue)
    # turn end
#game end
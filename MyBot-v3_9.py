import hlt
import logging
from collections import OrderedDict

game = hlt.Game("Psyqo-v4")
logging.info("Starting Psyqo-v4")
turn_number = 0
target_planet1 = None
target_planet2 = None
target_planet3 = None
ship1 = None
ship2 = None
ship3 = None
ship1id = None
ship2id = None
ship3id = None

while True:
    game_map = game.update_map()
    command_queue = []

    team_ships = game_map.get_me().all_ships()
    number_of_enemy_ships = 0

    #print debugging stuff each turn
    logging.info("Turn number: " + str(turn_number))
    logging.info("Number of planets: " + str(len(game_map.all_planets())))
    logging.info("Number of my ships: " + str(len(team_ships)))

    #todo damnit - all this splitting business didn't help us, maybe even hurt us.  what do?
    if turn_number == 0:
        # split up the first 3 ships
        ship1 = team_ships[0]
        ship1id = ship1.id
        ship2 = team_ships[1]
        ship2id = ship2.id
        ship3 = team_ships[2]
        ship3id = ship3.id

        entities_by_distance = game_map.nearby_entities_by_distance(ship1)
        entities_by_distance = OrderedDict(sorted(entities_by_distance.items(), key=lambda t: t[0]))
        closest_empty_planets = [entities_by_distance[distance][0] for distance in entities_by_distance if
                                 isinstance(entities_by_distance[distance][0], hlt.entity.Planet) and not
                                 entities_by_distance[distance][0].is_owned()]
        target_planet1 = closest_empty_planets[0]

        entities_by_distance = game_map.nearby_entities_by_distance(ship2)
        entities_by_distance = OrderedDict(sorted(entities_by_distance.items(), key=lambda t: t[0]))
        closest_empty_planets = [entities_by_distance[distance][0] for distance in entities_by_distance if
                                 isinstance(entities_by_distance[distance][0], hlt.entity.Planet) and not
                                 entities_by_distance[distance][0].is_owned()]
        closest_empty_planets.remove(target_planet1)
        target_planet2 = closest_empty_planets[0]

        entities_by_distance = game_map.nearby_entities_by_distance(ship3)
        entities_by_distance = OrderedDict(sorted(entities_by_distance.items(), key=lambda t: t[0]))
        closest_empty_planets = [entities_by_distance[distance][0] for distance in entities_by_distance if
                                 isinstance(entities_by_distance[distance][0], hlt.entity.Planet) and not
                                 entities_by_distance[distance][0].is_owned()]
        closest_empty_planets.remove(target_planet1)
        closest_empty_planets.remove(target_planet2)
        target_planet3 = closest_empty_planets[0]

    if turn_number < 1:
        #keeping the ship objects from turn to turn didn't work well as the game was sending back new objects each loop
        ship1 = game_map.get_me().get_ship(ship1id)
        ship2 = game_map.get_me().get_ship(ship2id)
        ship3 = game_map.get_me().get_ship(ship3id)
        #logging.info("Ship 1 docking status: " + str(ship1.docking_status))
        # if ship1.docking_status != ship1.DockingStatus.UNDOCKED:
        #     logging.info("Ship 1 is not undocked...")
        # else:
        if ship1.docking_status != ship1.DockingStatus.DOCKED:
            if ship1.can_dock(target_planet1):
                #logging.info("Ship 1 can dock!")
                command_queue.append(ship1.dock(target_planet1))
            else:
                #logging.info("Ship 1 is navigating.")
                navigate_command = ship1.navigate(
                    ship1.closest_point_to(target_planet1),
                    game_map,
                    speed=int(hlt.constants.MAX_SPEED),
                    ignore_ships=False
                )

                if navigate_command:
                    command_queue.append(navigate_command)

        if ship2.docking_status != ship2.DockingStatus.DOCKED:
            if ship2.can_dock(target_planet2):
                logging.info("Ship 2 can dock!")
                command_queue.append(ship2.dock(target_planet2))
            else:
                navigate_command = ship2.navigate(
                    ship2.closest_point_to(target_planet2),
                    game_map,
                    speed=int(hlt.constants.MAX_SPEED),
                    ignore_ships=False
                )

                if navigate_command:
                    command_queue.append(navigate_command)

        if ship3.docking_status != ship3.DockingStatus.DOCKED:
            if ship3.can_dock(target_planet3):
                logging.info("Ship 3 can dock!")
                command_queue.append(ship3.dock(target_planet3))
            else:
                navigate_command = ship3.navigate(
                    ship3.closest_point_to(target_planet3),
                    game_map,
                    speed=int(hlt.constants.MAX_SPEED),
                    ignore_ships=False
                )

                if navigate_command:
                    command_queue.append(navigate_command)

            logging.info("Ship id " + str(ship1.id) + " is going to planet " + str(target_planet1.id))
            logging.info("Ship id " + str(ship2.id) + " is going to planet " + str(target_planet2.id))
            logging.info("Ship id " + str(ship3.id) + " is going to planet " + str(target_planet3.id))
    else:
        for ship in team_ships:
            #shipid = ship.id

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
                                     entities_by_distance[distance][0] in team_ships]

            number_of_enemy_ships = len(closest_enemy_ships)

            #if there's at least 1 empty planet, then run towards that planet
            if len(closest_empty_planets) > 0:
                target_planet = closest_empty_planets[0]
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
                #logging.info("No empty planets - go on the attack")
                #todo which is closer - an enemy ship, or a planet we control without the maximum # of docks?
                target_ship = closest_enemy_ships[0]
                navigate_command = ship.navigate(
                    ship.closest_point_to(target_ship),
                    game_map,
                    speed=int(hlt.constants.MAX_SPEED),
                    ignore_ships=False
                )

                if navigate_command:
                    command_queue.append(navigate_command)

    #turn end debugging
    logging.info("Number of enemy ships: " + str(number_of_enemy_ships))
    turn_number += 1
    game.send_command_queue(command_queue)
    # turn end
#game end
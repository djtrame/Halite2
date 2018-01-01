import hlt
import logging
from collections import OrderedDict

game = hlt.Game("Psyqo-v7")
logging.info("Starting Psyqo-v7")
turn_number = 0
our_player_id = None

while True:
    game_map = game.update_map()
    command_queue = []
    our_player_id = game_map.get_me().id

    team_ships = game_map.get_me().all_ships()
    number_of_enemy_ships = 0

    closest_planet_docking_spots = None
    ships_sent_to_closest_planet = None
    previous_angle = None
    previous_planet_chosen = None

    #print debugging stuff each turn
    logging.info("Turn number: " + str(turn_number))
    #logging.info("Number of planets: " + str(len(game_map.all_planets())))
    #logging.info("Number of my ships: " + str(len(team_ships)))

    new_position_xy_adjust = 0

    #todo need to write the claim logic in order to prevent 3 ships from going to a size 2 planet right at the start
    if turn_number < 3:
        new_position_xy_adjust = 2



    for ship in team_ships:
        # if it is docked then skip it
        if ship.docking_status != ship.DockingStatus.UNDOCKED:
            continue

        #get a list of entities in relation to our ship, then order it by that distance
        entities_by_distance = game_map.nearby_entities_by_distance(ship)
        entities_by_distance = OrderedDict(sorted(entities_by_distance.items(), key=lambda t: t[0]))

        #find a list of owned planets
        closest_owned_planets = [entities_by_distance[distance][0] for distance in entities_by_distance if
                                 isinstance(entities_by_distance[distance][0], hlt.entity.Planet) and
                                 entities_by_distance[distance][0].is_owned()]

        #if the entity is a ship, but not ours
        closest_enemy_ships = [entities_by_distance[distance][0] for distance in entities_by_distance if
                                 isinstance(entities_by_distance[distance][0], hlt.entity.Ship) and not
                                 entities_by_distance[distance][0] in team_ships]

        number_of_enemy_ships = len(closest_enemy_ships)

        #build a list of planets we own
        closest_planets_we_own = []
        for planet in closest_owned_planets:
            if planet.owner.id == our_player_id:
                closest_planets_we_own.append(planet)

        number_of_planets_we_own = len(closest_planets_we_own)

        logging.info("    Debug info for ship ID " + str(ship.id))
        logging.info("      We own this many planets: " + str(number_of_planets_we_own))

        #if we are really close to a planet we own that is not full, then dock there
        closest_unfull_planets_we_own = []
        for planet in closest_planets_we_own:
            if not planet.is_full():
                closest_unfull_planets_we_own.append(planet)

        logging.info("      We own this many unfull planets: " + str(len(closest_unfull_planets_we_own)))
        if len(closest_unfull_planets_we_own) > 0:
            closest_unfull_planet_we_own = closest_unfull_planets_we_own[0]
            logging.info("      The closest unfull planet we own is: " + str(closest_unfull_planet_we_own.id))

            #find the distance between our ship and the closest unfull planet we own
            #we don't want to traverse the map trying to fill a planet... just doing it in close proximity
            distance_between_ship_and_unfull_planet_we_own = ship.calculate_distance_between(closest_unfull_planet_we_own)
            logging.info("      The distance between our ship and that planet is: " + str(distance_between_ship_and_unfull_planet_we_own))

            if distance_between_ship_and_unfull_planet_we_own < 30:
                if number_of_enemy_ships > 0:
                    closest_enemy_ship = closest_enemy_ships[0]
                    logging.info("      The closest enemy ship is: " + str(closest_enemy_ship.id))
                    distance_between_ship_and_enemy_ship = ship.calculate_distance_between(closest_enemy_ship)
                    logging.info("      The distance between our ship and that enemy ship is: " + str(distance_between_ship_and_enemy_ship))

                    if distance_between_ship_and_enemy_ship < 20:
                        # navigate towards that enemy ship
                        navigate_command = ship.navigate(
                            ship.closest_point_to(closest_enemy_ship),
                            game_map,
                            speed=int(hlt.constants.MAX_SPEED),
                            ignore_ships=False
                        )

                        if navigate_command:
                            command_queue.append(navigate_command)
                            logging.info("      We're successfully sending a navigate command to that enemy ship!")
                            continue

                    else:
                        #if an enemy ship is more than 25 units away, then try to dock
                        if ship.can_dock(closest_unfull_planet_we_own):
                            command_queue.append(ship.dock(closest_unfull_planet_we_own))
                            logging.info("      We're successfully docking with that unfull planet we own!")
                            continue
                        else:
                            #move to that unfull planet that we own
                            navigate_command = ship.navigate(
                                ship.closest_point_to(closest_unfull_planet_we_own),
                                game_map,
                                speed=int(hlt.constants.MAX_SPEED),
                                ignore_ships=False
                            )

                            if navigate_command:
                                command_queue.append(navigate_command)
                                logging.info("      We're successfully navigating to that unfull planet we own!")
                                continue


        #iterate over the entities by distance
        #we make sure its a planet, and that its unowned
        #if that's the case then build a list in order of the distance
        closest_empty_planets = [entities_by_distance[distance][0] for distance in entities_by_distance if
                                 isinstance(entities_by_distance[distance][0], hlt.entity.Planet) and not
                                 entities_by_distance[distance][0].is_owned()]


        number_of_empty_planets = len(closest_empty_planets)


        #if there's at least 1 empty planet
        if number_of_empty_planets > 0 and number_of_enemy_ships > 0:
            closest_empty_planet = closest_empty_planets[0]
            #closest_planet_docking_spots =
            # if our ship can dock just go ahead and do it
            if ship.can_dock(closest_empty_planet):
                command_queue.append(ship.dock(closest_empty_planet))
                continue

            # get the distance between this ship and that planet
            distance_between_ship_and_empty_planet = ship.calculate_distance_between(closest_empty_planet)
            #logging.info("Distance between ship id " + str(ship.id) + " and nearest empty planet (id " + str(closest_empty_planet.id) + ") is: " + str(distance_between_ship_and_empty_planet))

            #get the distance between this ship and the nearest enemy ship
            closest_enemy_ship = closest_enemy_ships[0]
            distance_between_ship_and_enemy_ship = ship.calculate_distance_between(closest_enemy_ship)
            #logging.info("Distance between ship id " + str(ship.id) + " and nearest enemy ship (id " + str(closest_enemy_ship.id) + ") is: " + str(distance_between_ship_and_enemy_ship))

            # calc distance between this ship and the nearest empty planet
            # then calc the distance between this ship and the nearest enemy ship
            # if the enemy ship is less than 1/3rd the distance that an empty planet would be, instead attack that ship
            distance_factor = .5
            #if the distance between us and an empty planet is 3x greater than the distance between us and an enemy ship, let's choose the ship
            if distance_between_ship_and_enemy_ship < (distance_between_ship_and_empty_planet * distance_factor):
                #logging.info("We are now 3x closer to an enemy ship than an empty planet. Go to the ship instead.")

                #navigate towards that enemy ship
                navigate_command = ship.navigate(
                    ship.closest_point_to(closest_enemy_ship),
                    game_map,
                    speed=int(hlt.constants.MAX_SPEED),
                    ignore_ships=False
                )

                if navigate_command:
                    command_queue.append(navigate_command)

            else:
                # todo if the 1st planet chosen only has 2 docking spots, send the 3rd ship elsewhere
                # todo if the distance from our ship to an empty planet is closer than that to an unfull planet we own, send it to the empty


                #navigate towards the empty planet
                new_position = ship.closest_point_to(closest_empty_planet)
                if turn_number < 40:
                    #new_position.x += new_position_xy_adjust
                    #new_position.y += new_position_xy_adjust
                    #new_position_xy_adjust += 1
                    #angle between ship and empty planet
                    angle_between_ship_and_empty_planet = ship.calculate_angle_between(closest_empty_planet)
                    angle_between_empty_planet_and_ship = closest_empty_planet.calculate_angle_between(ship)
                    logging.info("      Angle between ship (id " + str(ship.id) + ") and nearest empty planet (id " + str(
                        closest_empty_planet.id) + ") is: " + str(angle_between_ship_and_empty_planet))
                    logging.info("      Angle between nearest empty planet (id " + str(closest_empty_planet.id) + ") and ship (id " + str(
                        ship.id) + ") is: " + str(angle_between_empty_planet_and_ship))

                #we've picked an empty planet to go to, so add a claim to that planet
                #first make sure that planet doesn't have a full assortment of claims
                if len(closest_empty_planet.get_claims()) < closest_empty_planet.num_docking_spots:
                    closest_empty_planet.claim(ship)

                    #split off the first 3 ships
                    if turn_number < 10:
                        #this means we're working on the first ship
                        if previous_angle is None:
                            previous_angle = angle_between_ship_and_empty_planet
                        else:
                            #if there is a previous angle, compare it to this one
                            angle_difference = angle_between_ship_and_empty_planet - previous_angle
                            logging.info("      Angle difference: " + str(angle_difference))

                            if 45 <= angle_between_ship_and_empty_planet < 135:
                                logging.info("      Current angle is between 45 and 135.")
                            elif 135 <= angle_between_ship_and_empty_planet < 225:
                                logging.info("      Current angle is between 135 and 225.")
                            elif 225 <= angle_between_ship_and_empty_planet < 315:
                                logging.info("      Current angle is between 225 and 315.")
                            else:
                                logging.info("      Current angle is between 315 and 45.")
                                #todo still gotta fix the fucking claims with 3 on size 2 otherwise this shit don't matter
                                if angle_difference >= 0:
                                    new_position.y += 1
                                else:
                                    new_position.y -= 1




                    #     ship0 = team_ships[0]
                    #     #new_position.x = 240
                    #     navigate_command = ship0.navigate(
                    #         new_position,
                    #         game_map,
                    #         speed=int(hlt.constants.MAX_SPEED),
                    #         ignore_ships=False
                    #     )
                    #
                    #     if navigate_command:
                    #         command_queue.append(navigate_command)
                    #
                    #     ship1 = team_ships[1]
                    #     # new_position.x = 240
                    #     navigate_command = ship1.navigate(
                    #         new_position,
                    #         game_map,
                    #         speed=int(hlt.constants.MAX_SPEED),
                    #         ignore_ships=False
                    #     )
                    #
                    #     if navigate_command:
                    #         command_queue.append(navigate_command)
                    #
                    #     ship2 = team_ships[2]
                    #     # new_position.x = 240
                    #     navigate_command = ship2.navigate(
                    #         new_position,
                    #         game_map,
                    #         speed=int(hlt.constants.MAX_SPEED),
                    #         ignore_ships=False
                    #     )
                    #
                    #     if navigate_command:
                    #         command_queue.append(navigate_command)
                    #
                    #     #turn_number += 1
                    #     #game.send_command_queue(command_queue)
                    #     continue

                    #we've claimed that planet, so navigate to it
                    navigate_command = ship.navigate(
                        new_position,
                        game_map,
                        speed=int(hlt.constants.MAX_SPEED),
                        ignore_ships=False
                    )
                else:
                    #else check if there is more than 1 empty planet
                    if len(closest_empty_planets) > 1:
                        navigate_command = ship.navigate(
                            ship.closest_point_to(closest_empty_planets[1]),
                            game_map,
                            speed=int(hlt.constants.MAX_SPEED),
                            ignore_ships=False
                        )
                    else:
                        #move to closest enemy ship instead
                        closest_enemy_ship = closest_enemy_ships[0]

                        navigate_command = ship.navigate(
                            ship.closest_point_to(closest_enemy_ship),
                            game_map,
                            speed=int(hlt.constants.MAX_SPEED),
                            ignore_ships=False
                        )

                if navigate_command:
                    command_queue.append(navigate_command)

        elif number_of_enemy_ships > 0:
            #if there are no empty planets, just move to the nearest enemy ship
            closest_enemy_ship = closest_enemy_ships[0]

            navigate_command = ship.navigate(
                ship.closest_point_to(closest_enemy_ship),
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
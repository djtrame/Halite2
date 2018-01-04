import hlt
import logging
import math
from collections import OrderedDict

def establish_ship_to_ship_distances(my_ships, all_ships, docked, threshold=6):
    """
    Establish a list/dict of how close enemy ships are to our ships
    Code based on marcintustin's Halite2_py3_alpha repo
    I'm not skilled in numpy so this will be quite rudimentary programming
    :param my_ships: My ships
    :param all_ships: All ships
    :param docked: Boolean that allows us to look at docked or undocked enemy ships
    :param threshold: Distance between ships that we are concerned about
    :return:
    """
    if len(my_ships) <= 0 or len(all_ships) <= 0:
        raise ValueError("Sets of ships may not be empty")

    my_id = my_ships[0].owner

    my_undocked_ships = []
    for ship in my_ships:
        if ship.docking_status == ship.DockingStatus.UNDOCKED:
            my_undocked_ships.append(ship)

    enemy_ships = []
    #loop through all ships
    for ship in all_ships:
        #if we aren't the owner
        if ship.owner != my_id:
            #if the ship isn't docked
            if not docked:
                if ship.docking_status == ship.docking_status.UNDOCKED:
                    enemy_ships.append(ship)
            else:
                if not ship.docking_status == ship.docking_status.UNDOCKED:
                    enemy_ships.append(ship)

            #original code - didn't seem to work for docked enemy ships check
            # if ship.docking_status == ship.docking_status.UNDOCKED and not docked:
            #     enemy_ships.append(ship)
            # else:
            #     enemy_ships.append(ship)

    results = {}
    #loop through all our undocked ships
    for ship in my_undocked_ships:

        enemy_ships_in_range = []

        #loop through all enemy ships
        for enemy_ship in enemy_ships:
            #get the distance between each
            distance_between = ship.calculate_distance_between(enemy_ship)
            #if the enemy ship is close enough for us to care about
            if distance_between < threshold:
                #then add it to a list
                enemy_ships_in_range.append(enemy_ship)

        #add the list of enemy ships as a value paired with the key of our ship to a dictionary
        results[ship] = enemy_ships_in_range

    # return a dictionary with our ship as the key, and the value being a list of enemy ships
    # for now if there's at least 1 enemy ship in range we'd just target the 0th element, as that list isn't sorted
    # but being within 6 or so units we aren't terribly worried about spending the time sorting that list
    return results

game = hlt.Game("Psyqo-v7")
logging.info("Starting Psyqo-v7")
turn_number = 0
our_player_id = None

while True:
    game_map = game.update_map()

    #reset all claims on all planets so as to establish the best course of action each turn
    #making sure to treat a dock as 1 claim
    game_map.clear_all_claims_on_planets()
    command_queue = []
    our_player_id = game_map.get_me().id

    team_ships = game_map.get_me().all_ships()
    number_of_enemy_ships = 0

    #closest_planet_docking_spots = None
    #ships_sent_to_closest_planet = None
    #previous_angle = None
    #previous_planet_chosen = None

    #print debugging stuff each turn
    logging.info("Turn number: " + str(turn_number))
    #logging.info("Number of planets: " + str(len(game_map.all_planets())))
    #logging.info("Number of my ships: " + str(len(team_ships)))

    #new_position_xy_adjust = 0

    our_ships_to_undocked_enemy_ships = establish_ship_to_ship_distances(team_ships, game_map._all_ships(), False, threshold=20)
    undocked_enemy_ships_counter = 0
    for key, value in our_ships_to_undocked_enemy_ships.items():
        if len(value) > 0:
            #logging.info("    Key: " + str(key))
            #logging.info("      Value: " + str(value))
            undocked_enemy_ships_counter += 1

    logging.info("  Count of undocked enemy ships within 6 units of our ships: " + str(undocked_enemy_ships_counter))

    our_ships_to_docked_enemy_ships = establish_ship_to_ship_distances(team_ships, game_map._all_ships(), True, threshold=500)
    docked_enemy_ships_counter = 0
    for key, value in our_ships_to_docked_enemy_ships.items():
        if len(value) > 0:
            #logging.info("    Key: " + str(key))
            #logging.info("      Value: " + str(value))
            docked_enemy_ships_counter += 1

    logging.info("  Count of docked enemy ships within 500 units of our ships: " + str(docked_enemy_ships_counter))

    ship_angle_adjusted = False

    #todo fucking fuck god damnit the first 2 ships can still run into themselves
    for ship in team_ships:
        # if it is docked then skip it
        if ship.docking_status != ship.DockingStatus.UNDOCKED:
            continue

        logging.info("    Debug info for ship ID " + str(ship.id))

        target_object = None

        logging.info("      The amount of undocked, nearby enemy ships is: " + str(len(our_ships_to_undocked_enemy_ships[ship])))

        #go towards flying enemy ships if they are super close
        if ship in our_ships_to_undocked_enemy_ships and len(our_ships_to_undocked_enemy_ships[ship]) > 0:
            enemy_ship = our_ships_to_undocked_enemy_ships[ship][0]
            logging.info("We've found an enemy ship (id {0}) within X units of our ship, so engage!".format(enemy_ship.id))
            target_object = enemy_ship

        #get a list of planets sorted by distance to us
        closest_planets = OrderedDict(sorted(game_map.nearby_planets_by_distance(ship).items(), key=lambda t: t[0]))

        #logging.info("Closest planets: " + str(closest_planets))

        #loop through the closest planets and decide which one we want to take action on
        #todo fix bug with this code - if ship id 0 is furthest away, it gets 1st pick at the planet.  then ship 2 picks one that it thought was closest, but reevaluates itself next turn
        if target_object is None:
            for key, value in closest_planets.items():
                planet = value[0]
                logging.info("      Starting Planet loop with ID {0}".format(planet.id))
                if planet.is_owned():
                    logging.info("        This planet is owned.")
                    #if we own it
                    if planet.owner.id == our_player_id:
                        logging.info("        We own it.")
                        #if it's not full
                        if not planet.is_full():
                            logging.info("        This planet isn't full.")
                            #check if we can make a claim on this planet
                            #should we reset claims each turn?  or carry them over?
                            #i think turn them over so when a ship spawns on a planet, it can make its own claim
                            #and allow a ship traveling to that planet to turn around and go do something else useful
                            logging.info("        It has {0} docking spots.".format(planet.num_docking_spots))
                            logging.info("        It currently has {0} claims.".format(len(planet.get_claims())))
                            if len(planet.get_claims()) < planet.num_docking_spots:
                                #make a claim
                                planet.claim(ship)
                                target_object = planet
                                logging.info(
                                    "        We are making a claim on this planet and are breaking the planet loop.")

                                #we've established our target, so break the closest_planets loop
                                break
                else:
                    #if a planet isn't owned, then try to make a claim on it
                    logging.info("        Planet id: {0} is not owned.".format(planet.id))
                    logging.info("        It has {0} docking spots.".format(planet.num_docking_spots))
                    logging.info("        It currently has {0} claims.".format(len(planet.get_claims())))
                    if turn_number < 4:
                        if len(planet.get_claims()) < planet.num_docking_spots:
                            # make a claim
                            planet.claim(ship)

                            #or just try to dock later in the code
                            target_object = planet

                            logging.info("        We are making a claim on this planet and are breaking the planet loop.")

                            #break the planet loop
                            break
                        else:
                            logging.info("        This planet has reached it's maximum claim amount.  Move onto the next planet.")
                    else:
                        if len(planet.get_claims()) < 1: #test code, kill it?
                            # make a claim
                            planet.claim(ship)

                            # or just try to dock later in the code
                            target_object = planet
                            # break the planet loop
                            break

        #if we still don't have a plan, then go towards the nearest docked enemy ship
        #there should be NO situation where all are true:
            #there are no empty planets
            #there are no unfull planets we own
            #there are no undocked enemy ships within 6 units
            #there are no docked enemy ships within 500 units
        #i think it's safe to say we just send this guy along to the nearest docked enemy ship and call it a day
        if target_object is None:
            docked_enemy_ships_near_this_ship = len(our_ships_to_docked_enemy_ships[ship])
            if docked_enemy_ships_near_this_ship > 0:
                logging.info("      The amount of docked nearby enemy ships is: " + str(docked_enemy_ships_near_this_ship))
                #send the ship to the closest docked enemy ship
                target_object = our_ships_to_docked_enemy_ships[ship][0]
                logging.info("We are going after docked enemy ship {0}".format(target_object.id))
            else:
                logging.info("*********************** Something has gone terribly wrong!  ERROR!***********************")

        if target_object:
            #is it a planet?
            if isinstance(target_object, hlt.entity.Planet):
                #can we dock at it?
                if ship.can_dock(target_object):
                    command_queue.append(ship.dock(target_object))
                else:
                    # if we can't dock, just move towards the object
                    new_position = ship.closest_point_to(target_object)

                    #trig debug code
                    if turn_number < 10:
                        #angle between ship and empty planet
                        angle_between_ship_and_empty_planet = ship.calculate_angle_between(target_object)
                        logging.info("        The angle between this ship and planet #{0} is {1}".format(target_object.id,angle_between_ship_and_empty_planet))
                        angle_between_empty_planet_and_ship = target_object.calculate_angle_between(ship)
                        logging.info("        The angle between planet #{0} and this ship is {1}".format(target_object.id,
                                                                                                         angle_between_empty_planet_and_ship))
                        logging.info("        The center point of this planet is: {0},{1}".format(target_object.x, target_object.y))
                        logging.info("        The point our ship is navigating towards is: {0},{1}".format(new_position.x, new_position.y))
                        logging.info("        The radius of the planet is: {0}".format(target_object.radius))
                        rebased_X_units = new_position.x - target_object.x
                        rebased_Y_units = target_object.y - new_position.y
                        logging.info("        The rebased units are: {0},{1}".format(rebased_X_units,rebased_Y_units))
                        are_we_traveling_up = None
                        if rebased_Y_units < 0 and angle_between_ship_and_empty_planet > 180:
                            are_we_traveling_up = True
                        else:
                            are_we_traveling_up = False

                        logging.info("        Are we traveling up?: {0}".format(are_we_traveling_up))


                        #cos(t) = x/r (isolate for theta).  be sure to include the fudge of 3.
                        x_over_radius = rebased_X_units / (target_object.radius + 3)
                        logging.info("        The radius ratio is: {0}".format(x_over_radius))
                        #t = arccos(x/r)
                        theta = math.acos(x_over_radius)
                        logging.info("        Theta is: {0}".format(theta))
                        theta_degrees = theta * 180 / math.pi
                        logging.info("        Theta in degrees is: {0}".format(theta_degrees))
                        #subtract 180 from angle between ship and planet
                        true_angle = angle_between_ship_and_empty_planet - 180
                        logging.info("        True angle: {0}".format(true_angle))
                        #establish an additional angle by adding some radians
                        gamma = .2

                        if are_we_traveling_up:
                            gamma *= -1

                        bigger_angle_x = (target_object.radius + 3) * math.cos(theta + gamma)
                        bigger_angle_y = (target_object.radius + 3) * math.sin(theta + gamma)
                        new_angle = math.acos(bigger_angle_x / (target_object.radius + 3))
                        new_angle_degrees = new_angle * 180 / math.pi
                        logging.info("        The new angle in degrees is: {0}".format(new_angle_degrees))

                        #bug - if we're coming up from the bottom, the theta degrees represents an angle from x to -y.  so if we add to it, we end up moving clockwise.
                        logging.info("        If we add to this angle a new target position relative to the planet could be: {0},{1}".format(bigger_angle_x, bigger_angle_y))

                        absolute_bigger_angle_x = bigger_angle_x + target_object.x
                        absolute_bigger_angle_y = bigger_angle_y + target_object.y
                        logging.info("        A true new spot on the plane (counter clockwise from prior spot on the planet) is: {0},{1}".format(absolute_bigger_angle_x,absolute_bigger_angle_y))

                        if not ship_angle_adjusted:
                            new_position.x = absolute_bigger_angle_x
                            new_position.y = absolute_bigger_angle_y
                            ship_angle_adjusted = True

                        #trying random bullshit to scoot initial ships away from each other
                        #new_position.x = len(target_object.get_claims()) * 5
                        #new_position.y = len(target_object.get_claims()) * 5

                    navigate_command = ship.navigate(
                        new_position,
                        game_map,
                        #suggestion by Mandrewoid - didn't work out.  too slow of a start and sometimes 2 ships still crashed
                        #speed=min(turn_number+1,hlt.constants.MAX_SPEED),
                        speed=int(hlt.constants.MAX_SPEED),
                        ignore_ships=False
                    )

                    if navigate_command:
                        command_queue.append(navigate_command)

            else:
                #it must be a ship, so just move towards it and ignore collisions
                navigate_command = ship.navigate(
                    ship.closest_point_to(target_object),
                    game_map,
                    speed=int(hlt.constants.MAX_SPEED),
                    ignore_ships=False
                )

                if navigate_command:
                    command_queue.append(navigate_command)
        else:
            logging.info("No target found for this ship this turn.  What do?")

        #begin v6 block comment
        # #if the entity is a ship, but not ours
        # closest_enemy_ships = [entities_by_distance[distance][0] for distance in entities_by_distance if
        #                          isinstance(entities_by_distance[distance][0], hlt.entity.Ship) and not
        #                          entities_by_distance[distance][0] in team_ships]
        #
        # number_of_enemy_ships = len(closest_enemy_ships)
        #
        # #build a list of planets we own
        # closest_planets_we_own = []
        # for planet in closest_owned_planets:
        #     if planet.owner.id == our_player_id:
        #         closest_planets_we_own.append(planet)
        #
        # number_of_planets_we_own = len(closest_planets_we_own)
        #
        #
        # logging.info("      We own this many planets: " + str(number_of_planets_we_own))
        #
        # #if we are really close to a planet we own that is not full, then dock there
        # closest_unfull_planets_we_own = []
        # for planet in closest_planets_we_own:
        #     if not planet.is_full():
        #         closest_unfull_planets_we_own.append(planet)
        #
        # logging.info("      We own this many unfull planets: " + str(len(closest_unfull_planets_we_own)))
        # if len(closest_unfull_planets_we_own) > 0:
        #     closest_unfull_planet_we_own = closest_unfull_planets_we_own[0]
        #     logging.info("      The closest unfull planet we own is: " + str(closest_unfull_planet_we_own.id))
        #
        #     #find the distance between our ship and the closest unfull planet we own
        #     #we don't want to traverse the map trying to fill a planet... just doing it in close proximity
        #     distance_between_ship_and_unfull_planet_we_own = ship.calculate_distance_between(closest_unfull_planet_we_own)
        #     logging.info("      The distance between our ship and that planet is: " + str(distance_between_ship_and_unfull_planet_we_own))
        #
        #     if distance_between_ship_and_unfull_planet_we_own < 30:
        #         if number_of_enemy_ships > 0:
        #             closest_enemy_ship = closest_enemy_ships[0]
        #             logging.info("      The closest enemy ship is: " + str(closest_enemy_ship.id))
        #             distance_between_ship_and_enemy_ship = ship.calculate_distance_between(closest_enemy_ship)
        #             logging.info("      The distance between our ship and that enemy ship is: " + str(distance_between_ship_and_enemy_ship))
        #
        #             if distance_between_ship_and_enemy_ship < 20:
        #                 # navigate towards that enemy ship
        #                 navigate_command = ship.navigate(
        #                     ship.closest_point_to(closest_enemy_ship),
        #                     game_map,
        #                     speed=int(hlt.constants.MAX_SPEED),
        #                     ignore_ships=False
        #                 )
        #
        #                 if navigate_command:
        #                     command_queue.append(navigate_command)
        #                     logging.info("      We're successfully sending a navigate command to that enemy ship!")
        #                     continue
        #
        #             else:
        #                 #if an enemy ship is more than 25 units away, then try to dock
        #                 if ship.can_dock(closest_unfull_planet_we_own):
        #                     command_queue.append(ship.dock(closest_unfull_planet_we_own))
        #                     logging.info("      We're successfully docking with that unfull planet we own!")
        #                     continue
        #                 else:
        #                     #move to that unfull planet that we own
        #                     navigate_command = ship.navigate(
        #                         ship.closest_point_to(closest_unfull_planet_we_own),
        #                         game_map,
        #                         speed=int(hlt.constants.MAX_SPEED),
        #                         ignore_ships=False
        #                     )
        #
        #                     if navigate_command:
        #                         command_queue.append(navigate_command)
        #                         logging.info("      We're successfully navigating to that unfull planet we own!")
        #                         continue
        #
        #
        # #iterate over the entities by distance
        # #we make sure its a planet, and that its unowned
        # #if that's the case then build a list in order of the distance
        # closest_empty_planets = [entities_by_distance[distance][0] for distance in entities_by_distance if
        #                          isinstance(entities_by_distance[distance][0], hlt.entity.Planet) and not
        #                          entities_by_distance[distance][0].is_owned()]
        #
        #
        # number_of_empty_planets = len(closest_empty_planets)
        #
        #
        # #if there's at least 1 empty planet
        # if number_of_empty_planets > 0 and number_of_enemy_ships > 0:
        #     closest_empty_planet = closest_empty_planets[0]
        #     #closest_planet_docking_spots =
        #     # if our ship can dock just go ahead and do it
        #     if ship.can_dock(closest_empty_planet):
        #         command_queue.append(ship.dock(closest_empty_planet))
        #         continue
        #
        #     # get the distance between this ship and that planet
        #     distance_between_ship_and_empty_planet = ship.calculate_distance_between(closest_empty_planet)
        #     #logging.info("Distance between ship id " + str(ship.id) + " and nearest empty planet (id " + str(closest_empty_planet.id) + ") is: " + str(distance_between_ship_and_empty_planet))
        #
        #     #get the distance between this ship and the nearest enemy ship
        #     closest_enemy_ship = closest_enemy_ships[0]
        #     distance_between_ship_and_enemy_ship = ship.calculate_distance_between(closest_enemy_ship)
        #     #logging.info("Distance between ship id " + str(ship.id) + " and nearest enemy ship (id " + str(closest_enemy_ship.id) + ") is: " + str(distance_between_ship_and_enemy_ship))
        #
        #     # calc distance between this ship and the nearest empty planet
        #     # then calc the distance between this ship and the nearest enemy ship
        #     # if the enemy ship is less than 1/3rd the distance that an empty planet would be, instead attack that ship
        #     distance_factor = .5
        #     #if the distance between us and an empty planet is 3x greater than the distance between us and an enemy ship, let's choose the ship
        #     if distance_between_ship_and_enemy_ship < (distance_between_ship_and_empty_planet * distance_factor):
        #         #logging.info("We are now 3x closer to an enemy ship than an empty planet. Go to the ship instead.")
        #
        #         #navigate towards that enemy ship
        #         navigate_command = ship.navigate(
        #             ship.closest_point_to(closest_enemy_ship),
        #             game_map,
        #             speed=int(hlt.constants.MAX_SPEED),
        #             ignore_ships=False
        #         )
        #
        #         if navigate_command:
        #             command_queue.append(navigate_command)
        #
        #     else:
        #         # todo if the 1st planet chosen only has 2 docking spots, send the 3rd ship elsewhere
        #         # todo if the distance from our ship to an empty planet is closer than that to an unfull planet we own, send it to the empty
        #
        #
        #         #navigate towards the empty planet
        #         new_position = ship.closest_point_to(closest_empty_planet)
        #         if turn_number < 40:
        #             #new_position.x += new_position_xy_adjust
        #             #new_position.y += new_position_xy_adjust
        #             #new_position_xy_adjust += 1
        #             #angle between ship and empty planet
        #             angle_between_ship_and_empty_planet = ship.calculate_angle_between(closest_empty_planet)
        #             angle_between_empty_planet_and_ship = closest_empty_planet.calculate_angle_between(ship)
        #             logging.info("      Angle between ship (id " + str(ship.id) + ") and nearest empty planet (id " + str(
        #                 closest_empty_planet.id) + ") is: " + str(angle_between_ship_and_empty_planet))
        #             logging.info("      Angle between nearest empty planet (id " + str(closest_empty_planet.id) + ") and ship (id " + str(
        #                 ship.id) + ") is: " + str(angle_between_empty_planet_and_ship))
        #
        #         #we've picked an empty planet to go to, so add a claim to that planet
        #         #first make sure that planet doesn't have a full assortment of claims
        #         if len(closest_empty_planet.get_claims()) < closest_empty_planet.num_docking_spots:
        #             closest_empty_planet.claim(ship)
        #
        #             #split off the first 3 ships
        #             if turn_number < 10:
        #                 #this means we're working on the first ship
        #                 if previous_angle is None:
        #                     previous_angle = angle_between_ship_and_empty_planet
        #                 else:
        #                     #if there is a previous angle, compare it to this one
        #                     angle_difference = angle_between_ship_and_empty_planet - previous_angle
        #                     logging.info("      Angle difference: " + str(angle_difference))
        #
        #                     if 45 <= angle_between_ship_and_empty_planet < 135:
        #                         logging.info("      Current angle is between 45 and 135.")
        #                     elif 135 <= angle_between_ship_and_empty_planet < 225:
        #                         logging.info("      Current angle is between 135 and 225.")
        #                     elif 225 <= angle_between_ship_and_empty_planet < 315:
        #                         logging.info("      Current angle is between 225 and 315.")
        #                     else:
        #                         logging.info("      Current angle is between 315 and 45.")
        #                         #todo still gotta fix the fucking claims with 3 on size 2 otherwise this shit don't matter
        #                         if angle_difference >= 0:
        #                             new_position.y += 1
        #                         else:
        #                             new_position.y -= 1
        #
        #             #we've claimed that planet, so navigate to it
        #             navigate_command = ship.navigate(
        #                 new_position,
        #                 game_map,
        #                 speed=int(hlt.constants.MAX_SPEED),
        #                 ignore_ships=False
        #             )
        #         else:
        #             #else check if there is more than 1 empty planet
        #             if len(closest_empty_planets) > 1:
        #                 navigate_command = ship.navigate(
        #                     ship.closest_point_to(closest_empty_planets[1]),
        #                     game_map,
        #                     speed=int(hlt.constants.MAX_SPEED),
        #                     ignore_ships=False
        #                 )
        #             else:
        #                 #move to closest enemy ship instead
        #                 closest_enemy_ship = closest_enemy_ships[0]
        #
        #                 navigate_command = ship.navigate(
        #                     ship.closest_point_to(closest_enemy_ship),
        #                     game_map,
        #                     speed=int(hlt.constants.MAX_SPEED),
        #                     ignore_ships=False
        #                 )
        #
        #         if navigate_command:
        #             command_queue.append(navigate_command)
        #
        # elif number_of_enemy_ships > 0:
        #     #if there are no empty planets, just move to the nearest enemy ship
        #     closest_enemy_ship = closest_enemy_ships[0]
        #
        #     navigate_command = ship.navigate(
        #         ship.closest_point_to(closest_enemy_ship),
        #         game_map,
        #         speed=int(hlt.constants.MAX_SPEED),
        #         ignore_ships=False
        #     )
        #
        #     if navigate_command:
        #         command_queue.append(navigate_command)
        #end v6 block comment


    #turn end debugging
    logging.info("Number of enemy ships: " + str(number_of_enemy_ships))
    turn_number += 1
    game.send_command_queue(command_queue)
    # turn end
#game end
from ortools.constraint_solver import routing_enums_pb2, pywrapcp
import numpy as np
from geopy.distance import geodesic

def create_distance_matrix(coords):
    """
    Returns a symmetric distance matrix (in km) between all coordinates.
    coords: list of [lat, lon]
    """
    n = len(coords)
    matrix = np.zeros((n, n))
    for i in range(n):
        for j in range(n):
            if i == j:
                matrix[i, j] = 0
            else:
                matrix[i, j] = geodesic(coords[i], coords[j]).km
    return matrix.tolist()

def solve_vrp(df, num_groups, depot_idx=0, lat_col='latitude', lon_col='longitude'):
    """
    Solves the Vehicle Routing Problem using OR-Tools.
    Args:
        df: pandas DataFrame containing address data, must include latitude and longitude columns.
        num_groups: number of vehicles/groups.
        depot_idx: index of depot (default: 0).
        lat_col: name of latitude column in df.
        lon_col: name of longitude column in df.
    Returns:
        routes: list of lists, where each sublist is the indices of the route for a group.
    """
    coords = df[[lat_col, lon_col]].values.tolist()
    distance_matrix = create_distance_matrix(coords)

    manager = pywrapcp.RoutingIndexManager(len(distance_matrix), num_groups, depot_idx)
    routing = pywrapcp.RoutingModel(manager)

    def distance_callback(from_index, to_index):
        from_node = manager.IndexToNode(from_index)
        to_node = manager.IndexToNode(to_index)
        return int(distance_matrix[from_node][to_node] * 1000)  # meters

    transit_callback_index = routing.RegisterTransitCallback(distance_callback)
    routing.SetArcCostEvaluatorOfAllVehicles(transit_callback_index)

    # No capacity constraints here; add if needed

    search_parameters = pywrapcp.DefaultRoutingSearchParameters()
    search_parameters.time_limit.seconds = 10
    search_parameters.first_solution_strategy = (
        routing_enums_pb2.FirstSolutionStrategy.PATH_CHEAPEST_ARC)

    solution = routing.SolveWithParameters(search_parameters)
    routes = []
    if solution:
        for vehicle_id in range(num_groups):
            index = routing.Start(vehicle_id)
            route = []
            while not routing.IsEnd(index):
                route.append(manager.IndexToNode(index))
                index = solution.Value(routing.NextVar(index))
            route.append(manager.IndexToNode(index))  # End node
            routes.append(route)
    else:
        print("No solution found.")
        routes = None
    return routes
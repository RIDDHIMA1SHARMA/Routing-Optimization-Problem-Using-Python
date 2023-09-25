import math
import pandas as pd
import networkx as nx

def convert_to_cartesian(lat, lon, alt):
    lat_rad = math.radians(lat)
    lon_rad = math.radians(lon)
    x = (float(alt) + 6371000) * math.cos(lat_rad) * math.cos(lon_rad)
    y = (float(alt) + 6371000) * math.cos(lat_rad) * math.sin(lon_rad)
    z = (float(alt) + 6371000) * math.sin(lat_rad)
    return x, y, z

def calculate_distance(point1, point2):
    x1, y1, z1 = point1
    x2, y2, z2 = point2
    distance = math.sqrt((x2 - x1) ** 2 + (y2 - y1) ** 2 + (z2 - z1) ** 2)
    return distance

data = pd.read_csv("data.txt", delimiter=",")
df = pd.DataFrame(data)
G = nx.Graph()

latitude, longitude, altitude = convert_to_cartesian(74.1745, -40.689, 8.72)
G.add_node("LHR", altitude=altitude, latitude=latitude, longitude=longitude)
latitude, longitude, altitude = convert_to_cartesian(0.4543, 51.4700, 81.73)
G.add_node("EWR", altitude=altitude, latitude=latitude, longitude=longitude)

for index, row in df.iterrows():
    flightNo = row["Flight no"]
    latitude, longitude, altitude = convert_to_cartesian(
        row["Latitude"], row["Longitude"], row["Altitude"]
    )
    G.add_node(flightNo, altitude=altitude, latitude=latitude, longitude=longitude)

graphRate = {}
graphLat = {}
ground_stations = {
    "LHR": convert_to_cartesian(51.4700, -0.4543, 81.73),
    "EWR": convert_to_cartesian(40.6895, -74.1745, 8.72),
}
# Optimal path
for index, row in df.iterrows():
    flightNo = row["Flight no"]
    altitude = row["Altitude"]
    latitude = row["Latitude"]
    longitude = row["Longitude"]
    G.add_node(flightNo, altitude=altitude, latitude=latitude, longitude=longitude)

for i, row1 in df.iterrows():
    for j, row2 in df.iterrows():
        if i != j:
            distance = calculate_distance(
                [row1["Latitude"], row1["Longitude"], row1["Altitude"]],
                [row2["Latitude"], row2["Longitude"], row2["Altitude"]],
            )
            if distance >= 500:
                weight = 31.895
            elif distance >= 400 and distance < 500:
                weight = 43.505
            elif distance >= 300 and distance < 400:
                weight = 43.505
            elif distance >= 190 and distance < 300:
                weight = 43.505
            elif distance >= 90 and distance < 190:
                weight = 43.505
            elif distance >= 35 and distance < 90:
                weight = 43.505
            else:
                weight = 119.130
            G.add_edge(row1["Flight no"], row2["Flight no"], weight=weight)

for i, row in df.iterrows():
    for ground_station in ["LHR", "EWR"]:
        distance = calculate_distance(
            [row["Latitude"], row["Longitude"], row["Altitude"]],
            [
                G.nodes[ground_station]["latitude"],
                G.nodes[ground_station]["longitude"],
                G.nodes[ground_station]["altitude"],
            ],
        )
        transmission_rate = (
            52.875 if distance <= 400 else abs((1000 - distance / 100) / 1000)
        )
        G.add_edge(row1["Flight no"], row2["Flight no"], weight=transmission_rate)
optimal_paths = {}
for flight_no in df["Flight no"]:
    shortest_paths = nx.single_source_dijkstra_path(G, flight_no, weight="weight")
    optimal_path = max(shortest_paths, key=lambda x: shortest_paths[x][-1])
    optimal_paths[flight_no] = shortest_paths[optimal_path]
# transmission_rate and transmission_delay
for flightNo, row in df.iterrows():
    current_node = (
        flightNo,
        convert_to_cartesian(row["Latitude"], row["Longitude"], row["Altitude"]),
    )
    graphRate[current_node] = []
    graphLat[current_node] = []
    for gs, gs_coordinates in ground_stations.items():
        distance = calculate_distance(current_node[1], gs_coordinates)
        transmission_rate = (
            52.875 if distance <= 400 else abs((1000 - distance / 100) / 1000)
        )
        graphRate[current_node].append((gs, transmission_rate))
        propogation_delay = distance / 300000000
        transmission_delay = 70 / transmission_rate
        latency = transmission_delay + propogation_delay
        graphLat[current_node] = latency

optimal_path = []
for node in graphRate:
    current_path = [node]
    current_rate = 0
    while current_path[-1][0] not in ground_stations:
        neighbors = graphRate[current_path[-1]]
        max_rate = max(neighbors, key=lambda x: x[1])
        current_path.append(max_rate)
        current_rate = max_rate[1]
        optimal_path.append((node[0], current_path, current_rate))
    optimal_path.sort(key=lambda x: x[2], reverse=True)
d = False

for Flight, path, rate in optimal_path:
    print(f"Flight No: {Flight}")
    for node in path:
        if d:
            print(f"- {node[0]}")
            d = False
        else:
            d = True
            print(f"Maximum Data Transmission Rate: {rate} Mbps")
    for lat in graphLat:
        print(f"Minimum Latency : {graphLat[lat]} seconds")
        del graphLat[lat]
        break
# print OPtimal Path
for flight_no, path in optimal_paths.items():
    print(f"Flight No: {flight_no}, Optimal path:{path}")

print()


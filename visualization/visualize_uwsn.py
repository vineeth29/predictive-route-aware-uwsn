import csv
import os
import matplotlib.pyplot as plt
from matplotlib.animation import FuncAnimation

BASE_DIR = os.path.expanduser(
    "~/uwsn-project/ns-allinone-3.41/ns-3.41"
)

ROUTE_FILES = {
    "A": os.path.join(BASE_DIR, "route-A-events.csv"),
    "B": os.path.join(BASE_DIR, "route-B-events.csv"),
}

CSV_FILES = {
    "A": os.path.join(BASE_DIR, "two-route-A-aloha.csv"),
    "B": os.path.join(BASE_DIR, "two-route-B-aloha.csv"),
}

POSITIONS = {
    0: (0, 0, -50),
    1: (250, 50, -150),
    2: (500, -50, -250),
    3: (750, 80, -350),
    4: (1000, -80, -450),
    5: (1250, 50, -550),
    6: (1500, -50, -650),
    7: (1750, 0, -750),
}

ROUTES = {
    "A": [0, 1, 2, 3, 4, 5, 6, 7],
    "B": [0, 4, 5, 7],
}


def load_events(filename):

    events = []

    with open(filename, "r") as f:

        reader = csv.DictReader(f)

        for row in reader:

            packet_text = row.get("packet", "").strip()

            packet = None

            if packet_text:
                try:
                    packet = int(packet_text)
                except ValueError:
                    pass

            noise_text = row.get("noise", "").strip()

            noise = 0.0

            if noise_text:
                try:
                    noise = float(noise_text)
                except ValueError:
                    pass

            events.append({
                "time": float(row["time"]),
                "event": row["event"].strip().upper(),
                "node": int(row["node"]),
                "packet": packet,
                "noise": noise,
            })

    events.sort(key=lambda x: x["time"])

    return events


def load_results(route):

    filename = CSV_FILES[route]

    result = {
        "tx": 0,
        "rx": 0,
        "phy_tx": 0,
        "phy_rx": 0,
        "collisions": 0,
        "pdr": 0,
        "loss": 0,
        "throughput": 0,
        "delay": 0,
        "queue": 0,
    }

    with open(filename, "r") as f:

        reader = csv.DictReader(f)
        row = next(reader)

        result["tx"] = int(float(row["txPackets"]))
        result["rx"] = int(float(row["rxPackets"]))
        result["phy_tx"] = int(float(row["phyTx"]))
        result["phy_rx"] = int(float(row["phyRx"]))
        result["collisions"] = int(float(row["collisions"]))
        result["pdr"] = float(row["pdr"])
        result["loss"] = float(row["packetLoss"])
        result["throughput"] = float(row["throughputKbps"])
        result["delay"] = float(row["averageDelayMs"])
        result["queue"] = float(row["averageQueue"])

    return result


def draw_nodes(ax):

    for node, pos in POSITIONS.items():

        x, y, z = pos

        if node == 0:
            marker = "^"
            size = 180

        elif node == 7:
            marker = "s"
            size = 180

        else:
            marker = "o"
            size = 100

        ax.scatter(
            x,
            y,
            z,
            marker=marker,
            s=size,
            color="white",
            edgecolors="black",
            linewidths=1.5,
        )

        label = "N" + str(node)

        if node == 0:
            label += " SOURCE"

        if node == 7:
            label += " SINK"

        ax.text(
            x,
            y,
            z + 45,
            label,
            fontsize=9,
            fontweight="bold",
        )


def draw_route(ax, route):

    for i in range(len(route) - 1):

        a = route[i]
        b = route[i + 1]

        x1, y1, z1 = POSITIONS[a]
        x2, y2, z2 = POSITIONS[b]

        ax.plot(
            [x1, x2],
            [y1, y2],
            [z1, z2],
            linewidth=3,
            color="black",
            alpha=0.6,
        )


def set_scatter(scatter, points):

    if points:

        scatter._offsets3d = (
            [p[0] for p in points],
            [p[1] for p in points],
            [p[2] for p in points],
        )

    else:

        scatter._offsets3d = (
            [],
            [],
            [],
        )


def visualize(route_name):

    event_file = ROUTE_FILES[route_name]

    if not os.path.exists(event_file):

        print("ERROR: Event file not found:")
        print(event_file)
        return

    events = load_events(event_file)
    results = load_results(route_name)

    if not events:

        print("ERROR: No events found.")
        return

    route = ROUTES[route_name]

    fig = plt.figure(figsize=(16, 9))

    ax = fig.add_subplot(
        111,
        projection="3d",
    )

    ax.set_xlim(-150, 1900)
    ax.set_ylim(-450, 450)
    ax.set_zlim(-850, 100)

    ax.set_xlabel("X position (m)")
    ax.set_ylabel("Y position (m)")
    ax.set_zlabel("Depth (m)")

    ax.set_title(
        "UWSN 3D ROUTE " + route_name + " - EVENT REPLAY",
        fontsize=15,
        fontweight="bold",
    )

    draw_nodes(ax)
    draw_route(ax, route)

    tx_scatter = ax.scatter(
        [],
        [],
        [],
        marker="*",
        s=220,
        color="blue",
        label="TX",
    )

    rx_scatter = ax.scatter(
        [],
        [],
        [],
        marker="o",
        s=130,
        color="green",
        label="PHY RX",
    )

    collision_scatter = ax.scatter(
        [],
        [],
        [],
        marker="X",
        s=220,
        color="orange",
        label="COLLISION",
    )

    loss_scatter = ax.scatter(
        [],
        [],
        [],
        marker="x",
        s=220,
        color="red",
        linewidths=3,
        label="LOSS",
    )

    ax.legend(
        loc="upper right",
    )

    info = ax.text2D(
        0.02,
        0.95,
        "",
        transform=ax.transAxes,
        fontsize=10,
        verticalalignment="top",
        bbox=dict(
            boxstyle="round",
            facecolor="white",
            alpha=0.9,
        ),
    )

    results_text = ax.text2D(
        0.70,
        0.72,
        "",
        transform=ax.transAxes,
        fontsize=10,
        verticalalignment="top",
        bbox=dict(
            boxstyle="round",
            facecolor="white",
            alpha=0.9,
        ),
    )

    def update(frame):

        current_time = events[frame]["time"]

        active = [
            e for e in events
            if e["time"] <= current_time
        ]

        tx = [
            e for e in active
            if e["event"] == "TX"
        ]

        rx = [
            e for e in active
            if e["event"] == "RX"
        ]

        collisions = [
            e for e in active
            if e["event"] == "COLLISION"
        ]

        tx_packets = {
            e["packet"]
            for e in tx
            if e["packet"] is not None
        }

        rx_packets = {
            e["packet"]
            for e in rx
            if e["packet"] is not None
        }

        lost_packets = tx_packets - rx_packets

        loss_events = [
            e for e in tx
            if e["packet"] in lost_packets
        ]

        tx_xyz = [
            POSITIONS[e["node"]]
            for e in tx
            if e["node"] in POSITIONS
        ]

        rx_xyz = [
            POSITIONS[e["node"]]
            for e in rx
            if e["node"] in POSITIONS
        ]

        collision_xyz = [
            POSITIONS[e["node"]]
            for e in collisions
            if e["node"] in POSITIONS
        ]

        loss_xyz = [
            POSITIONS[e["node"]]
            for e in loss_events
            if e["node"] in POSITIONS
        ]

        set_scatter(tx_scatter, tx_xyz)
        set_scatter(rx_scatter, rx_xyz)
        set_scatter(collision_scatter, collision_xyz)
        set_scatter(loss_scatter, loss_xyz)

        current = events[frame]

        info.set_text(
            "ROUTE " + route_name + "\n"
            "────────────────────\n"
            "Time       : " + f"{current_time:.3f}" + " s\n"
            "Event      : " + current["event"] + "\n"
            "Node       : N" + str(current["node"]) + "\n"
            "Packet UID : " + str(current["packet"]) + "\n\n"
            "TX events  : " + str(len(tx)) + "\n"
            "PHY RX     : " + str(len(rx)) + "\n"
            "Collisions : " + str(len(collisions)) + "\n"
            "Loss est.  : " + str(len(lost_packets))
        )

        results_text.set_text(
            "FINAL SIMULATION RESULTS\n"
            "────────────────────────\n"
            "Application TX : " + str(results["tx"]) + "\n"
            "Application RX : " + str(results["rx"]) + "\n"
            "PHY TX         : " + str(results["phy_tx"]) + "\n"
            "PHY RX         : " + str(results["phy_rx"]) + "\n"
            "Collisions     : " + str(results["collisions"]) + "\n"
            "PDR            : " + f"{results['pdr']:.2f}" + "%\n"
            "Packet Loss    : " + f"{results['loss']:.2f}" + "%\n"
            "Throughput     : " + f"{results['throughput']:.3f}" + " kbps\n"
            "Avg Delay      : " + f"{results['delay']:.2f}" + " ms\n"
            "Avg Queue      : " + f"{results['queue']:.3f}"
        )

        return (
            tx_scatter,
            rx_scatter,
            collision_scatter,
            loss_scatter,
            info,
            results_text,
        )

    animation = FuncAnimation(
        fig,
        update,
        frames=len(events),
        interval=100,
        repeat=True,
    )

    plt.show()


if __name__ == "__main__":

    print()
    print("======================================")
    print("       UWSN 3D EVENT VISUALIZER")
    print("======================================")
    print()
    print("1. Route A")
    print("2. Route B")
    print()

    choice = input(
        "Select route (A/B): "
    ).strip().upper()

    if choice not in ("A", "B"):

        print("Invalid route.")

    else:

        visualize(choice)

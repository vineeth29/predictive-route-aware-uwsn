import csv
import os
import numpy as np
import matplotlib.pyplot as plt
from matplotlib.animation import FuncAnimation

# ============================================================
# UWSN 3D EVENT VISUALIZER
# ============================================================

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

ROUTE_A = [0, 1, 2, 3, 4, 5, 6, 7]
ROUTE_B = [0, 4, 5, 7]


# ============================================================
# LOAD EVENT FILE
# ============================================================

def load_events(filename):

    events = []

    with open(filename, "r") as f:

        reader = csv.DictReader(f)

        for row in reader:

            packet_text = row.get("packet", "").strip()

            try:
                packet = int(packet_text) if packet_text else None
            except ValueError:
                packet = None

            try:
                noise = float(row.get("noise", 0) or 0)
            except ValueError:
                noise = 0.0

            events.append({
                "time": float(row["time"]),
                "event": row["event"].strip().upper(),
                "node": int(row["node"]),
                "packet": packet,
                "noise": noise
            })

    events.sort(key=lambda x: x["time"])

    return events


# ============================================================
# LOAD CSV RESULTS
# ============================================================

def load_results(route):

    result = {
        "txPackets": 0,
        "rxPackets": 0,
        "phyTx": 0,
        "phyRx": 0,
        "collisions": 0,
        "pdr": 0.0,
        "packetLoss": 0.0,
        "throughput": 0.0,
        "delay": 0.0,
        "queue": 0.0
    }

    filename = CSV_FILES[route]

    if not os.path.exists(filename):
        return result

    with open(filename, "r") as f:

        reader = csv.DictReader(f)
        row = next(reader, None)

        if row is None:
            return result

        result["txPackets"] = int(float(row["txPackets"]))
        result["rxPackets"] = int(float(row["rxPackets"]))
        result["phyTx"] = int(float(row["phyTx"]))
        result["phyRx"] = int(float(row["phyRx"]))
        result["collisions"] = int(float(row["collisions"]))
        result["pdr"] = float(row["pdr"])
        result["packetLoss"] = float(row["packetLoss"])
        result["throughput"] = float(row["throughputKbps"])
        result["delay"] = float(row["averageDelayMs"])
        result["queue"] = float(row["averageQueue"])

    return result


# ============================================================
# ROUTE
# ============================================================

def route_edges(route):

    return list(zip(route[:-1], route[1:]))


# ============================================================
# NODE DRAWING
# ============================================================

def draw_nodes(ax):

    for node, position in POSITIONS.items():

        x, y, z = position

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
            depthshade=True
        )

        label = f"N{node}"

        if node == 0:
            label += " SOURCE"

        elif node == 7:
            label += " SINK"

        ax.text(
            x,
            y,
            z + 45,
            label,
            fontsize=9,
            fontweight="bold"
        )


# ============================================================
# ROUTE DRAWING
# ============================================================

def draw_route(ax, route):

    for a, b in route_edges(route):

        x1, y1, z1 = POSITIONS[a]
        x2, y2, z2 = POSITIONS[b]

        ax.plot(
            [x1, x2],
            [y1, y2],
            [z1, z2],
            linewidth=3,
            color="black",
            alpha=0.55
        )


# ============================================================
# VISUALIZATION
# ============================================================

def visualize(route_name):

    events = load_events(
        ROUTE_FILES[route_name]
    )

    results = load_results(route_name)

    if not events:

        print("ERROR: No events found.")

        return

    route = (
        ROUTE_A
        if route_name == "A"
        else ROUTE_B
    )

    fig = plt.figure(
        figsize=(16, 9)
    )

    ax = fig.add_subplot(
        111,
        projection="3d"
    )

    # --------------------------------------------------------
    # Environment
    # --------------------------------------------------------

    ax.set_xlim(-150, 1900)
    ax.set_ylim(-450, 450)
    ax.set_zlim(-850, 100)

    ax.set_xlabel("X position (m)")
    ax.set_ylabel("Y position (m)")
    ax.set_zlabel("Depth (m)")

    ax.set_title(
        f"UWSN 3D ROUTE {route_name} — LIVE EVENT REPLAY",
        fontsize=15,
        fontweight="bold"
    )

    draw_nodes(ax)
    draw_route(ax, route)

    # --------------------------------------------------------
    # Event markers
    # --------------------------------------------------------

    tx_scatter = ax.scatter(
        [],
        [],
        [],
        marker="*",
        s=220,
        color="blue",
        label="TX"
    )

    rx_scatter = ax.scatter(
        [],
        [],
        [],
        marker="o",
        s=130,
        color="green",
        label="PHY RX"
    )

    collision_scatter = ax.scatter(
        [],
        [],
        [],
        marker="X",
        s=220,
        color="orange",
        label="COLLISION"
    )

    loss_scatter = ax.scatter(
        [],
        [],
        [],
        marker="x",
        s=220,
        color="red",
        linewidths=3,
        label="PACKET LOSS"
    )

    # --------------------------------------------------------
    # Information panels
    # --------------------------------------------------------

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
            alpha=0.88
        )
    )

    legend_text = ax.text2D(
        0.73,
        0.95,
        "",
        transform=ax.transAxes,
        fontsize=10,
        verticalalignment="top",
        bbox=dict(
            boxstyle="round",
            facecolor="white",
            alpha=0.88
        )
    )

    # --------------------------------------------------------
    # Animation
    # --------------------------------------------------------

    def update(frame):

        current_time = events[frame]["time"]

        active = [
            e
            for e in events
            if e["time"] <= current_time
        ]

        tx = [
            e
            for e in active
            if e["event"] == "TX"
        ]

        rx = [
            e
            for e in active
            if e["event"] == "RX"
        ]

        collisions = [
            e
            for e in active
            if e["event"] == "COLLISION"
        ]

        # ----------------------------------------------------
        # Estimate lost packets from TX/RX event information
        #
        # IMPORTANT:
        # This is an event-level visualization estimate,
        # not the final scientific PDR metric.
        # ----------------------------------------------------

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

        # ----------------------------------------------------
        # TX
        # ----------------------------------------------------

        tx_xyz = [
            POSITIONS[e["node"]]
            for e in tx
            if e["node"] in POSITIONS
        ]

        if tx_xyz:

            tx_scatter._offsets3d = (
                [p[0] for p in tx_xyz],
                [p[1] for p in tx_xyz],
                [p[2] for p in tx_xyz]
            )

        else:

            tx_scatter._offsets3d = (
                [],
                [],
                []
            )

        # ----------------------------------------------------
        # RX
        # ----------------------------------------------------

        rx_xyz = [
            POSITIONS[e["node"]]
            for e in rx
            if e["node"] in POSITIONS
        ]

        if rx_xyz:

            rx_scatter._offsets3d = (
                [p[0] for p in rx_xyz],
                [p[1] for p in rx_xyz],
                [p[2] for p in rx_xyz]
            )

        else:

            rx_scatter._offsets3d = (
                [],
                [],
                []
            )

        # ----------------------------------------------------
        # COLLISIONS
        # ----------------------------------------------------

        collision_xyz = [
            POSITIONS[e["node"]]
            for e in collisions
            if e["node"] in POSITIONS
        ]

        if collision_xyz:

            collision_scatter._offsets3d = (
                [p[0] for p in collision_xyz],
                [p[1] for p in collision_xyz],
                [p[2] for p in collision_xyz]
            )

        else:

            collision_scatter._offsets3d = (
                [],
                [],
                []
            )

        # ----------------------------------------------------
        # PACKET LOSS
        # ----------------------------------------------------

        loss_events = [
            e
            for e in active
            if (
                e["event"] == "TX"
                and e["packet"] in lost_packets
            )
        ]

        loss_xyz = [
            POSITIONS[e["node"]]
            for e in loss_events
            if e["node"] in POSITIONS
        ]

        if loss_xyz:

            loss_scatter._offsets3d = (
                [p[0] for p in loss_xyz],
                [p[1] for p in loss_xyz],
                [p[2] for p in loss_xyz
            )

        else:

            loss_scatter._offsets3d = (
                [],
                [],
                []
            )

        # ----------------------------------------------------
        # Current event
        # ----------------------------------------------------

        current = events[frame]

        # ----------------------------------------------------
        # Statistics
        # ----------------------------------------------------

        info.set_text(
            f"ROUTE {route_name}\n"
            f"────────────────────────\n"
            f"Time       : {current_time:7.3f} s\n"
            f"Current    : {current['event']}\n"
            f"Node       : N{current['node']}\n"
            f"Packet UID : {current['packet']}\n"
            f"\n"
            f"TX events  : {len(tx):7d}\n"
            f"PHY RX     : {len(rx):7d}\n"
            f"Collisions : {len(collisions):7d}\n"
            f"Lost est.  : {len(lost_packets):7d}"
        )

        legend_text.set_text(
            "SIMULATION RESULTS\n"
            "────────────────────\n"
            f"Application TX : {results['txPackets']}\n"
            f"PHY TX         : {results['phyTx']}\n"
            f"PHY RX         : {results['phyRx']}\n"
            f"Collisions     : {results['collisions']}\n"
            f"PDR            : {results['pdr']:.2f}%\n"
            f"Packet Loss    : {results['packetLoss']:.2f}%\n"
            f"Throughput     : {results['throughput']:.3f} kbps\n"
            f"Avg Delay      : {results['delay']:.2f} ms\n"
            f"Avg Queue      : {results['queue']:.3f}\n"
            "\n"
            "BLUE  = TX\n"
            "GREEN = PHY RX\n"
            "ORANGE = COLLISION\n"
            "RED = LOSS ESTIMATE"
        )

        return (
            tx_scatter,
            rx_scatter,
            collision_scatter,
            loss_scatter,
            info,
            legend_text
        )

    animation = FuncAnimation(
        fig,
        update,
        frames=len(events),
        interval=100,
        repeat=True
    )

    plt.show()


# ============================================================
# MAIN
# ============================================================

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

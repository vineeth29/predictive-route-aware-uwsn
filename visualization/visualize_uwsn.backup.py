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

# ------------------------------------------------------------
# 3D node positions
# ------------------------------------------------------------

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


def load_events(filename):
    events = []

    with open(filename, "r") as f:
        reader = csv.DictReader(f)

        for row in reader:
            events.append({
                "time": float(row["time"]),
                "event": row["event"],
                "node": int(row["node"]),
                "packet": (
                    int(row["packet"])
                    if row["packet"].strip()
                    else None
                ),
                "noise": float(row["noise"]) if row["noise"].strip() else 0.0,
            })

    events.sort(key=lambda x: x["time"])

    return events


def route_edges(route):
    return list(zip(route[:-1], route[1:]))


def draw_nodes(ax):
    for node, position in POSITIONS.items():

        x, y, z = position

        if node == 0:
            marker = "^"
            size = 120
        elif node == 7:
            marker = "s"
            size = 120
        else:
            marker = "o"
            size = 70

        ax.scatter(
            x,
            y,
            z,
            marker=marker,
            s=size
        )

        ax.text(
            x,
            y,
            z + 35,
            f"N{node}",
            fontsize=10
        )


def draw_route(ax, route):
    for a, b in route_edges(route):

        x1, y1, z1 = POSITIONS[a]
        x2, y2, z2 = POSITIONS[b]

        ax.plot(
            [x1, x2],
            [y1, y2],
            [z1, z2],
            linewidth=2
        )


def visualize(route_name):

    events = load_events(
        ROUTE_FILES[route_name]
    )

    if route_name == "A":
        route = ROUTE_A
    else:
        route = ROUTE_B

    fig = plt.figure(
        figsize=(13, 8)
    )

    ax = fig.add_subplot(
        111,
        projection="3d"
    )

    # --------------------------------------------------------
    # Underwater environment
    # --------------------------------------------------------

    ax.set_xlim(-100, 1900)
    ax.set_ylim(-400, 400)
    ax.set_zlim(-850, 100)

    ax.set_xlabel("X position (m)")
    ax.set_ylabel("Y position (m)")
    ax.set_zlabel("Depth (m)")

    ax.set_title(
        f"UWSN Route {route_name} — PHY Event Visualization"
    )

    # --------------------------------------------------------
    # Draw nodes and selected route
    # --------------------------------------------------------

    draw_nodes(ax)
    draw_route(ax, route)

    # --------------------------------------------------------
    # Event objects
    # --------------------------------------------------------

    tx_scatter = ax.scatter(
        [],
        [],
        [],
        marker="*",
        s=160
    )

    rx_scatter = ax.scatter(
        [],
        [],
        [],
        marker="o",
        s=90
    )

    collision_scatter = ax.scatter(
        [],
        [],
        [],
        marker="x",
        s=120
    )

    info = ax.text2D(
        0.02,
        0.95,
        "",
        transform=ax.transAxes
    )

    # --------------------------------------------------------
    # Animation state
    # --------------------------------------------------------

    displayed = []

    def update(frame):

        current_time = (
            events[frame]["time"]
        )

        # Show events up to current time
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
        # Statistics
        # ----------------------------------------------------

        info.set_text(
            f"Route {route_name}\n"
            f"Simulation time: {current_time:.3f} s\n"
            f"Packet UID: {events[frame]['packet']}\n"
            f"Current event: {events[frame]['event']}\n"
            f"TX events: {len(tx)}\n"
            f"RX events: {len(rx)}\n"
            f"Collisions: {len(collisions)}"
        )

        return (
            tx_scatter,
            rx_scatter,
            collision_scatter,
            info
        )

    animation = FuncAnimation(
        fig,
        update,
        frames=len(events),
        interval=100,
        repeat=True
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

    if choice not in ROUTE_FILES:
        print("Invalid route.")
        raise SystemExit(1)

    visualize(choice)

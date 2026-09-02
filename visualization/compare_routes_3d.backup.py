import csv
import os
import numpy as np
import matplotlib.pyplot as plt
from matplotlib.animation import FuncAnimation

BASE_DIR = os.path.expanduser(
    "~/uwsn-project/ns-allinone-3.41/ns-3.41"
)

FILE_A = os.path.join(BASE_DIR, "route-A-events.csv")
FILE_B = os.path.join(BASE_DIR, "route-B-events.csv")

# ============================================================
# 3D NODE POSITIONS
# ============================================================

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
# LOAD EVENTS
# ============================================================

def load_events(filename):

    events = []

    with open(filename, "r") as f:

        reader = csv.DictReader(f)

        for row in reader:

            packet_text = row["packet"].strip()

            if packet_text:
                packet = int(packet_text)
            else:
                packet = None

            noise_text = row["noise"].strip()

            if noise_text:
                noise = float(noise_text)
            else:
                noise = 0.0

            events.append({
                "time": float(row["time"]),
                "event": row["event"].strip(),
                "node": int(row["node"]),
                "packet": packet,
                "noise": noise,
            })

    events.sort(key=lambda x: x["time"])

    return events


# ============================================================
# ROUTE DRAWING
# ============================================================

def draw_route(ax, route, linewidth=3):

    for a, b in zip(route[:-1], route[1:]):

        x1, y1, z1 = POSITIONS[a]
        x2, y2, z2 = POSITIONS[b]

        ax.plot(
            [x1, x2],
            [y1, y2],
            [z1, z2],
            linewidth=linewidth
        )


# ============================================================
# NODE DRAWING
# ============================================================

def draw_nodes(ax):

    for node, (x, y, z) in POSITIONS.items():

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
            s=size
        )

        label = "SOURCE" if node == 0 else (
            "SINK" if node == 7 else ""
        )

        ax.text(
            x,
            y,
            z + 50,
            f"N{node} {label}",
            fontsize=9
        )


# ============================================================
# MAIN VISUALIZATION
# ============================================================

def visualize():

    events_a = load_events(FILE_A)
    events_b = load_events(FILE_B)

    all_times = (
        [e["time"] for e in events_a]
        + [e["time"] for e in events_b]
    )

    max_time = max(all_times)

    frame_count = max(
        len(events_a),
        len(events_b)
    )

    fig = plt.figure(
        figsize=(15, 9)
    )

    ax = fig.add_subplot(
        111,
        projection="3d"
    )

    ax.set_xlim(-150, 1900)
    ax.set_ylim(-400, 400)
    ax.set_zlim(-850, 100)

    ax.set_xlabel("X position (m)")
    ax.set_ylabel("Y position (m)")
    ax.set_zlabel("Depth (m)")

    ax.set_title(
        "UWSN 3D Route Comparison — NS-3.41 + Aqua-Sim NG"
    )

    # --------------------------------------------------------
    # Nodes
    # --------------------------------------------------------

    draw_nodes(ax)

    # --------------------------------------------------------
    # Both candidate routes
    # --------------------------------------------------------

    draw_route(
        ax,
        ROUTE_A,
        linewidth=3
    )

    draw_route(
        ax,
        ROUTE_B,
        linewidth=5
    )

    # --------------------------------------------------------
    # Event markers
    # --------------------------------------------------------

    tx_a = ax.scatter(
        [], [], [],
        marker="*",
        s=160
    )

    rx_a = ax.scatter(
        [], [], [],
        marker="o",
        s=80
    )

    collision_a = ax.scatter(
        [], [], [],
        marker="x",
        s=120
    )

    tx_b = ax.scatter(
        [], [], [],
        marker="*",
        s=160
    )

    rx_b = ax.scatter(
        [], [], [],
        marker="o",
        s=80
    )

    collision_b = ax.scatter(
        [], [], [],
        marker="x",
        s=120
    )

    # --------------------------------------------------------
    # Information panel
    # --------------------------------------------------------

    info = ax.text2D(
        0.02,
        0.96,
        "",
        transform=ax.transAxes,
        verticalalignment="top",
        fontsize=10
    )

    # --------------------------------------------------------
    # Update animation
    # --------------------------------------------------------

    def update(frame):

        if frame < len(events_a):

            time_a = events_a[frame]["time"]

        else:

            time_a = max_time

        if frame < len(events_b):

            time_b = events_b[frame]["time"]

        else:

            time_b = max_time

        current_time = max(
            time_a,
            time_b
        )

        # ----------------------------------------------------
        # Route A events up to current time
        # ----------------------------------------------------

        active_a = [
            e for e in events_a
            if e["time"] <= current_time
        ]

        tx_events_a = [
            e for e in active_a
            if e["event"] == "TX"
        ]

        rx_events_a = [
            e for e in active_a
            if e["event"] == "RX"
        ]

        collision_events_a = [
            e for e in active_a
            if e["event"] == "COLLISION"
        ]

        # ----------------------------------------------------
        # Route B events
        # ----------------------------------------------------

        active_b = [
            e for e in events_b
            if e["time"] <= current_time
        ]

        tx_events_b = [
            e for e in active_b
            if e["event"] == "TX"
        ]

        rx_events_b = [
            e for e in active_b
            if e["event"] == "RX"
        ]

        collision_events_b = [
            e for e in active_b
            if e["event"] == "COLLISION"
        ]

        # ----------------------------------------------------
        # Helper
        # ----------------------------------------------------

        def coordinates(events):

            points = [
                POSITIONS[e["node"]]
                for e in events
                if e["node"] in POSITIONS
            ]

            if not points:

                return [], [], []

            return (
                [p[0] for p in points],
                [p[1] for p in points],
                [p[2] for p in points]
            )

        # ----------------------------------------------------
        # Route A
        # ----------------------------------------------------

        x, y, z = coordinates(tx_events_a)

        tx_a._offsets3d = (x, y, z)

        x, y, z = coordinates(rx_events_a)

        rx_a._offsets3d = (x, y, z)

        x, y, z = coordinates(collision_events_a)

        collision_a._offsets3d = (x, y, z)

        # ----------------------------------------------------
        # Route B
        # ----------------------------------------------------

        x, y, z = coordinates(tx_events_b)

        tx_b._offsets3d = (x, y, z)

        x, y, z = coordinates(rx_events_b)

        rx_b._offsets3d = (x, y, z)

        x, y, z = coordinates(collision_events_b)

        collision_b._offsets3d = (x, y, z)

        # ----------------------------------------------------
        # Statistics
        # ----------------------------------------------------

        info.set_text(
            "UWSN TWO-ROUTE BASELINE\n"
            f"Simulation time: {current_time:.3f} s\n\n"
            "ROUTE A: N0 → N1 → N2 → N3 → N4 → N5 → N6 → N7\n"
            f"TX: {len(tx_events_a)}   "
            f"RX: {len(rx_events_a)}   "
            f"Collisions: {len(collision_events_a)}\n\n"
            "ROUTE B: N0 → N4 → N5 → N7\n"
            f"TX: {len(tx_events_b)}   "
            f"RX: {len(rx_events_b)}   "
            f"Collisions: {len(collision_events_b)}"
        )

        return (
            tx_a,
            rx_a,
            collision_a,
            tx_b,
            rx_b,
            collision_b,
            info
        )

    animation = FuncAnimation(
        fig,
        update,
        frames=frame_count,
        interval=80,
        repeat=True
    )

    plt.show()


# ============================================================
# START
# ============================================================

if __name__ == "__main__":

    print()
    print("============================================")
    print("       UWSN 3D ROUTE COMPARISON")
    print("============================================")
    print()
    print("Route A and Route B will be shown together.")
    print()

    visualize()

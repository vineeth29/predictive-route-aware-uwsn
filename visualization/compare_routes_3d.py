import csv
import os
import matplotlib.pyplot as plt
from matplotlib.animation import FuncAnimation

BASE_DIR = os.path.expanduser(
    "~/uwsn-project/ns-allinone-3.41/ns-3.41"
)

EVENT_FILES = {
    "A": os.path.join(BASE_DIR, "route-A-events.csv"),
    "B": os.path.join(BASE_DIR, "route-B-events.csv"),
}

RESULT_FILES = {
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

            events.append({
                "time": float(row["time"]),
                "event": row["event"].strip().upper(),
                "node": int(row["node"]),
                "packet": packet,
            })

    events.sort(key=lambda x: x["time"])

    return events


def load_results(route):

    with open(RESULT_FILES[route], "r") as f:

        row = next(csv.DictReader(f))

    return {
        "tx": int(float(row["txPackets"])),
        "rx": int(float(row["rxPackets"])),
        "phy_tx": int(float(row["phyTx"])),
        "phy_rx": int(float(row["phyRx"])),
        "collisions": int(float(row["collisions"])),
        "pdr": float(row["pdr"]),
        "loss": float(row["packetLoss"]),
        "throughput": float(row["throughputKbps"]),
        "delay": float(row["averageDelayMs"]),
        "queue": float(row["averageQueue"]),
    }


def set_points(scatter, points):

    if points:

        scatter._offsets3d = (
            [p[0] for p in points],
            [p[1] for p in points],
            [p[2] for p in points],
        )

    else:

        scatter._offsets3d = ([], [], [])


def draw_network(ax, route, title):

    for node, (x, y, z) in POSITIONS.items():

        if node == 0:
            marker = "^"
            size = 180

        elif node == 7:
            marker = "s"
            size = 180

        else:
            marker = "o"
            size = 90

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

        elif node == 7:
            label += " SINK"

        ax.text(
            x,
            y,
            z + 45,
            label,
            fontsize=8,
            fontweight="bold",
        )

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
            alpha=0.65,
        )

    ax.set_xlim(-150, 1900)
    ax.set_ylim(-450, 450)
    ax.set_zlim(-850, 100)

    ax.set_xlabel("X (m)")
    ax.set_ylabel("Y (m)")
    ax.set_zlabel("Depth (m)")

    ax.set_title(
        title,
        fontsize=14,
        fontweight="bold",
    )


def main():

    events_a = load_events(EVENT_FILES["A"])
    events_b = load_events(EVENT_FILES["B"])

    results_a = load_results("A")
    results_b = load_results("B")

    max_frames = max(
        len(events_a),
        len(events_b),
    )

    fig = plt.figure(
        figsize=(18, 10)
    )

    ax_a = fig.add_subplot(
        131,
        projection="3d",
    )

    ax_middle = fig.add_subplot(
        132
    )

    ax_b = fig.add_subplot(
        133,
        projection="3d",
    )

    fig.suptitle(
        "UWSN TWO-ROUTE BASELINE COMPARISON",
        fontsize=18,
        fontweight="bold",
    )

    draw_network(
        ax_a,
        ROUTES["A"],
        "ROUTE A\n7 HOPS",
    )

    draw_network(
        ax_b,
        ROUTES["B"],
        "ROUTE B\n3 HOPS",
    )

    # --------------------------------------------------------
    # Event markers
    # --------------------------------------------------------

    tx_a = ax_a.scatter(
        [], [], [],
        marker="*",
        s=220,
        color="blue",
        label="TX",
    )

    rx_a = ax_a.scatter(
        [], [], [],
        marker="o",
        s=120,
        color="green",
        label="RX",
    )

    collision_a = ax_a.scatter(
        [], [], [],
        marker="X",
        s=200,
        color="orange",
        label="COLLISION",
    )

    tx_b = ax_b.scatter(
        [], [], [],
        marker="*",
        s=220,
        color="blue",
        label="TX",
    )

    rx_b = ax_b.scatter(
        [], [], [],
        marker="o",
        s=120,
        color="green",
        label="RX",
    )

    collision_b = ax_b.scatter(
        [], [], [],
        marker="X",
        s=200,
        color="orange",
        label="COLLISION",
    )

    ax_a.legend(
        loc="upper right",
        fontsize=8,
    )

    ax_b.legend(
        loc="upper right",
        fontsize=8,
    )

    # --------------------------------------------------------
    # Center comparison panel
    # --------------------------------------------------------

    ax_middle.axis("off")

    comparison_text = ax_middle.text(
        0.5,
        0.5,
        "",
        ha="center",
        va="center",
        fontsize=11,
        family="monospace",
    )

    # --------------------------------------------------------
    # Animation
    # --------------------------------------------------------

    def update(frame):

        if events_a:
            frame_a = min(frame, len(events_a) - 1)
            time_a = events_a[frame_a]["time"]
            active_a = [
                e for e in events_a
                if e["time"] <= time_a
            ]
        else:
            active_a = []
            time_a = 0

        if events_b:
            frame_b = min(frame, len(events_b) - 1)
            time_b = events_b[frame_b]["time"]
            active_b = [
                e for e in events_b
                if e["time"] <= time_b
            ]
        else:
            active_b = []
            time_b = 0

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

        set_points(
            tx_a,
            [
                POSITIONS[e["node"]]
                for e in tx_events_a
                if e["node"] in POSITIONS
            ],
        )

        set_points(
            rx_a,
            [
                POSITIONS[e["node"]]
                for e in rx_events_a
                if e["node"] in POSITIONS
            ],
        )

        set_points(
            collision_a,
            [
                POSITIONS[e["node"]]
                for e in collision_events_a
                if e["node"] in POSITIONS
            ],
        )

        set_points(
            tx_b,
            [
                POSITIONS[e["node"]]
                for e in tx_events_b
                if e["node"] in POSITIONS
            ],
        )

        set_points(
            rx_b,
            [
                POSITIONS[e["node"]]
                for e in rx_events_b
                if e["node"] in POSITIONS
            ],
        )

        set_points(
            collision_b,
            [
                POSITIONS[e["node"]]
                for e in collision_events_b
                if e["node"] in POSITIONS
            ],
        )

        # ----------------------------------------------------
        # Differences
        # ----------------------------------------------------

        collision_difference = (
            results_a["collisions"]
            - results_b["collisions"]
        )

        phy_tx_difference = (
            results_a["phy_tx"]
            - results_b["phy_tx"]
        )

        delay_difference = (
            results_b["delay"]
            - results_a["delay"]
        )

        queue_difference = (
            results_b["queue"]
            - results_a["queue"]
        )

        comparison_text.set_text(

            "ROUTE COMPARISON\n"
            "════════════════════════════\n\n"

            "                ROUTE A     ROUTE B\n"
            "HOPS              7           3\n\n"

            f"PHY TX          {results_a['phy_tx']:>5}       "
            f"{results_b['phy_tx']:>5}\n"

            f"PHY RX          {results_a['phy_rx']:>5}       "
            f"{results_b['phy_rx']:>5}\n\n"

            f"COLLISIONS      {results_a['collisions']:>5}       "
            f"{results_b['collisions']:>5}\n"

            f"PACKET LOSS     {results_a['loss']:>5.1f}%      "
            f"{results_b['loss']:>5.1f}%\n"

            f"PDR             {results_a['pdr']:>5.1f}%      "
            f"{results_b['pdr']:>5.1f}%\n\n"

            f"THROUGHPUT      {results_a['throughput']:>5.2f}       "
            f"{results_b['throughput']:>5.2f}\n"

            f"DELAY           {results_a['delay']:>5.1f} ms   "
            f"{results_b['delay']:>5.1f} ms\n"

            f"QUEUE           {results_a['queue']:>5.2f}       "
            f"{results_b['queue']:>5.2f}\n\n"

            "────────────────────────────\n"

            f"Collision Δ     {collision_difference:+d}\n"
            f"PHY TX Δ        {phy_tx_difference:+d}\n"
            f"Delay Δ         {delay_difference:+.1f} ms\n"
            f"Queue Δ         {queue_difference:+.2f}\n\n"

            "LIVE EVENT REPLAY\n"
            f"Route A time: {time_a:.2f} s\n"
            f"Route B time: {time_b:.2f} s"
        )

        return (
            tx_a,
            rx_a,
            collision_a,
            tx_b,
            rx_b,
            collision_b,
            comparison_text,
        )

    
    animation = FuncAnimation(
        fig,
        update,
        frames=max_frames,
        interval=100,
        repeat=True,
        blit=False,
    )

    # Keep a persistent reference to the animation.
    fig._uwsn_animation = animation

    plt.tight_layout(
        rect=[0, 0, 1, 0.95]
    )

    plt.show()


if __name__ == "__main__":
    main()

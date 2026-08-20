import csv
from pathlib import Path

import numpy as np
import matplotlib.pyplot as plt


PROJECT_ROOT = Path(__file__).resolve().parents[1]
RESULTS_DIR = PROJECT_ROOT / "results" / "raw"


def load_result(filename):
    path = RESULTS_DIR / filename

    with open(path, newline="") as f:
        row = next(csv.DictReader(f))

    return row


def make_nodes():
    """
    Deterministic 3D node positions for visualization.
    These are visualization positions only.
    Later we will replace them with positions recorded
    directly from the NS-3 simulation.
    """
    positions = np.array([
        [20, 20, -20],
        [80, 20, -35],
        [140, 40, -50],
        [40, 90, -70],
        [100, 100, -90],
        [170, 90, -60],
        [30, 160, -120],
        [100, 160, -100],
        [170, 150, -130],
        [220, 100, -80],
    ])

    sink = np.array([120, 70, 0])

    return positions, sink


def print_result(name, result):
    print()
    print("=" * 50)
    print(f"{name.upper()} BASELINE")
    print("=" * 50)

    print(f"Nodes:             {result['nodes']}")
    print(f"Simulation time:   {result['simStop']} s")
    print(f"TX packets:        {result['txPackets']}")
    print(f"RX packets:        {result['rxPackets']}")
    print(f"PHY TX:            {result['phyTx']}")
    print(f"PHY RX:            {result['phyRx']}")
    print(f"Collisions:        {result['collisions']}")
    print(f"PDR:               {float(result['pdr']):.3f}%")
    print(f"Throughput:        {float(result['throughputKbps']):.3f} kbps")
    print(f"Average delay:     {float(result['averageDelayMs']):.3f} ms")
    print(f"Average queue:     {float(result['averageQueue']):.3f}")


def draw_scene(result, mac_name):
    nodes, sink = make_nodes()

    fig = plt.figure(figsize=(14, 8))
    ax = fig.add_subplot(111, projection="3d")

    # Sensor nodes
    ax.scatter(
        nodes[:, 0],
        nodes[:, 1],
        nodes[:, 2],
        s=100,
        label="Underwater sensor nodes"
    )

    # Node labels
    for i, (x, y, z) in enumerate(nodes, start=1):
        ax.text(x, y, z, f" N{i}", fontsize=9)

    # Sink
    ax.scatter(
        sink[0],
        sink[1],
        sink[2],
        s=220,
        marker="*",
        label="Sink"
    )

    ax.text(
        sink[0],
        sink[1],
        sink[2],
        " SINK",
        fontsize=11
    )

    # Draw communication lines from nodes toward sink.
    # These are visualization links only at this stage.
    for node in nodes:
        ax.plot(
            [node[0], sink[0]],
            [node[1], sink[1]],
            [node[2], sink[2]],
            linewidth=0.7,
            alpha=0.25
        )

    ax.set_title(
        f"UWSN 3D Visualization — {mac_name.upper()} Baseline",
        fontsize=15
    )

    ax.set_xlabel("X position (m)")
    ax.set_ylabel("Y position (m)")
    ax.set_zlabel("Depth (m)")

    ax.set_xlim(0, 250)
    ax.set_ylim(0, 190)
    ax.set_zlim(-150, 10)

    ax.legend(loc="upper left")

    # Metrics panel
    metrics = (
        f"MAC: {mac_name.upper()}\n"
        f"Nodes: {result['nodes']}\n"
        f"Simulation: {result['simStop']} s\n\n"
        f"TX: {result['txPackets']}\n"
        f"RX: {result['rxPackets']}\n"
        f"Collisions: {result['collisions']}\n"
        f"PDR: {float(result['pdr']):.3f}%\n"
        f"Throughput: {float(result['throughputKbps']):.3f} kbps\n"
        f"Delay: {float(result['averageDelayMs']):.3f} ms\n"
        f"Queue: {float(result['averageQueue']):.3f}"
    )

    fig.text(
        0.02,
        0.02,
        metrics,
        fontsize=11,
        family="monospace"
    )

    plt.tight_layout()
    plt.show()


def main():
    aloha = load_result("baseline-aloha.csv")
    tdma = load_result("baseline-tdma.csv")

    print_result("ALOHA", aloha)
    print_result("TDMA", tdma)

    # Start with ALOHA visualization.
    draw_scene(aloha, "aloha")


if __name__ == "__main__":
    main()

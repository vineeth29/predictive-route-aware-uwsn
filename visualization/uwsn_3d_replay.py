import sys
import csv
import os
import math
from collections import defaultdict

import matplotlib.pyplot as plt
from matplotlib.animation import FuncAnimation
from matplotlib.lines import Line2D
from mpl_toolkits.mplot3d.art3d import Poly3DCollection


# ============================================================
# CONFIGURATION
# ============================================================

PROJECT_ROOT = os.path.abspath(
    os.path.join(os.path.dirname(__file__), "..")
)

EVENT_DIR = os.path.join(
    PROJECT_ROOT,
    "results",
    "visualization"
)

# ------------------------------------------------------------
# Visualization topology
#
# IMPORTANT:
# These coordinates are visualization coordinates.
# Later we will export the actual NS-3 node coordinates.
#
# Depth is negative because the water surface is z = 0.
# ------------------------------------------------------------

NODE_POSITIONS = {
    0: (40, 40, -20),
    1: (110, 90, -35),
    2: (180, 40, -50),
    3: (250, 110, -65),
    4: (330, 55, -80),
    5: (120, 180, -25),
    6: (220, 160, -45),
    7: (300, 190, -60),
    8: (390, 130, -30),
    9: (450, 70, -75),
}

SINK_POSITION = (250, 250, 0)

TRANSMISSION_RANGE = 150.0

PACKET_SIZE_BYTES = 50
DATA_RATE_BPS = 80000

PACKET_DURATION = (
    PACKET_SIZE_BYTES * 8
) / DATA_RATE_BPS


# ============================================================
# COLOUR DEFINITIONS
# ============================================================

COLOR_IDLE = "royalblue"
COLOR_TX = "gold"
COLOR_RX = "limegreen"
COLOR_COLLISION = "red"

COLOR_PACKET = "orange"
COLOR_SUCCESS = "green"

COLOR_TDMA = "purple"
COLOR_RANGE = "gray"

COLOR_WATER = "lightskyblue"
COLOR_TEXT = "black"


# ============================================================
# EVENT READER
# ============================================================

def load_events(mode):

    filename = os.path.join(
        EVENT_DIR,
        f"{mode}-events.csv"
    )

    if not os.path.exists(filename):

        raise FileNotFoundError(
            f"\nEvent file not found:\n{filename}\n\n"
            f"Run the NS-3 simulation first."
        )

    events = []

    with open(filename, "r") as file:

        reader = csv.DictReader(file)

        for row in reader:

            try:

                event = {
                    "time": float(row["time"]),
                    "event": row["event"].strip(),
                    "node": int(row["node"]),
                    "packet": (
                        int(row["packet"])
                        if row["packet"] != ""
                        else None
                    ),
                    "noise": float(row["noise"])
                    if row["noise"] != ""
                    else 0.0,
                }

                events.append(event)

            except (ValueError, KeyError):

                continue

    events.sort(
        key=lambda e: e["time"]
    )

    return events


# ============================================================
# REPLAY CLASS
# ============================================================

class UWSNReplay:

    def __init__(self, mode):

        self.mode = mode.lower()

        if self.mode not in ("aloha", "tdma"):

            raise ValueError(
                "Mode must be 'aloha' or 'tdma'."
            )

        self.events = load_events(self.mode)

        if not self.events:

            raise RuntimeError(
                "No events found in event file."
            )

        self.index = 0

        self.playing = True

        self.speed = 1.0

        self.current_time = 0.0

        self.max_time = self.events[-1]["time"]

        # ----------------------------------------
        # Statistics
        # ----------------------------------------

        self.tx_count = 0
        self.rx_count = 0
        self.collision_count = 0

        self.current_tx_nodes = set()
        self.current_rx_nodes = set()
        self.current_collision_nodes = set()

        # ----------------------------------------
        # Packet history
        # ----------------------------------------

        self.packet_sources = {}

        self.successful_links = []

        # ----------------------------------------
        # Matplotlib
        # ----------------------------------------

        self.fig = plt.figure(
            figsize=(16, 9)
        )

        self.ax = self.fig.add_subplot(
            111,
            projection="3d"
        )

        self.setup_scene()

        self.update_scene()

        self.fig.canvas.mpl_connect(
            "key_press_event",
            self.on_key
        )

        self.animation = FuncAnimation(
            self.fig,
            self.animation_step,
            interval=50,
            cache_frame_data=False
        )

    # ========================================================
    # SCENE
    # ========================================================

    def setup_scene(self):

        self.ax.set_title(
            "UNDERWATER MAC PROTOCOL 3D REPLAY",
            fontsize=18,
            fontweight="bold",
            pad=20
        )

        self.ax.set_xlabel(
            "X position (m)",
            labelpad=10
        )

        self.ax.set_ylabel(
            "Y position (m)",
            labelpad=10
        )

        self.ax.set_zlabel(
            "Depth (m)",
            labelpad=10
        )

        self.ax.set_xlim(
            0,
            500
        )

        self.ax.set_ylim(
            0,
            320
        )

        self.ax.set_zlim(
            -110,
            10
        )

        self.ax.view_init(
            elev=25,
            azim=-60
        )

        self.ax.grid(
            True,
            alpha=0.25
        )

        # ----------------------------------------------------
        # Water surface
        # ----------------------------------------------------

        x = [0, 500, 500, 0]
        y = [0, 0, 320, 320]
        z = [0, 0, 0, 0]

        vertices = [
            list(zip(x, y, z))
        ]

        water_surface = Poly3DCollection(
            vertices,
            alpha=0.08,
            facecolor=COLOR_WATER
        )

        self.ax.add_collection3d(
            water_surface
        )

        # ----------------------------------------------------
        # Sink
        # ----------------------------------------------------

        sx, sy, sz = SINK_POSITION

        self.ax.scatter(
            sx,
            sy,
            sz,
            s=250,
            marker="*",
            color="darkorange",
            edgecolors="black",
            linewidths=1.5,
            depthshade=False
        )

        self.ax.text(
            sx + 8,
            sy,
            sz + 5,
            "SINK",
            fontsize=10,
            fontweight="bold"
        )

        # ----------------------------------------------------
        # Node artists
        # ----------------------------------------------------

        self.node_artists = {}

        for node_id, pos in NODE_POSITIONS.items():

            x, y, z = pos

            artist = self.ax.scatter(
                x,
                y,
                z,
                s=130,
                marker="o",
                color=COLOR_IDLE,
                edgecolors="black",
                linewidths=1.2,
                depthshade=True
            )

            self.node_artists[node_id] = artist

            self.ax.text(
                x,
                y,
                z + 5,
                f"N{node_id}",
                fontsize=9,
                fontweight="bold"
            )

            self.ax.text(
                x,
                y,
                z - 7,
                f"{int(z)} m",
                fontsize=7
            )

        # ----------------------------------------------------
        # Current packet line
        # ----------------------------------------------------

        self.packet_line, = self.ax.plot(
            [],
            [],
            [],
            color=COLOR_PACKET,
            linewidth=4,
            marker="o",
            markersize=7
        )

        # ----------------------------------------------------
        # Successful links
        # ----------------------------------------------------

        self.success_lines = []

        # ----------------------------------------------------
        # Collision markers
        # ----------------------------------------------------

        self.collision_artist = self.ax.scatter(
            [],
            [],
            [],
            s=500,
            marker="X",
            color=COLOR_COLLISION,
            edgecolors="darkred",
            linewidths=2,
            depthshade=False
        )

        # ----------------------------------------------------
        # Transmission range
        # ----------------------------------------------------

        self.range_lines = []

        # ----------------------------------------------------
        # Text panels
        # ----------------------------------------------------

        self.info_text = self.fig.text(
            0.02,
            0.16,
            "",
            fontsize=10,
            family="monospace",
            verticalalignment="top"
        )

        self.event_text = self.fig.text(
            0.73,
            0.17,
            "",
            fontsize=10,
            family="monospace",
            verticalalignment="top"
        )

        self.status_text = self.fig.text(
            0.02,
            0.04,
            "",
            fontsize=10,
            family="monospace"
        )

        self.legend_text = self.fig.text(
            0.73,
            0.55,
            "",
            fontsize=9,
            family="monospace",
            verticalalignment="top"
        )

    # ========================================================
    # EVENT PROCESSING
    # ========================================================

    def calculate_statistics(self):

        tx = 0
        rx = 0
        collisions = 0

        for event in self.events[:self.index + 1]:

            if event["event"] == "TX":
                tx += 1

            elif event["event"] == "RX":
                rx += 1

            elif event["event"] == "COLLISION":
                collisions += 1

        self.tx_count = tx
        self.rx_count = rx
        self.collision_count = collisions

    # ========================================================
    # CONTENTION DETECTION
    # ========================================================

    def contention_detected(self):

        if self.mode != "aloha":
            return False

        current = self.events[self.index]

        if current["event"] != "TX":
            return False

        current_time = current["time"]

        window_start = (
            current_time - PACKET_DURATION
        )

        simultaneous = 0

        for event in self.events:

            if event["event"] != "TX":
                continue

            if (
                window_start
                <= event["time"]
                <= current_time
            ):

                simultaneous += 1

        return simultaneous > 1

    # ========================================================
    # TDMA DETECTION
    # ========================================================

    def tdma_scheduled(self):

        if self.mode != "tdma":
            return False

        current = self.events[self.index]

        return current["event"] == "TX"

    # ========================================================
    # UPDATE NODE COLOURS
    # ========================================================

    def update_node_states(self):

        current = self.events[self.index]

        self.current_tx_nodes = set()
        self.current_rx_nodes = set()
        self.current_collision_nodes = set()

        if current["event"] == "TX":

            self.current_tx_nodes.add(
                current["node"]
            )

        elif current["event"] == "RX":

            self.current_rx_nodes.add(
                current["node"]
            )

        elif current["event"] == "COLLISION":

            self.current_collision_nodes.add(
                current["node"]
            )

        for node_id, artist in self.node_artists.items():

            if node_id in self.current_collision_nodes:

                artist.set_color(
                    COLOR_COLLISION
                )

                artist.set_sizes([230])

            elif node_id in self.current_tx_nodes:

                artist.set_color(
                    COLOR_TX
                )

                artist.set_sizes([220])

            elif node_id in self.current_rx_nodes:

                artist.set_color(
                    COLOR_RX
                )

                artist.set_sizes([200])

            else:

                artist.set_color(
                    COLOR_IDLE
                )

                artist.set_sizes([130])

    # ========================================================
    # PACKET PATH
    # ========================================================

    def find_packet_source(self, packet):

        if packet is None:
            return None

        for i in range(
            self.index,
            -1,
            -1
        ):

            event = self.events[i]

            if (
                event["event"] == "TX"
                and event["packet"] == packet
            ):

                return event["node"]

        return None

    def update_packet_visual(self):

        current = self.events[self.index]

        self.packet_line.set_data(
            [],
            []
        )

        self.packet_line.set_3d_properties(
            []
        )

        if current["packet"] is None:
            return

        source = self.find_packet_source(
            current["packet"]
        )

        if source is None:
            return

        if source not in NODE_POSITIONS:
            return

        sx, sy, sz = NODE_POSITIONS[source]

        # ----------------------------------------------------
        # TX
        # ----------------------------------------------------

        if current["event"] == "TX":

            # Show packet leaving source
            self.packet_line.set_data(
                [sx, sx + 1],
                [sy, sy + 1]
            )

            self.packet_line.set_3d_properties(
                [sz, sz + 1]
            )

        # ----------------------------------------------------
        # RX
        # ----------------------------------------------------

        elif current["event"] == "RX":

            target = current["node"]

            if target not in NODE_POSITIONS:
                return

            tx, ty, tz = NODE_POSITIONS[target]

            self.packet_line.set_data(
                [sx, tx],
                [sy, ty]
            )

            self.packet_line.set_3d_properties(
                [sz, tz]
            )

            self.draw_success_link(
                source,
                target
            )

    # ========================================================
    # SUCCESS LINK
    # ========================================================

    def draw_success_link(
        self,
        source,
        target
    ):

        for line in self.success_lines:

            line.remove()

        self.success_lines.clear()

        if source not in NODE_POSITIONS:
            return

        if target not in NODE_POSITIONS:
            return

        sx, sy, sz = NODE_POSITIONS[source]
        tx, ty, tz = NODE_POSITIONS[target]

        line, = self.ax.plot(
            [sx, tx],
            [sy, ty],
            [sz, tz],
            color=COLOR_SUCCESS,
            linewidth=3,
            alpha=0.85
        )

        self.success_lines.append(
            line
        )

    # ========================================================
    # COLLISION VISUAL
    # ========================================================

    def update_collision_visual(self):

        current = self.events[self.index]

        if current["event"] != "COLLISION":

            self.collision_artist._offsets3d = (
                [],
                [],
                []
            )

            return

        node = current["node"]

        if node not in NODE_POSITIONS:
            return

        x, y, z = NODE_POSITIONS[node]

        self.collision_artist._offsets3d = (
            [x],
            [y],
            [z]
        )

    # ========================================================
    # TRANSMISSION RANGE
    # ========================================================

    def update_range_visual(self):

        for line in self.range_lines:

            line.remove()

        self.range_lines.clear()

        current = self.events[self.index]

        if current["event"] not in (
            "TX",
            "RX",
            "COLLISION"
        ):

            return

        node = current["node"]

        if node not in NODE_POSITIONS:
            return

        x, y, z = NODE_POSITIONS[node]

        # Horizontal circle
        points = 50

        xs = []
        ys = []
        zs = []

        for i in range(points + 1):

            theta = (
                2
                * math.pi
                * i
                / points
            )

            xs.append(
                x
                + TRANSMISSION_RANGE
                * math.cos(theta)
            )

            ys.append(
                y
                + TRANSMISSION_RANGE
                * math.sin(theta)
            )

            zs.append(z)

        line, = self.ax.plot(
            xs,
            ys,
            zs,
            linestyle="--",
            color=COLOR_RANGE,
            alpha=0.45,
            linewidth=1.5
        )

        self.range_lines.append(
            line
        )

    # ========================================================
    # TEXT PANELS
    # ========================================================

    def update_text(self):

        current = self.events[self.index]

        event_type = current["event"]
        node = current["node"]
        packet = current["packet"]

        # ----------------------------------------------------
        # MAC status
        # ----------------------------------------------------

        if self.mode == "aloha":

            if self.contention_detected():

                mac_status = (
                    "⚠ CONTENTION DETECTED"
                )

            else:

                mac_status = (
                    "CONTENTION-BASED ACCESS"
                )

        else:

            if self.tdma_scheduled():

                mac_status = (
                    "✓ SCHEDULED TRANSMISSION"
                )

            else:

                mac_status = (
                    "SCHEDULED ACCESS"
                )

        # ----------------------------------------------------
        # Event explanation
        # ----------------------------------------------------

        if event_type == "TX":

            event_description = (
                "NODE IS TRANSMITTING"
            )

        elif event_type == "RX":

            event_description = (
                "PACKET RECEIVED"
            )

        elif event_type == "COLLISION":

            event_description = (
                "MULTIPLE SIGNALS OVERLAPPED"
            )

        else:

            event_description = event_type

        # ----------------------------------------------------
        # Left panel
        # ----------------------------------------------------

        pdr = (
            (self.rx_count / self.tx_count) * 100
            if self.tx_count > 0
            else 0
        )

        throughput = (
            (
                self.rx_count
                * PACKET_SIZE_BYTES
                * 8
                / current["time"]
            )
            / 1000
            if current["time"] > 0
            else 0
        )

        self.info_text.set_text(

            "MAC PROTOCOL\n"
            "━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
            f"{self.mode.upper()}\n\n"

            f"SIM TIME       : "
            f"{current['time']:.3f} s\n"

            f"EVENT          : "
            f"{self.index + 1}/{len(self.events)}\n\n"

            f"PHY TX        : "
            f"{self.tx_count}\n"

            f"PHY RX        : "
            f"{self.rx_count}\n"

            f"COLLISIONS    : "
            f"{self.collision_count}\n\n"

            f"EVENT PDR     : "
            f"{pdr:.2f}%\n"

            f"EST. THROUGHPUT: "
            f"{throughput:.3f} kbps\n\n"

            f"MAC STATUS\n"
            f"→ {mac_status}"
        )

        # ----------------------------------------------------
        # Current event
        # ----------------------------------------------------

        source = self.find_packet_source(
            packet
        )

        source_text = (
            f"N{source}"
            if source is not None
            else "Unknown"
        )

        self.event_text.set_text(

            "CURRENT EVENT\n"
            "━━━━━━━━━━━━━━━━━━━━━━━━━━\n"

            f"Time      : "
            f"{current['time']:.6f} s\n"

            f"Type      : "
            f"{event_type}\n"

            f"Node      : "
            f"N{node}\n"

            f"Packet    : "
            f"{packet if packet is not None else '-'}\n"

            f"Source    : "
            f"{source_text}\n"

            f"Noise     : "
            f"{current['noise']:.6f}\n\n"

            f"STATUS\n"
            f"{event_description}"
        )

        # ----------------------------------------------------
        # Legend
        # ----------------------------------------------------

        self.legend_text.set_text(

            "VISUAL LEGEND\n"
            "━━━━━━━━━━━━━━━━━━━━━━━━━━\n"

            "●  BLUE    = Idle sensor node\n"
            "●  YELLOW  = TX / transmitting\n"
            "●  GREEN   = RX / receiving\n"
            "✕  RED     = Collision\n"
            "━  ORANGE  = Packet in transit\n"
            "━  GREEN   = Successful link\n"
            "┄  PURPLE  = TDMA scheduled\n"
            "┄  GRAY    = Transmission range\n"
            "★  ORANGE  = Sink\n\n"

            "CONTROLS\n"
            "━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
            "SPACE  Play / Pause\n"
            "← →    Previous / Next event\n"
            "↑ ↓    Change replay speed\n"
            "R      Reset\n"
            "Q      Quit\n"
        )

        # ----------------------------------------------------
        # Bottom status
        # ----------------------------------------------------

        self.status_text.set_text(

            f"MODE: {self.mode.upper()}    |    "
            f"TIME: {current['time']:.3f} s / "
            f"{self.max_time:.3f} s    |    "

            f"TX: {self.tx_count}    |    "
            f"RX: {self.rx_count}    |    "
            f"COLLISIONS: {self.collision_count}    |    "

            f"SPEED: {self.speed:.1f}x"
        )

    # ========================================================
    # MAIN SCENE UPDATE
    # ========================================================

    def update_scene(self):

        self.calculate_statistics()

        self.update_node_states()

        self.update_packet_visual()

        self.update_collision_visual()

        self.update_range_visual()

        self.update_text()

        self.fig.canvas.draw_idle()

    # ========================================================
    # ANIMATION
    # ========================================================

    def animation_step(self, frame):

        if not self.playing:
            return

        steps = max(
            1,
            int(self.speed)
        )

        self.index += steps

        if self.index >= len(self.events):

            self.index = (
                len(self.events) - 1
            )

            self.playing = False

        self.update_scene()

    # ========================================================
    # KEYBOARD CONTROLS
    # ========================================================

    def on_key(self, event):

        if event.key == " ":

            self.playing = (
                not self.playing
            )

        elif event.key == "right":

            self.playing = False

            self.index = min(
                self.index + 1,
                len(self.events) - 1
            )

            self.update_scene()

        elif event.key == "left":

            self.playing = False

            self.index = max(
                self.index - 1,
                0
            )

            self.update_scene()

        elif event.key == "up":

            self.speed = min(
                self.speed * 2,
                16
            )

        elif event.key == "down":

            self.speed = max(
                self.speed / 2,
                0.25
            )

        elif event.key in ("r", "R"):

            self.index = 0

            self.playing = True

            self.speed = 1.0

            self.update_scene()

        elif event.key in ("q", "Q"):

            plt.close(
                self.fig
            )


# ============================================================
# MAIN
# ============================================================

def main():

    if len(sys.argv) != 2:

        print()
        print(
            "Usage:"
        )

        print(
            "python visualization/"
            "uwsn_3d_replay.py aloha"
        )

        print(
            "python visualization/"
            "uwsn_3d_replay.py tdma"
        )

        print()

        sys.exit(1)

    mode = sys.argv[1].lower()

    try:

        UWSNReplay(mode)

    except Exception as error:

        print()
        print(
            "ERROR:"
        )
        print(error)
        print()

        sys.exit(1)

    plt.show()


if __name__ == "__main__":

    main()

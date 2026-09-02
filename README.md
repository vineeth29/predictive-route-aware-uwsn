# Predictive Route-Aware Packetization for Energy-Efficient Underwater Acoustic Sensor Networks

<p align="center">

### A Predictive Communication Framework for Underwater Wireless Sensor Networks

**NS-3.41 + Aqua-Sim NG**

</p>

---

## Table of Contents

1. [Project Overview](#1-project-overview)
2. [Research Problem](#2-research-problem)
3. [Research Motivation](#3-research-motivation)
4. [Research Gap](#4-research-gap)
5. [Proposed Research Contribution](#5-proposed-research-contribution)
6. [Research Objectives](#6-research-objectives)
7. [Research Questions](#7-research-questions)
8. [Overall Research Concept](#8-overall-research-concept)
9. [Final System Architecture](#9-final-system-architecture)
10. [Complete Project Workflow](#10-complete-project-workflow)
11. [Final Build Definition](#11-final-build-definition)
12. [UWSN Network Model](#12-uwsn-network-model)
13. [Candidate Routes](#13-candidate-routes)
14. [Simulation Architecture](#14-simulation-architecture)
15. [Communication Stack](#15-communication-stack)
16. [Data Collection Architecture](#16-data-collection-architecture)
17. [Phase 1 - Reliable Baseline](#17-phase-1---reliable-baseline)
18. [Phase 2 - Channel-State Extraction](#18-phase-2---channel-state-extraction)
19. [Phase 3 - Short-Term Prediction](#19-phase-3---short-term-prediction)
20. [Phase 4 - Route-Level Risk Prediction](#20-phase-4---route-level-risk-prediction)
21. [Phase 5 - Adaptive Packetization](#21-phase-5---adaptive-packetization)
22. [Fragmentation and Reassembly](#22-fragmentation-and-reassembly)
23. [Phase 6 - ACK/NACK Feedback](#23-phase-6---acknack-feedback)
24. [Phase 7 - Energy Model](#24-phase-7---energy-model)
25. [Final Joint Decision Engine](#25-final-joint-decision-engine)
26. [Baseline Strategies](#26-baseline-strategies)
27. [Final Experimental Methodology](#27-final-experimental-methodology)
28. [Performance Metrics](#28-performance-metrics)
29. [Data Pipeline](#29-data-pipeline)
30. [Results Pipeline](#30-results-pipeline)
31. [Visualization](#31-visualization)
32. [Repository Structure](#32-repository-structure)
33. [Build Environment](#33-build-environment)
34. [Building the Current Project](#34-building-the-current-project)
35. [Running the Current Baseline](#35-running-the-current-baseline)
36. [Debugging Workflow](#36-debugging-workflow)
37. [Experiment Reproducibility](#37-experiment-reproducibility)
38. [Current Implementation Status](#38-current-implementation-status)
39. [Seven-Phase Development Roadmap](#39-seven-phase-development-roadmap)
40. [Expected Final Outputs](#40-expected-final-outputs)
41. [Final Research Evaluation](#41-final-research-evaluation)
42. [Limitations](#42-limitations)
43. [Research Integrity](#43-research-integrity)
44. [Final Target Architecture](#44-final-target-architecture)
45. [Conclusion](#45-conclusion)

---

# 1. Project Overview

This project investigates a **predictive, route-aware packetization framework for energy-efficient communication in Underwater Wireless Sensor Networks (UWSNs)**.

The project is developed using:

- **NS-3.41**
- **Aqua-Sim NG**
- C++
- Python
- CSV-based experiment data
- Git

The central research idea is to use **historical underwater communication observations** to predict short-term future link conditions and use those predictions to make better communication decisions.

The proposed system jointly considers:

- Route selection
- Packet-size selection
- Fragmentation
- Retransmission risk
- Delay
- Reliability
- Energy consumption
- ACK/NACK feedback

The final system is intended to move beyond conventional fixed and purely reactive communication approaches.

The overall concept is:

```text
                 HISTORICAL CHANNEL OBSERVATIONS
                              |
                              v
                     LINK-STATE EXTRACTION
                              |
                              v
                       PREDICTION ENGINE
                              |
                              v
                    PREDICTED LINK STATES
                              |
                              v
                    ROUTE-LEVEL RISK ENGINE
                              |
                              v
                     JOINT DECISION ENGINE
                         /           \
                        /             \
                       v               v
                ROUTE SELECTION   PACKETIZATION
                                      |
                                      v
                              FRAGMENTATION
                                DECISION
                                      |
                                      v
                                  TRANSMIT
                                      |
                                      v
                                  RECEIVE
                                      |
                                      v
                                  ACK/NACK
                                      |
                                      v
                               STATE UPDATE
                                      |
                                      +-------------->
                                           NEXT CYCLE
```

The final architecture is documented in this README even though several components are still under development.

---

# 2. Research Problem

Underwater Wireless Sensor Networks face communication challenges that are substantially different from conventional terrestrial wireless networks.

Underwater communication commonly relies on acoustic signals.

The underwater acoustic environment can experience:

* High propagation delay
* Limited bandwidth
* Time-varying channel quality
* Interference
* Collisions
* Packet loss
* Retransmissions
* Queue buildup
* High communication energy consumption
* Multi-hop reliability problems

These conditions make fixed communication parameters potentially inefficient.

For example:

```text
                    GOOD CHANNEL
                         |
                         v
                    LARGE PACKET
                         |
                         v
               Lower Relative Overhead
```

But under poor channel conditions:

```text
                    POOR CHANNEL
                         |
                         v
                    LARGE PACKET
                         |
                         v
                 Higher Failure Cost
                         |
                         v
                    RETRANSMISSION
                         |
                         v
                 More Energy + Delay
```

Therefore, the communication strategy should ideally account for changing channel conditions.

The main research problem is:

> **How can short-term prediction of underwater communication conditions be combined with complete-route evaluation and adaptive packetization to improve reliability, throughput, delay, retransmission behavior, and energy efficiency in multi-hop UWSNs?**

---

# 3. Research Motivation

## 3.1 Time-Varying Underwater Channel

The underwater acoustic channel should not be assumed to remain constant throughout a simulation.

Conceptually:

```text
Channel Quality

Good
  |
  |       /\
  |      /  \
  |     /    \        /\
  |    /      \      /  \
  |___/________\____/____\________
  |
  +---------------------------------> Time
```

A packet size or route that is efficient at one point in time may not remain optimal later.

---

## 3.2 Packet Size Trade-Off

Packet size creates a fundamental trade-off.

### Large Packets

Advantages:

* Lower relative header overhead
* More application data per transmission
* Potentially better efficiency when the channel is reliable

Disadvantages:

* More data can be lost when a packet fails
* Higher retransmission cost
* Potentially greater delay under poor conditions

### Small Packets

Advantages:

* Less application data lost per failed transmission
* Potentially better reliability under poor conditions

Disadvantages:

* More packets
* More headers
* More transmissions
* Additional fragmentation overhead

Therefore:

```text
                    PACKET SIZE
                         |
             +-----------+-----------+
             |                       |
             v                       v
        LARGE PACKET            SMALL PACKET
             |                       |
             v                       v
      Lower overhead          Smaller failure
                              exposure
             |                       |
             +-----------+-----------+
                         |
                         v
                CHANNEL DEPENDENT
                     DECISION
```

---

## 3.3 Route Trade-Off

Routing creates another important trade-off.

A shorter route is not automatically the best route.

For example:

```text
Route A:

0 -> 1 -> 2 -> 3 -> 4 -> 5 -> 6 -> 7
```

and:

```text
Route B:

0 -> 4 -> 5 -> 7
```

Route B has fewer hops.

However, if one link on Route B becomes severely degraded, Route A may provide better end-to-end performance.

Therefore, the proposed research evaluates the **complete candidate route**.

---

# 4. Research Gap

A fixed communication system uses predetermined parameters:

```text
Fixed Route
    +
Fixed Packet Size
    +
Fixed Communication Configuration
```

A reactive system observes current conditions and responds:

```text
Current Condition
       |
       v
Current Decision
       |
       v
React to Problem
```

The proposed research investigates predictive communication:

```text
Historical Conditions
       |
       v
Prediction
       |
       v
Future Condition
       |
       v
Decision Before Degradation
```

The research additionally combines:

```text
Prediction
    +
Complete Route Awareness
    +
Adaptive Packetization
    +
Fragmentation
    +
ACK/NACK Feedback
    +
Energy Evaluation
```

The key research direction is therefore not merely predicting the channel, but using the prediction to make a **joint communication decision**.

---

# 5. Proposed Research Contribution

The intended contribution is a framework that combines:

1. Historical per-link channel-state extraction.
2. Short-term link-condition prediction.
3. Complete-route risk evaluation.
4. Predictive route selection.
5. Adaptive packet-size selection.
6. Fragmentation/reassembly decisions.
7. ACK/NACK feedback.
8. Energy-aware evaluation.

The intended contribution can be summarized as:

```text
                PREDICTIVE COMMUNICATION

                       Historical Data
                              |
                              v
                      Future Prediction
                              |
                              v
                     Route-Level Risk
                              |
                              v
                    Route Selection
                              |
                              v
                  Packetization Selection
                              |
                              v
                   Fragmentation Decision
                              |
                              v
                        Transmission
                              |
                              v
                         ACK/NACK
                              |
                              v
                        State Update
```

The framework will be experimentally evaluated rather than assuming that prediction automatically improves performance.

---

# 6. Research Objectives

## Objective 1 - Reliable Simulation Foundation

Build a controlled underwater acoustic simulation environment using NS-3.41 and Aqua-Sim NG.

---

## Objective 2 - Historical Channel-State Extraction

Collect and organize historical information for individual communication links.

Potential variables include:

* PDR
* Packet loss
* Collision rate
* RX power
* SINR
* Delay
* Retransmissions
* Queue state
* Temporal trend

---

## Objective 3 - Short-Term Prediction

Predict near-future communication conditions for individual links.

---

## Objective 4 - Route-Level Prediction

Combine predicted link conditions to estimate the future risk of complete candidate routes.

---

## Objective 5 - Adaptive Packetization

Select an appropriate packet size based on predicted route conditions.

---

## Objective 6 - Fragmentation Decision

Determine whether direct transmission or fragmentation provides a better expected communication outcome.

---

## Objective 7 - Feedback Integration

Use ACK/NACK outcomes to update the link-state history and future decisions.

---

## Objective 8 - Energy Evaluation

Measure the energy cost of the different communication strategies.

---

# 7. Research Questions

### RQ1 - Prediction

Can short-term prediction improve communication decisions compared with purely reactive approaches?

### RQ2 - Route Awareness

Does evaluating the complete predicted route provide better decisions than evaluating only the immediate next hop?

### RQ3 - Packetization

Can adaptive packet sizing reduce retransmissions and improve delivery reliability?

### RQ4 - Fragmentation

When is fragmentation more beneficial than direct packet transmission?

### RQ5 - Energy

Can predictive route-aware packetization reduce energy consumed per successfully delivered bit?

### RQ6 - Overall Performance

Can the proposed system outperform fixed and reactive baselines under changing underwater channel conditions?

---

# 8. Overall Research Concept

The complete concept is:

```text
                        UWSN
                         |
                         v
                Observe Channel
                         |
                         v
              Historical Link State
                         |
                         v
                 Predict Future
                         |
                         v
                Evaluate Routes
                         |
                         v
               Evaluate Packet Size
                         |
                         v
              Evaluate Fragmentation
                         |
                         v
                  Make Decision
                         |
                         v
                   Transmit
                         |
                         v
                 Actual Outcome
                         |
                    +----+----+
                    |         |
                   ACK       NACK
                    |         |
                    |         v
                    |    Retransmission
                    |         |
                    +----+----+
                         |
                         v
                  Update State
                         |
                         v
                  Next Prediction
```

The important feature is the feedback loop.

The system does not simply make one decision and stop.

It continuously updates its understanding of the communication environment.

---

# 9. Final System Architecture

The final target architecture is:

```text
                         +-----------------------------+
                         |       UWSN ENVIRONMENT      |
                         |                             |
                         | Nodes / Traffic / Channel  |
                         | Acoustic Propagation       |
                         +--------------+--------------+
                                        |
                                        v
                         +-----------------------------+
                         |    CHANNEL OBSERVATION      |
                         |                             |
                         | PHY TX                      |
                         | PHY RX                      |
                         | RX Power                    |
                         | SINR                        |
                         | Noise                       |
                         | Interference                |
                         | Collisions                  |
                         | Queue                       |
                         | Delay                       |
                         | Packet Outcomes             |
                         +--------------+--------------+
                                        |
                                        v
                         +-----------------------------+
                         |     LINK-STATE MANAGER      |
                         |                             |
                         | Per-Link History            |
                         | Time Windows                |
                         | Statistics                  |
                         | Trends                      |
                         +--------------+--------------+
                                        |
                                        v
                         +-----------------------------+
                         |      PREDICTION ENGINE      |
                         |                             |
                         | Future PDR                  |
                         | Future Loss                 |
                         | Future Delay                |
                         | Future Link Risk            |
                         +--------------+--------------+
                                        |
                                        v
                +----------------------------------------------+
                |             ROUTE RISK ENGINE                 |
                |                                              |
                | Route A: 0 -> 1 -> 2 -> 3 -> 4 -> 5 -> 6 -> 7|
                | Route B: 0 -> 4 -> 5 -> 7                    |
                |                                              |
                | Complete Predicted Route Condition           |
                +-----------------------+----------------------+
                                        |
                                        v
                +----------------------------------------------+
                |              JOINT DECISION ENGINE            |
                |                                              |
                | Route + Packet Size + Fragmentation          |
                +-----------------------+----------------------+
                                        |
                         +--------------+--------------+
                         |                             |
                         v                             v
                  ROUTE SELECTION              PACKETIZATION
                         |                             |
                  +------+-----+              +--------+--------+
                  |            |              |        |        |
                  v            v              v        v        v
               Route A      Route B         Large    Medium   Small
                                             Packet   Packet  Packet
                                                \       |      /
                                                 \      |     /
                                                  +-----+----+
                                                        |
                                                        v
                                             Fragmentation Decision
                                                        |
                                                        v
                                               +----------------+
                                               | MAC / ROUTING  |
                                               +-------+--------+
                                                       |
                                                       v
                                               +----------------+
                                               |  AQUA-SIM PHY  |
                                               +-------+--------+
                                                       |
                                                       v
                                               +----------------+
                                               |    ACOUSTIC    |
                                               |    CHANNEL     |
                                               +-------+--------+
                                                       |
                                                       v
                                               +----------------+
                                               |    RECEIVER    |
                                               +-------+--------+
                                                       |
                                                  +----+----+
                                                  |         |
                                                  v         v
                                                 ACK       NACK
                                                  |         |
                                                  |         v
                                                  |   RETRANSMISSION
                                                  |         |
                                                  +----+----+
                                                       |
                                                       v
                                             FEEDBACK / STATE UPDATE
                                                       |
                                                       +------------>
                                                           NEXT CYCLE
```

---

# 10. Complete Project Workflow

The entire project workflow is:

```text
                         START
                           |
                           v
                  Configure Scenario
                           |
                           v
                  Configure Topology
                           |
                           v
                    Configure Routes
                           |
                           v
                   Configure Traffic
                           |
                           v
                Run Underwater Simulation
                           |
                           v
             Collect PHY / MAC / Network Data
                           |
                           v
                Build Link-State History
                           |
                           v
                 Predict Future State
                           |
                           v
                Evaluate Candidate Routes
                           |
                           v
                   Calculate Route Risk
                           |
                           v
                   Select Best Route
                           |
                           v
              Evaluate Packetization Options
                           |
                           v
                 Select Packet Size
                           |
                           v
                Evaluate Fragmentation
                           |
                           v
                       TRANSMIT
                           |
                           v
                       RECEIVE
                           |
                           v
                      ACK / NACK
                           |
                  +--------+--------+
                  |                 |
                 ACK               NACK
                  |                 |
                  v                 v
              SUCCESS           FAILURE
                  |                 |
                  |                 v
                  |          RETRANSMISSION
                  |                 |
                  +--------+--------+
                           |
                           v
                 Update Link Statistics
                           |
                           v
                   Update Energy State
                           |
                           v
                  Update Prediction
                           |
                           v
                   Next Decision Cycle
                           |
                           +------------------->
```

---

# 11. Final Build Definition

The final build is intended to be a modular predictive communication framework.

```text
+------------------------------------------------------------+
|       PREDICTIVE ROUTE-AWARE COMMUNICATION SYSTEM          |
+------------------------------------------------------------+
|                                                            |
|  1. Channel State Collector                               |
|                                                            |
|  2. Link History Manager                                  |
|                                                            |
|  3. Feature Extraction                                    |
|                                                            |
|  4. Prediction Engine                                     |
|                                                            |
|  5. Route Risk Engine                                     |
|                                                            |
|  6. Predictive Route Selector                             |
|                                                            |
|  7. Packet Size Selection Engine                          |
|                                                            |
|  8. Fragmentation / Reassembly Manager                    |
|                                                            |
|  9. Transmission Controller                               |
|                                                            |
| 10. ACK/NACK Processor                                    |
|                                                            |
| 11. Energy Accounting                                     |
|                                                            |
| 12. Metrics and Experiment Logger                         |
|                                                            |
+------------------------------------------------------------+
```

The final system combines:

```text
Channel Observation
        +
Historical State
        +
Prediction
        +
Route Risk
        +
Route Selection
        +
Packetization
        +
Fragmentation
        +
ACK/NACK
        +
Energy Evaluation
```

---

# 12. UWSN Network Model

The current controlled simulation uses an 8-node underwater network.

```text
Node 0 = SOURCE

Node 1
Node 2
Node 3
Node 4
Node 5
Node 6

Node 7 = SINK
```

The conceptual network is:

```text
                       UNDERWATER NETWORK

                           Node 0
                           SOURCE
                              |
                              v
                           Node 1
                              |
                              v
                           Node 2
                              |
                              v
                           Node 3
                              |
                              v
                           Node 4
                          /     \
                         /       \
                        v         v
                     Node 5    Alternative
                        |
                        v
                     Node 6
                        |
                        v
                     Node 7
                      SINK
```

The controlled topology allows routing strategies to be compared under comparable conditions.

---

# 13. Candidate Routes

## Route A

The longer candidate route is:

```text
0 -> 1 -> 2 -> 3 -> 4 -> 5 -> 6 -> 7
```

Diagram:

```text
SOURCE
   |
   v
 Node 0
   |
   v
 Node 1
   |
   v
 Node 2
   |
   v
 Node 3
   |
   v
 Node 4
   |
   v
 Node 5
   |
   v
 Node 6
   |
   v
 Node 7
   |
   v
 SINK
```

The current static route representation uses Aqua-Sim addresses corresponding to the destination.

---

## Route B

The shorter candidate route is:

```text
0 -> 4 -> 5 -> 7
```

Diagram:

```text
SOURCE
   |
   v
 Node 0
   |
   v
 Node 4
   |
   v
 Node 5
   |
   v
 Node 7
   |
   v
 SINK
```

---

## Route Selection Principle

The proposed system should not select routes using hop count alone.

Instead:

```text
Predicted Link Conditions
           |
           v
Complete Route Condition
           |
           v
Route Risk
           |
           v
Expected Communication Cost
           |
           v
Route Decision
```

---

# 14. Simulation Architecture

The research repository is separated from the NS-3 installation.

```text
+--------------------------------------+
|          RESEARCH REPOSITORY         |
|                                      |
| simulations/                         |
| visualization/                       |
| analysis/                            |
| results/                             |
| docs/                                |
| configs/                             |
+-------------------+------------------+
                    |
                    v
             NS-3.41 Environment
                    |
                    v
               Aqua-Sim NG
                    |
                    v
          Underwater Simulation
```

Current project location:

```text
~/uwsn-project/project
```

Current NS-3 environment:

```text
~/uwsn-project/ns-allinone-3.41/ns-3.41
```

---

# 15. Communication Stack

The current and future communication architecture is:

```text
+--------------------------------+
|          APPLICATION           |
|        Packet Generation      |
+---------------+----------------+
                |
                v
+--------------------------------+
|           ROUTING              |
|       Route Selection          |
+---------------+----------------+
                |
                v
+--------------------------------+
|             MAC                |
|        ALOHA / TDMA            |
+---------------+----------------+
                |
                v
+--------------------------------+
|             PHY                |
|    Underwater Acoustic PHY     |
+---------------+----------------+
                |
                v
+--------------------------------+
|       ACOUSTIC CHANNEL         |
+--------------------------------+
```

The predictive modules will interact with the routing, packetization, feedback, and measurement mechanisms.

---

# 16. Data Collection Architecture

The current simulation collects low-level communication events.

```text
                     SIMULATION
                         |
             +-----------+-----------+
             |           |           |
             v           v           v
            PHY         MAC        QUEUE
             |           |           |
             +-----------+-----------+
                         |
                         v
                  EVENT COLLECTOR
                         |
                         v
                      CSV FILE
                         |
                         v
                 DATA PROCESSING
                         |
                         v
                LINK-STATE HISTORY
```

Current event categories include:

```text
TX
RX
RXPOWER
SINR
COLLISION
```

The current event CSV structure contains fields such as:

```text
time
event
node
packet
noise
rxPower
error
interference
environmentalNoise
sinr
```

Example header:

```text
time,event,node,packet,noise,rxPower,error,interference,environmentalNoise,sinr
```

---

# 17. Phase 1 - Reliable Baseline

## Objective

Build a trustworthy simulation foundation before introducing prediction.

The baseline provides the experimental reference against which all future adaptive methods will be compared.

---

## Implemented Components

### Simulation

* NS-3.41
* Aqua-Sim NG
* Controlled UWSN topology
* Multi-hop communication

### Routing

* Route A
* Route B
* Static route foundation

### MAC

* Fixed ALOHA baseline
* TDMA baseline framework

### Traffic

* Packet generation
* Configurable packet size
* Configurable simulation duration
* Source/sink configuration

### Monitoring

* PHY TX
* PHY RX
* RX power
* Collision
* Queue
* Delay
* Event logging

---

## Phase 1 Workflow

```text
Topology
   |
   v
Traffic
   |
   v
MAC
   |
   v
Routing
   |
   v
PHY
   |
   v
Acoustic Channel
   |
   v
Receiver
   |
   v
Metrics
```

---

## Current Phase 1 Issue

The simulation is producing significant PHY-level activity.

However, the final end-to-end sink delivery measurement is still being validated.

A diagnostic experiment produced values such as:

```text
Application TX : 210
PHY TX         : 385
PHY RX         : 859
Collisions     : 1321
Average Delay  : 5587.715 ms
Average Queue  : 8.941
```

while the current sink measurement reported:

```text
Sink RX        : 0
PDR            : 0%
Throughput     : 0 kbps
```

This indicates that PHY-level activity is occurring, but the final end-to-end delivery measurement cannot yet be considered validated.

The immediate goal is therefore:

```text
Application TX
      |
      v
Forwarding
      |
      v
Final Hop
      |
      v
Sink
      |
      v
Correct Delivery Count
      |
      v
Correct PDR
      |
      v
Correct Throughput
      |
      v
Validated Baseline
```

---

# 18. Phase 2 - Channel-State Extraction

## Objective

Transform raw simulation events into structured historical state for individual communication links.

Current raw observations include:

```text
TX
RX
RXPOWER
SINR
COLLISION
QUEUE
DELAY
PACKET OUTCOME
```

The future link-state representation should contain information such as:

```text
+--------------------------------+
|          LINK STATE            |
+--------------------------------+
| Source Node                    |
| Destination Node               |
| Timestamp                      |
| PDR                            |
| Loss Rate                      |
| Collision Rate                 |
| RX Power                       |
| SINR                           |
| Delay                          |
| Retransmissions                |
| Queue State                    |
| Temporal Trend                 |
+--------------------------------+
```

---

## Example Historical Link State

```text
Link 1 -> 2

Time       PDR      SINR      Delay      Collision
---------------------------------------------------
10 s       0.95     Good      Low        Low
20 s       0.93     Good      Low        Low
30 s       0.86     Medium    Medium     Medium
40 s       0.71     Poor      High       High
50 s       0.65     Poor      High       High
```

The purpose of Phase 2 is to generate the time-series information required by the prediction engine.

---

# 19. Phase 3 - Short-Term Prediction

## Objective

Predict the near-future condition of individual underwater links.

Conceptual process:

```text
Historical Observations
          |
          +---- t-3
          |
          +---- t-2
          |
          +---- t-1
          |
          +---- t
               |
               v
        Prediction Engine
               |
               v
        Future Link State
               |
               +---- t + Δ
```

Potential prediction targets include:

* Future PDR
* Future loss rate
* Future SINR
* Future RX power
* Future delay
* Future collision probability
* Future link risk

---

## Prediction Pipeline

```text
Historical Link Data
        |
        v
Feature Construction
        |
        v
Prediction Model
        |
        v
Future Link Condition
        |
        v
Prediction Validation
```

The prediction model will be selected and validated experimentally after the historical state pipeline is reliable.

---

# 20. Phase 4 - Route-Level Risk Prediction

## Objective

Use predicted link conditions to estimate the future condition of complete candidate routes.

This is one of the central route-aware components of the proposed framework.

---

## Example

Route A:

```text
0 -> 1 -> 2 -> 3 -> 4 -> 5 -> 6 -> 7
```

Predicted link states:

```text
0-1 : Good
1-2 : Good
2-3 : Medium
3-4 : Poor
4-5 : Good
5-6 : Good
6-7 : Medium
```

Route B:

```text
0 -> 4 -> 5 -> 7
```

Predicted link states:

```text
0-4 : Good
4-5 : Good
5-7 : Good
```

The route engine should evaluate the complete route rather than simply counting hops.

---

## Route Risk Architecture

```text
                 PREDICTED LINK STATES
                          |
             +------------+------------+
             |                         |
             v                         v
          ROUTE A                   ROUTE B
             |                         |
             v                         v
       Link Predictions         Link Predictions
             |                         |
             v                         v
        Route Risk A              Route Risk B
             |                         |
             +------------+------------+
                          |
                          v
                   Route Decision
```

The exact mathematical route-risk formulation will be finalized during implementation and experimental validation.

---

# 21. Phase 5 - Adaptive Packetization

## Objective

Select the packetization strategy based on predicted route conditions.

Potential packet sizes include:

```text
128 bytes
256 bytes
512 bytes
1024 bytes
```

The final candidate set will be established from controlled experiments.

---

## Packetization Decision

```text
Predicted Route Condition
          |
          v
+-------------------------+
| Packetization Evaluator |
+-----------+-------------+
            |
      +-----+-----+-----+
      |           |     |
      v           v     v
    128 B       512 B  1024 B
      |           |     |
      +-----+-----+-----+
            |
            v
       Expected Cost
            |
            v
      Select Strategy
```

The decision should consider:

* Predicted reliability
* Retransmission probability
* Header overhead
* Fragmentation overhead
* Delay
* Energy

The intended approach is not simply:

```text
Bad channel -> Small packet
```

Instead:

```text
Predicted Condition
        |
        v
Evaluate Candidate Strategies
        |
        v
Estimate Expected Cost
        |
        v
Select Best Strategy
```

---

# 22. Fragmentation and Reassembly

## Objective

Determine whether an application packet should be transmitted directly or fragmented.

Conceptual flow:

```text
                 APPLICATION PACKET
                         |
                         v
                FRAGMENTATION ENGINE
                         |
                  +------+------+
                  |             |
                  v             v
             NO FRAGMENT      FRAGMENT
                  |             |
                  v             v
              DIRECT TX     Fragment 1
                            Fragment 2
                            Fragment 3
                                 |
                                 v
                            TRANSMISSION
                                 |
                                 v
                             REASSEMBLY
```

Fragmentation introduces:

* Additional headers
* More transmissions
* Additional processing
* More potential failure points
* Reassembly requirements
* Additional delay

The decision should compare:

```text
Expected Direct Transmission Cost

versus

Expected Fragmented Transmission Cost
```

---

# 23. Phase 6 - ACK/NACK Feedback

## Objective

Close the adaptive communication loop.

The intended mechanism is:

```text
                    TRANSMIT
                       |
                       v
                    RECEIVER
                       |
              +--------+--------+
              |                 |
              v                 v
             ACK               NACK
              |                 |
              v                 v
          SUCCESS        FAILURE DETECTED
                              |
                              v
                        RETRANSMISSION
                              |
                              v
                         STATE UPDATE
                              |
                              v
                          PREDICTION
                              |
                              v
                        NEXT DECISION
```

---

## Feedback Loop

```text
Prediction
    |
    v
Decision
    |
    v
Transmission
    |
    v
Actual Outcome
    |
    v
ACK / NACK
    |
    v
Update History
    |
    v
Next Prediction
```

The actual communication outcome becomes new information for future decisions.

---

# 24. Phase 7 - Energy Model

## Objective

Quantify the energy consequences of routing, packetization, fragmentation, and retransmissions.

The energy model should eventually account for:

```text
Transmission Energy
        +
Reception Energy
        +
Idle Energy
        +
Retransmission Energy
        +
Fragmentation Energy
        +
Protocol Overhead
```

---

## Energy Pipeline

```text
Communication Activity
        |
        +---- TX
        |
        +---- RX
        |
        +---- Idle
        |
        +---- Retransmission
        |
        +---- Fragmentation
        |
        v
Energy Accounting
        |
        v
Total Energy
        |
        v
Energy / Delivered Bit
        |
        v
Network Lifetime
```

---

## Primary Energy Metric

The primary energy metric is:

```text
Energy per Successfully Delivered Bit
```

Formula:

```text
Energy per Delivered Bit
=
Total Communication Energy
--------------------------------
Successfully Delivered Bits
```

---

## Network Lifetime

The final system should also evaluate network lifetime.

This is important because routing decisions may cause some nodes to forward significantly more traffic than others.

---

# 25. Final Joint Decision Engine

The final decision engine combines the major components.

```text
                    HISTORICAL DATA
                           |
                           v
                 +-------------------+
                 | Link-State        |
                 | Extraction        |
                 +---------+---------+
                           |
                           v
                 +-------------------+
                 | Prediction        |
                 | Engine            |
                 +---------+---------+
                           |
                           v
                 +-------------------+
                 | Route Risk        |
                 | Engine            |
                 +---------+---------+
                           |
                           v
                 +-------------------+
                 | Route Selector    |
                 +---------+---------+
                           |
                           v
                 +-------------------+
                 | Packet Size       |
                 | Selector          |
                 +---------+---------+
                           |
                           v
                 +-------------------+
                 | Fragmentation     |
                 | Decision          |
                 +---------+---------+
                           |
                           v
                 +-------------------+
                 | Transmission      |
                 +---------+---------+
                           |
                           v
                      ACK / NACK
                           |
                           v
                 +-------------------+
                 | State Update      |
                 +---------+---------+
                           |
                           +------------>
                              NEXT CYCLE
```

The joint decision should ultimately answer:

```text
Which route?
     +
Which packet size?
     +
Fragment or not?
     +
What is the expected communication cost?
```

---

# 26. Baseline Strategies

The final system will be compared against multiple baselines.

---

## Baseline 1 - Fixed Routing + Fixed Packetization

```text
Fixed Route
     +
Fixed Packet Size
     +
No Prediction
```

This provides the basic reference.

---

## Baseline 2 - Reactive Routing

```text
Current Channel State
          |
          v
Reactive Route Decision
```

This reacts to currently observed conditions.

---

## Baseline 3 - Reactive Packetization

```text
Current Channel State
          |
          v
Adaptive Packet Size
```

This evaluates packetization adaptation without future prediction.

---

## Proposed System

```text
Historical State
       |
       v
Prediction
       |
       v
Complete Route Risk
       |
       v
Route Selection
       |
       v
Packet Size Selection
       |
       v
Fragmentation Decision
       |
       v
Transmission
       |
       v
ACK/NACK
       |
       v
State Update
```

---

# 27. Final Experimental Methodology

The final experiments should use controlled and reproducible conditions.

Important parameters include:

* Node count
* Topology
* Source
* Sink
* Candidate routes
* Packet size
* Data rate
* Simulation duration
* MAC protocol
* PHY configuration
* Channel configuration
* Traffic load
* Random seed

---

## Potential Node Counts

```text
2
4
8
12
16
24
32
```

The final node-count matrix will be established after baseline validation.

---

## Potential Packet Sizes

```text
128 B
256 B
512 B
1024 B
```

---

## Routing Conditions

```text
Route A
Route B
Predictive Route Selection
```

---

## MAC Conditions

```text
ALOHA
TDMA
```

---

## Experiment Principle

Each comparison should use equivalent conditions wherever possible.

For example:

```text
Same Topology
      +
Same Traffic
      +
Same Duration
      +
Same PHY
      +
Same Seed Set
      |
      v
Different Communication Strategy
```

This allows the effect of the proposed method to be isolated more reliably.

---

# 28. Performance Metrics

The final evaluation will use multiple metrics.

---

## Packet Delivery Ratio

```text
PDR =
Successfully Delivered Packets
--------------------------------
Generated Packets
```

---

## Packet Loss

```text
Packet Loss =
Generated Packets
-
Successfully Delivered Packets
```

---

## Throughput

Measure successfully delivered application data per unit time.

---

## End-to-End Delay

Measure the time between application packet generation and successful sink delivery.

---

## Retransmissions

Measure the number of retransmissions required for successful delivery.

---

## Queue Behavior

Measure:

* Average queue
* Maximum queue
* Queue growth
* Queue stability

---

## Collision Rate

Measure communication collisions caused by overlapping transmissions.

---

## Energy

Measure:

* TX energy
* RX energy
* Idle energy
* Retransmission energy
* Fragmentation energy
* Total energy

---

## Energy per Delivered Bit

```text
Energy per Delivered Bit
=
Total Energy
---------------------------
Successfully Delivered Bits
```

---

## Network Lifetime

Measure the operating lifetime of the network according to the selected energy model.

---

## Prediction Metrics

Depending on the final prediction formulation, evaluate:

* Prediction error
* Mean absolute error
* Future-state estimation error
* Classification accuracy
* Route decision accuracy

---

# 29. Data Pipeline

The complete future data pipeline is:

```text
                         SIMULATION
                             |
                             v
                    RAW EVENT COLLECTION
                             |
                             v
                       EVENT CSV FILES
                             |
                             v
                     DATA PREPROCESSING
                             |
                             v
                    PER-LINK AGGREGATION
                             |
                             v
                     HISTORICAL DATASET
                             |
                             v
                     PREDICTION DATASET
                             |
                             v
                      PREDICTION MODEL
                             |
                             v
                    ROUTE RISK DATASET
                             |
                             v
                    DECISION EVALUATION
                             |
                             v
                      FINAL METRICS CSV
                             |
                             v
                        VISUALIZATION
                             |
                             v
                       FINAL RESULTS
```

---

# 30. Results Pipeline

The final analysis pipeline should be:

```text
Simulation
    |
    v
Raw Events
    |
    v
Clean Data
    |
    v
Aggregate Statistics
    |
    v
Multiple Seeds
    |
    v
Mean / Variance
    |
    v
Statistical Comparison
    |
    v
Graphs
    |
    v
Tables
    |
    v
Research Conclusions
```

The final conclusions should not depend on a single simulation run.

---

# 31. Visualization

Current visualization work includes:

```text
visualization/
|
+-- compare_routes_3d.py
|
+-- visualize_uwsn.py
```

The visualization system is intended to support:

* UWSN topology visualization
* Route visualization
* Route comparison
* Node positions
* Communication paths

Future visualization should include:

```text
Channel Quality vs Time
Prediction vs Actual
Route Risk vs Time
Packet Size Decisions
Fragmentation Decisions
PDR Comparison
Throughput Comparison
Delay Comparison
Retransmission Comparison
Energy Comparison
Network Lifetime
```

---

# 32. Repository Structure

The research repository is intentionally separated from the NS-3 installation.

Current and planned structure:

```text
uwsn-project/
|
+-- project/
|   |
|   +-- README.md
|   |
|   +-- simulations/
|   |   |
|   |   +-- level1/
|   |       |
|   |       +-- two-route-baseline.cc
|   |       +-- ...
|   |
|   +-- visualization/
|   |   |
|   |   +-- compare_routes_3d.py
|   |   +-- visualize_uwsn.py
|   |
|   +-- analysis/
|   |
|   +-- results/
|   |
|   +-- docs/
|   |
|   +-- configs/
|   |
|   +-- scripts/
|   |
|   +-- data/
|       |
|       +-- raw/
|       +-- processed/
|
+-- ns-allinone-3.41/
    |
    +-- ns-3.41/
```

As development progresses, additional modules will be added for:

* Prediction
* Route risk
* Packetization
* Fragmentation
* Feedback
* Energy
* Final evaluation

---

# 33. Build Environment

Current environment:

```text
Operating System:
Linux / WSL

Simulator:
NS-3.41

Underwater Framework:
Aqua-Sim NG

Primary Language:
C++

Analysis:
Python

Build System:
NS-3 build system / CMake / Ninja

Version Control:
Git
```

---

# 34. Building the Current Project

Enter the NS-3 directory:

```bash
cd ~/uwsn-project/ns-allinone-3.41/ns-3.41
```

Build NS-3:

```bash
./ns3 build
```

Build the current baseline:

```bash
./ns3 build scratch/two-route-baseline
```

The research source remains in the research repository while the NS-3 scratch directory provides the compilation entry point.

---

# 35. Running the Current Baseline

## Route A

```bash
./ns3 run "scratch/two-route-baseline --route=A --nodes=8 --packetSize=512 --simStop=30"
```

---

## Route B

```bash
./ns3 run "scratch/two-route-baseline --route=B --nodes=8 --packetSize=512 --simStop=30"
```

---

## Longer Route A Experiment

```bash
./ns3 run "scratch/two-route-baseline --route=A --nodes=8 --packetSize=512 --simStop=120"
```

---

# 36. Debugging Workflow

Because the baseline is still being validated, terminal debugging is an important part of the current development workflow.

Capture a complete experiment:

```bash
./ns3 run "scratch/two-route-baseline --route=A --nodes=8 --packetSize=512 --simStop=30" 2>&1 | tee route-A-debug.txt
```

Search routing events:

```bash
grep -E "ROUTING RECV|ROUTE LOOKUP|ROUTING SENDDOWN" route-A-debug.txt | tail -100
```

Inspect Node 6 and Node 7:

```bash
grep -E "node=6|node=7" route-A-debug.txt | tail -100
```

Inspect the event file:

```bash
head -30 route-A-events.csv
```

```bash
tail -30 route-A-events.csv
```

Inspect Node 7 events:

```bash
grep ",7," route-A-events.csv | tail -50
```

Count Node 7 collision events:

```bash
grep ",COLLISION,7," route-A-events.csv | wc -l
```

---

# 37. Experiment Reproducibility

Every final experiment should record:

```text
Experiment ID
Route
MAC protocol
Node count
Packet size
Data rate
Simulation duration
Random seed
Topology
PHY configuration
Channel configuration
Traffic configuration
```

Example:

```text
Experiment:
route-A-8nodes-512B-aloha-seed01

Route:
A

Nodes:
8

Packet:
512 B

MAC:
ALOHA

Simulation:
120 s

Seed:
01
```

Raw event traces should be retained whenever practical.

---

# 38. Current Implementation Status

The project is currently in active research development.

## Implemented

```text
+------------------------------------------+
|              IMPLEMENTED                 |
+------------------------------------------+
| NS-3.41                                  |
| Aqua-Sim NG                              |
| Controlled UWSN topology                 |
| Multi-hop communication                  |
| Route A                                  |
| Route B                                  |
| Fixed ALOHA baseline                     |
| TDMA baseline framework                  |
| Packet generation                        |
| Packet-size experiments                  |
| PHY TX tracing                           |
| PHY RX tracing                           |
| RX power tracing                         |
| Collision tracing                        |
| Queue monitoring                         |
| Delay monitoring                         |
| Raw event CSV generation                 |
| Route-specific experiments               |
+------------------------------------------+
```

---

## In Progress

```text
+------------------------------------------+
|              IN PROGRESS                 |
+------------------------------------------+
| Sink delivery validation                 |
| Correct PDR measurement                  |
| Correct throughput measurement           |
| Retransmission measurement               |
| Reproducible baseline CSV                |
| Per-link historical state extraction     |
+------------------------------------------+
```

---

## Planned

```text
+------------------------------------------+
|                 PLANNED                  |
+------------------------------------------+
| Short-term prediction                    |
| Prediction validation                    |
| Route-level risk engine                  |
| Predictive route selection               |
| Adaptive packet-size selection           |
| Fragmentation / reassembly               |
| ACK/NACK feedback                        |
| Energy model                             |
| Energy per delivered bit                |
| Network lifetime                         |
| Final integrated framework               |
| Final experimental comparison            |
+------------------------------------------+
```

---

# 39. Seven-Phase Development Roadmap

The project follows a controlled seven-phase development sequence.

```text
                         PROJECT START
                              |
                              v
                 +------------------------+
                 |       PHASE 1          |
                 |    RELIABLE BASELINE   |
                 +-----------+------------+
                             |
                             v
                 Correct Sink Delivery
                             |
                             v
                 Correct PDR / Throughput
                             |
                             v
                 Retransmission Measurement
                             |
                             v
                 Reproducible Baseline CSV
                             |
                             v
                 +------------------------+
                 |       PHASE 2          |
                 | CHANNEL-STATE EXTRACT  |
                 +-----------+------------+
                             |
                             v
                    Per-Link History
                             |
                             v
                    Historical Dataset
                             |
                             v
                 +------------------------+
                 |       PHASE 3          |
                 | SHORT-TERM PREDICTION  |
                 +-----------+------------+
                             |
                             v
                  Future Link Conditions
                             |
                             v
                  Prediction Validation
                             |
                             v
                 +------------------------+
                 |       PHASE 4          |
                 |   ROUTE-LEVEL RISK     |
                 +-----------+------------+
                             |
                             v
                   Predicted Route Risk
                             |
                             v
                    Route Selection
                             |
                             v
                 +------------------------+
                 |       PHASE 5          |
                 | ADAPTIVE PACKETIZATION |
                 +-----------+------------+
                             |
                             v
                  Packet Size Selection
                             |
                             v
                 Fragmentation Decision
                             |
                             v
                 +------------------------+
                 |       PHASE 6          |
                 |     ACK / NACK         |
                 +-----------+------------+
                             |
                             v
                       Feedback
                             |
                             v
                    State Update
                             |
                             v
                 +------------------------+
                 |       PHASE 7          |
                 |   ENERGY + LIFETIME    |
                 +-----------+------------+
                             |
                             v
                     Energy Analysis
                             |
                             v
                    Network Lifetime
                             |
                             v
                 +------------------------+
                 |   FINAL EVALUATION     |
                 +-----------+------------+
                             |
                             v
                       FINAL RESULTS
```

---

# 40. Expected Final Outputs

## Simulation Outputs

* Raw event traces
* Route-specific logs
* Packet delivery statistics
* Collision statistics
* Queue statistics
* Delay statistics
* Retransmission statistics

---

## Prediction Outputs

* Historical link state
* Predicted link state
* Prediction error
* Predicted route risk

---

## Decision Outputs

* Selected route
* Selected packet size
* Fragmentation decision
* Expected communication cost
* Actual communication outcome

---

## Energy Outputs

* TX energy
* RX energy
* Idle energy
* Retransmission energy
* Fragmentation energy
* Total energy
* Energy per delivered bit
* Network lifetime

---

## Visualization Outputs

* UWSN topology
* Route comparison
* Link-quality trends
* Prediction accuracy
* Route-risk trends
* Packetization decisions
* PDR graphs
* Throughput graphs
* Delay graphs
* Retransmission graphs
* Energy graphs
* Lifetime graphs

---

# 41. Final Research Evaluation

The final evaluation should compare the progression from fixed communication to the complete predictive framework.

```text
                  FIXED
                    |
                    v
                REACTIVE
                    |
                    v
               PREDICTIVE
                    |
                    v
          PREDICTIVE + ROUTE AWARE
                    |
                    v
      PREDICTIVE + ROUTE AWARE
          + ADAPTIVE PACKETIZATION
                    |
                    v
             COMPLETE SYSTEM
```

The final comparison should answer whether the additional intelligence provides measurable benefits.

---

## Final Comparison Table

| Strategy                 | Prediction | Route Adaptation | Packet Adaptation | Fragmentation | Feedback |
| ------------------------ | ---------- | ---------------- | ------------------ | ------------- | -------- |
| Fixed                    | No         | Fixed            | Fixed              | Fixed         | No       |
| Reactive Route           | No         | Yes               | Fixed              | Fixed         | Limited  |
| Reactive Packetization   | No         | Fixed/Reactive    | Yes                | Planned       | Limited  |
| Predictive Route         | Yes        | Yes               | Fixed/Adaptive     | Planned       | Yes      |
| Proposed Complete System | Yes        | Yes               | Yes                | Yes           | Yes      |

---

## Evaluation Dimensions

```text
RELIABILITY
    |
    +---- PDR
    +---- Packet Loss


PERFORMANCE
    |
    +---- Throughput
    +---- Delay


COMMUNICATION COST
    |
    +---- Retransmissions
    +---- Fragmentation


ENERGY
    |
    +---- Total Energy
    +---- Energy / Delivered Bit
    +---- Network Lifetime


PREDICTION
    |
    +---- Prediction Error
    +---- Decision Accuracy
```

---

# 42. Limitations

The current implementation does not yet contain all components of the final proposed system.

The following remain incomplete:

* Fully validated end-to-end sink delivery
* Final PDR implementation
* Final throughput implementation
* Complete retransmission accounting
* Complete per-link historical state pipeline
* Prediction model
* Prediction validation
* Route-risk model
* Predictive route selection
* Adaptive packet-size engine
* Fragmentation and reassembly
* ACK/NACK feedback loop
* Energy model
* Network lifetime evaluation
* Final integrated comparison

These components are documented as part of the target research architecture.

They are not represented as already implemented.

---

# 43. Research Integrity

This repository intentionally distinguishes between:

```text
IMPLEMENTED
IN PROGRESS
PLANNED
```

The final architecture can therefore be documented before every component is implemented.

The project should not claim that prediction improves performance until:

1. The baseline is validated.
2. The prediction model is implemented.
3. Prediction accuracy is measured.
4. Route-level prediction is implemented.
5. Adaptive packetization is implemented.
6. Fragmentation is implemented.
7. ACK/NACK feedback is implemented.
8. Energy accounting is implemented.
9. Controlled experiments are completed.
10. Results are compared against appropriate baselines.

This distinction is important for reproducible and defensible research.

---

# 44. Final Target Architecture

The complete final system can be summarized as:

```text
                         +----------------------+
                         |        UWSN          |
                         |      Environment     |
                         +----------+-----------+
                                    |
                                    v
                         +----------------------+
                         | Channel Observation  |
                         +----------+-----------+
                                    |
                                    v
                         +----------------------+
                         | Link-State History   |
                         +----------+-----------+
                                    |
                                    v
                         +----------------------+
                         | Prediction Engine    |
                         +----------+-----------+
                                    |
                                    v
                         +----------------------+
                         | Route Risk Engine    |
                         +----------+-----------+
                                    |
                                    v
                         +----------------------+
                         | Route Selector       |
                         +----------+-----------+
                                    |
                                    v
                         +----------------------+
                         | Packetization Engine |
                         +----------+-----------+
                                    |
                                    v
                         +----------------------+
                         | Fragmentation        |
                         | Decision             |
                         +----------+-----------+
                                    |
                                    v
                         +----------------------+
                         | MAC / Routing        |
                         +----------+-----------+
                                    |
                                    v
                         +----------------------+
                         | Aqua-Sim PHY         |
                         +----------+-----------+
                                    |
                                    v
                         +----------------------+
                         | Acoustic Channel     |
                         +----------+-----------+
                                    |
                                    v
                         +----------------------+
                         | Receiver             |
                         +----------+-----------+
                                    |
                              +-----+-----+
                              |           |
                              v           v
                             ACK         NACK
                              |           |
                              |           v
                              |     Retransmission
                              |           |
                              +-----+-----+
                                    |
                                    v
                         +----------------------+
                         | Feedback Manager      |
                         +----------+-----------+
                                    |
                                    v
                         +----------------------+
                         | State Update          |
                         +----------+-----------+
                                    |
                                    +------------->
                                      NEXT CYCLE
```

---

## Final Build at a Glance

```text
+-------------------------------------------------------------+
|                  FINAL RESEARCH SYSTEM                      |
+-------------------------------------------------------------+
|                                                             |
|  Historical Channel Data                                   |
|            |                                                |
|            v                                                |
|  Per-Link State Extraction                                 |
|            |                                                |
|            v                                                |
|  Short-Term Prediction                                     |
|            |                                                |
|            v                                                |
|  Complete Route Risk Evaluation                            |
|            |                                                |
|            v                                                |
|  Predictive Route Selection                                |
|            |                                                |
|            v                                                |
|  Adaptive Packet-Size Selection                            |
|            |                                                |
|            v                                                |
|  Fragmentation / Reassembly                                |
|            |                                                |
|            v                                                |
|  Transmission through Aqua-Sim                             |
|            |                                                |
|            v                                                |
|  ACK / NACK Feedback                                       |
|            |                                                |
|            v                                                |
|  Link-State Update                                         |
|            |                                                |
|            v                                                |
|  Energy Accounting                                         |
|            |                                                |
|            v                                                |
|  Performance Evaluation                                    |
|                                                             |
+-------------------------------------------------------------+
```

---

# 45. Conclusion

This project develops a research framework for **predictive route-aware packetization in underwater acoustic sensor networks**.

The project begins with a controlled NS-3.41 + Aqua-Sim NG simulation foundation.

The intended research progression is:

```text
Reliable Simulation
        |
        v
Reliable Measurements
        |
        v
Historical Link State
        |
        v
Short-Term Prediction
        |
        v
Route-Level Risk Prediction
        |
        v
Predictive Route Selection
        |
        v
Adaptive Packetization
        |
        v
Fragmentation
        |
        v
ACK/NACK Feedback
        |
        v
Energy Evaluation
        |
        v
Final Experimental Comparison
```

The final research question is whether predicting future underwater communication conditions and considering the complete candidate route can improve the joint trade-off between:

```text
Reliability
     +
Throughput
     +
Delay
     +
Retransmission Cost
     +
Energy Efficiency
     +
Network Lifetime
```

The project is currently focused on completing and validating the baseline and channel-state foundation before implementing the predictive components.

---

## Project Identity

**Project:** Predictive Route-Aware Packetization for Energy-Efficient Underwater Acoustic Sensor Networks

**Domain:** Underwater Wireless Sensor Networks

**Simulator:** NS-3.41

**Framework:** Aqua-Sim NG

**Primary Language:** C++

**Analysis:** Python

**Current Branch:** `predictive-route-aware`

**Current Milestone:** Reliable baseline validation and channel-state extraction

**Final Goal:** Predictive route-aware adaptive packetization with feedback and energy-aware evaluation

---

## Development Status

```text
PHASE 1  Reliable Baseline              IN PROGRESS
PHASE 2  Channel-State Extraction       PARTIAL
PHASE 3  Short-Term Prediction          PLANNED
PHASE 4  Route-Level Risk Prediction    PLANNED
PHASE 5  Adaptive Packetization         PLANNED
PHASE 6  ACK/NACK Feedback              PLANNED
PHASE 7  Energy + Network Lifetime      PLANNED

FINAL    Integrated Research System     FUTURE BUILD
```

---

**Status: Active Research Development**

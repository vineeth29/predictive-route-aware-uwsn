/*
 * baseline-mac-comparison.cc
 *
 * Controlled baseline experiment for the Adaptive UWSN MAC project.
 *
 * Baselines:
 *   1. ALOHA  - contention based
 *   2. TDMA   - scheduled access
 *
 * The network topology, PHY, channel, traffic model and simulation
 * parameters remain the same. Only the MAC protocol changes.
 */

#include "ns3/core-module.h"
#include "ns3/network-module.h"
#include "ns3/mobility-module.h"
#include "ns3/aqua-sim-ng-module.h"
#include "ns3/applications-module.h"

#include <fstream>
#include <iomanip>
#include <iostream>
#include <string>

using namespace ns3;

NS_LOG_COMPONENT_DEFINE("BaselineMacComparison");

// ------------------------------------------------------------
// Experiment statistics
// ------------------------------------------------------------

static uint64_t g_txPackets = 0;
static uint64_t g_rxPackets = 0;
static uint64_t g_phyTxPackets = 0;
static uint64_t g_phyRxPackets = 0;
static uint64_t g_collisions = 0;

static uint64_t g_totalDelayMs = 0;
static uint64_t g_delaySamples = 0;

static uint64_t g_totalQueueSize = 0;
static uint64_t g_queueSamples = 0;

// ------------------------------------------------------------
// Trace callbacks
// ------------------------------------------------------------

static void
TraceApplicationTx(Ptr<const Packet>)
{
    g_txPackets++;
}

static void
TraceMacRx(Ptr<const Packet>)
{
    g_rxPackets++;
}

static void
TracePhyTx(Ptr<Packet>, double)
{
    g_phyTxPackets++;
}

static void
TracePhyRx(Ptr<Packet>, double)
{
    g_phyRxPackets++;
}

static void
TraceCollision()
{
    g_collisions++;
}

static void
TraceDelay(uint32_t delayMs)
{
    g_totalDelayMs += delayMs;
    g_delaySamples++;
}

static void
TraceQueue(uint32_t queueSize)
{
    g_totalQueueSize += queueSize;
    g_queueSamples++;
}

// ------------------------------------------------------------
// Main
// ------------------------------------------------------------

int
main(int argc, char* argv[])
{
    // -----------------------------
    // Default experiment parameters
    // -----------------------------

    std::string mac = "aloha";

    uint32_t nodes = 10;
    double simStop = 30.0;

    uint32_t packetSize = 50;
    double dataRate = 80000.0;

    double transmissionRange = 1500.0;
    double txPower = 20.0;

    uint32_t seed = 12345;
    uint64_t run = 1;

    // -----------------------------
    // Command-line parameters
    // -----------------------------

    CommandLine cmd;

    cmd.AddValue(
        "mac",
        "MAC protocol: aloha or tdma",
        mac);

    cmd.AddValue(
        "nodes",
        "Number of underwater sensor nodes",
        nodes);

    cmd.AddValue(
        "simStop",
        "Simulation duration in seconds",
        simStop);

    cmd.AddValue(
        "packetSize",
        "Packet size in bytes",
        packetSize);

    cmd.AddValue(
        "dataRate",
        "Application data rate in bits per second",
        dataRate);

    cmd.AddValue(
        "range",
        "Underwater transmission range in meters",
        transmissionRange);

    cmd.AddValue(
        "txPower",
        "PHY transmission power in watts",
        txPower);

    cmd.AddValue(
        "seed",
        "Random seed",
        seed);

    cmd.AddValue(
        "run",
        "Random run number",
        run);

    cmd.Parse(argc, argv);

    // ------------------------------------------------------------
    // Validate MAC selection
    // ------------------------------------------------------------

    if (mac != "aloha" && mac != "tdma")
    {
        NS_FATAL_ERROR(
            "Invalid MAC. Use --mac=aloha or --mac=tdma");
    }

    // ------------------------------------------------------------
    // Reproducibility
    // ------------------------------------------------------------

    SeedManager::SetSeed(seed);
    SeedManager::SetRun(run);

    std::cout << "\n";
    std::cout << "============================================\n";
    std::cout << "      UWSN BASELINE MAC EXPERIMENT\n";
    std::cout << "============================================\n";
    std::cout << "MAC Protocol       : " << mac << "\n";
    std::cout << "Nodes              : " << nodes << "\n";
    std::cout << "Simulation Time    : " << simStop << " s\n";
    std::cout << "Packet Size        : " << packetSize << " bytes\n";
    std::cout << "Data Rate          : " << dataRate << " bps\n";
    std::cout << "Transmission Range : " << transmissionRange << " m\n";
    std::cout << "TX Power           : " << txPower << " W\n";
    std::cout << "Seed               : " << seed << "\n";
    std::cout << "Run                : " << run << "\n";
    std::cout << "============================================\n\n";

    // ------------------------------------------------------------
    // Create nodes
    // ------------------------------------------------------------

    NodeContainer nodesContainer;
    nodesContainer.Create(nodes);

    PacketSocketHelper socketHelper;
    socketHelper.Install(nodesContainer);

    // ------------------------------------------------------------
    // Aqua-Sim channel
    // ------------------------------------------------------------

    AquaSimChannelHelper channel =
        AquaSimChannelHelper::Default();

    channel.SetPropagation(
        "ns3::AquaSimRangePropagation");

    AquaSimHelper aquaHelper =
        AquaSimHelper::Default();

    aquaHelper.SetChannel(channel.Create());

    // ------------------------------------------------------------
    // Select baseline MAC
    // ------------------------------------------------------------

    if (mac == "aloha")
    {
        aquaHelper.SetMac(
            "ns3::AquaSimAloha",
            "AckOn",
            IntegerValue(0),
            "MinBackoff",
            DoubleValue(0.0),
            "MaxBackoff",
            DoubleValue(1.5));
    }
    else
    {
        aquaHelper.SetMac(
            "ns3::AquaSimTdmaMac",
            "TdmaSlotPeriod",
            UintegerValue(nodes),
            "TdmaSlotDuration",
            TimeValue(MilliSeconds(600)),
            "TdmaGuardTime",
            TimeValue(MilliSeconds(1)));
    }

    // ------------------------------------------------------------
    // Routing
    // ------------------------------------------------------------

    aquaHelper.SetRouting(
        "ns3::AquaSimRoutingDummy");

    // ------------------------------------------------------------
    // PHY
    // ------------------------------------------------------------

    aquaHelper.SetPhy(
        "ns3::AquaSimPhyCmn",
        "PT",
        DoubleValue(txPower));

    // ------------------------------------------------------------
    // Create underwater devices
    // ------------------------------------------------------------

    MobilityHelper mobility;

    Ptr<ListPositionAllocator> positionAllocator =
        CreateObject<ListPositionAllocator>();

    NetDeviceContainer devices;

    /*
     * Fixed 3D topology.
     *
     * We intentionally use fixed positions for the baseline so
     * that ALOHA and TDMA experience the exact same topology.
     */

    for (uint32_t i = 0; i < nodes; ++i)
    {
        Ptr<AquaSimNetDevice> device =
            CreateObject<AquaSimNetDevice>();

        devices.Add(
            aquaHelper.Create(
                nodesContainer.Get(i),
                device));

        // Deterministic 3D underwater arrangement.
        double x = 50.0 + (i % 5) * 100.0;
        double y = 50.0 + (i / 5) * 100.0;
        double z = -20.0 - (i % 4) * 20.0;

        positionAllocator->Add(
            Vector(x, y, z));

        device->GetPhy()->SetTransRange(
            transmissionRange);

        // TDMA node gets its own slot.
        if (mac == "tdma")
        {
            device->GetMac()->SetAttribute(
                "TdmaSlotNumber",
                UintegerValue(i));
        }
    }

    mobility.SetPositionAllocator(positionAllocator);

    mobility.SetMobilityModel(
        "ns3::ConstantPositionMobilityModel");

    mobility.Install(nodesContainer);

    // ------------------------------------------------------------
    // Application traffic
    // ------------------------------------------------------------

    for (uint32_t i = 0; i < nodes; ++i)
    {
        AquaSimApplicationHelper app(
            "ns3::PacketSocketFactory",
            nodes);

        /*
         * Poisson-like traffic generation using exponential
         * on/off periods, following the Aqua-Sim NG examples.
         */

        double meanOn =
            (packetSize * 8.0) / dataRate;

        double meanOff = 1.0 / 2.0;

        std::string onTime =
            "ns3::ExponentialRandomVariable[Mean=" +
            std::to_string(meanOn) + "]";

        std::string offTime =
            "ns3::ExponentialRandomVariable[Mean=" +
            std::to_string(meanOff) + "]";

        app.SetAttribute(
            "OnTime",
            StringValue(onTime));

        app.SetAttribute(
            "OffTime",
            StringValue(offTime));

        app.SetAttribute(
            "DataRate",
            DataRateValue(
                DataRate(dataRate)));

        app.SetAttribute(
            "PacketSize",
            UintegerValue(packetSize));

        ApplicationContainer application =
            app.Install(nodesContainer.Get(i));

        application.Start(
            Seconds(0.5));

        application.Stop(
            Seconds(simStop));
    }

    // ------------------------------------------------------------
    // Connect simulation traces
    // ------------------------------------------------------------

    Config::ConnectWithoutContext(
        "/NodeList/*/ApplicationList/*/$ns3::Application/Tx",
        MakeCallback(&TraceApplicationTx));

    Config::ConnectWithoutContext(
        "/NodeList/*/DeviceList/*/$ns3::NetDevice/Mac/RoutingRx",
        MakeCallback(&TraceMacRx));

    Config::ConnectWithoutContext(
        "/NodeList/*/DeviceList/*/$ns3::NetDevice/Mac/QueueSizeTrace",
        MakeCallback(&TraceQueue));

    Config::ConnectWithoutContext(
        "/NodeList/*/DeviceList/*/$ns3::NetDevice/Mac/E2EDelayTrace",
        MakeCallback(&TraceDelay));

    Config::ConnectWithoutContext(
        "/NodeList/*/DeviceList/*/$ns3::NetDevice/Phy/Tx",
        MakeCallback(&TracePhyTx));

    Config::ConnectWithoutContext(
        "/NodeList/*/DeviceList/*/$ns3::NetDevice/Phy/Rx",
        MakeCallback(&TracePhyRx));

    Config::ConnectWithoutContext(
        "/NodeList/*/DeviceList/*/$ns3::NetDevice/Phy/RxColl",
        MakeCallback(&TraceCollision));

    // ------------------------------------------------------------
    // Run simulation
    // ------------------------------------------------------------

    std::cout << "----------- Running Simulation -----------\n";

    Simulator::Stop(
        Seconds(simStop));

    Simulator::Run();

    // ------------------------------------------------------------
    // Calculate metrics
    // ------------------------------------------------------------

    double pdr = 0.0;

    if (g_txPackets > 0)
    {
        pdr =
            100.0 *
            static_cast<double>(g_rxPackets) /
            static_cast<double>(g_txPackets);
    }

    double throughputKbps =
        (static_cast<double>(g_rxPackets) *
         packetSize * 8.0) /
        simStop /
        1000.0;

    double averageDelayMs = 0.0;

    if (g_delaySamples > 0)
    {
        averageDelayMs =
            static_cast<double>(g_totalDelayMs) /
            static_cast<double>(g_delaySamples);
    }

    double averageQueue = 0.0;

    if (g_queueSamples > 0)
    {
        averageQueue =
            static_cast<double>(g_totalQueueSize) /
            static_cast<double>(g_queueSamples);
    }

    // ------------------------------------------------------------
    // Print results
    // ------------------------------------------------------------

    std::cout << "\n";
    std::cout << "============================================\n";
    std::cout << "              RESULTS\n";
    std::cout << "============================================\n";

    std::cout << "MAC Protocol       : " << mac << "\n";
    std::cout << "Application TX     : " << g_txPackets << "\n";
    std::cout << "MAC RX             : " << g_rxPackets << "\n";
    std::cout << "PHY TX             : " << g_phyTxPackets << "\n";
    std::cout << "PHY RX             : " << g_phyRxPackets << "\n";
    std::cout << "Collisions         : " << g_collisions << "\n";

    std::cout << std::fixed
              << std::setprecision(3);

    std::cout << "PDR                : "
              << pdr << " %\n";

    std::cout << "Throughput         : "
              << throughputKbps << " kbps\n";

    std::cout << "Average Delay      : "
              << averageDelayMs << " ms\n";

    std::cout << "Average Queue      : "
              << averageQueue << "\n";

    std::cout << "============================================\n";

    // ------------------------------------------------------------
    // Save result to CSV
    // ------------------------------------------------------------

    std::string resultFile =
        "baseline-" + mac + ".csv";

    std::ofstream results(resultFile);

    results << "mac,nodes,simStop,packetSize,dataRate,"
            << "txPackets,rxPackets,phyTx,phyRx,"
            << "collisions,pdr,throughputKbps,"
            << "averageDelayMs,averageQueue\n";

    results << mac << ","
            << nodes << ","
            << simStop << ","
            << packetSize << ","
            << dataRate << ","
            << g_txPackets << ","
            << g_rxPackets << ","
            << g_phyTxPackets << ","
            << g_phyRxPackets << ","
            << g_collisions << ","
            << pdr << ","
            << throughputKbps << ","
            << averageDelayMs << ","
            << averageQueue << "\n";

    results.close();

    Simulator::Destroy();

    std::cout << "\nResults saved to: "
              << resultFile << "\n";

    std::cout << "Simulation finished successfully.\n";

    return 0;
}

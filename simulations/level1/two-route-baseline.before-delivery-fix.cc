/*
 * two-route-baseline.cc
 *
 * Controlled UWSN fixed-route baseline.
 *
 * Purpose:
 *   Compare two fixed routes under identical:
 *     - topology
 *     - traffic
 *     - PHY
 *     - MAC
 *     - simulation time
 *
 * Route A:
 *   Node 0 -> forward path -> Sink
 *
 * Route B:
 *   Node 0 -> alternate path -> Sink
 *
 * Main metrics:
 *   - Packet Delivery Ratio
 *   - Packet Loss
 *   - Throughput
 *   - End-to-End Delay
 *   - Queue
 *   - PHY TX/RX
 *   - Collisions
 *
 * Real PHY events are written to CSV for later 3D visualization.
 */

#include "ns3/core-module.h"
#include "ns3/network-module.h"
#include "ns3/mobility-module.h"
#include "ns3/aqua-sim-ng-module.h"
#include "ns3/applications-module.h"
#include "ns3/aqua-sim-routing-static.h"

#include <fstream>
#include <iomanip>
#include <iostream>
#include <string>
#include <vector>
#include <unordered_set>

using namespace ns3;

NS_LOG_COMPONENT_DEFINE("TwoRouteBaseline");

// ============================================================
// GLOBAL STATISTICS
// ============================================================

static uint64_t g_txPackets = 0;
static uint64_t g_rxPackets = 0;

static uint64_t g_phyTxPackets = 0;
static uint64_t g_phyRxPackets = 0;

static uint64_t g_collisions = 0;

static uint64_t g_totalDelayMs = 0;
static uint64_t g_delaySamples = 0;

static uint64_t g_totalQueueSize = 0;
static uint64_t g_queueSamples = 0;

static std::ofstream* g_eventFile = nullptr;
static std::unordered_set<uint64_t> g_deliveredPacketUids;


// ============================================================
// SINK RX
// ============================================================
//
// Aqua-Sim's RoutingRx trace is emitted for every node. For the
// delivery metric we connect this callback only to the sink node
// (NodeList[nodes-1]) so intermediate forwarding is not counted.
//
// Packet UIDs are tracked so a duplicate copy/reception of the same
// application packet is not counted as a second successful delivery.
// ============================================================

static void
TraceSinkRx(Ptr<const Packet> packet)
{
    if (packet != nullptr)
    {
        const uint64_t uid = packet->GetUid();

        if (g_deliveredPacketUids.insert(uid).second)
        {
            g_rxPackets++;
        }
    }
}


// ============================================================
// APPLICATION TX
// ============================================================

static void
TraceApplicationTx(Ptr<const Packet>)
{
    g_txPackets++;
}


// ============================================================
// REAL PHY TX
// ============================================================

static void
TracePhyTx(
    uint32_t nodeId,
    Ptr<Packet> packet,
    double noise)
{
    g_phyTxPackets++;

    if (g_eventFile != nullptr)
    {
        (*g_eventFile)
            << std::fixed
            << std::setprecision(6)
            << Simulator::Now().GetSeconds()
            << ",TX,"
            << nodeId
            << ","
            << packet->GetUid()
            << ","
            << noise
            << "\n";
    }
}


// ============================================================
// REAL PHY RX
// ============================================================

static void
TracePhyRx(
    uint32_t nodeId,
    Ptr<Packet> packet,
    double noise)
{
    g_phyRxPackets++;

    if (g_eventFile != nullptr)
    {
        (*g_eventFile)
            << std::fixed
            << std::setprecision(6)
            << Simulator::Now().GetSeconds()
            << ",RX,"
            << nodeId
            << ","
            << packet->GetUid()
            << ","
            << noise
            << "\n";
    }
}


// ============================================================
// REAL PHY COLLISION
// ============================================================

static void
TraceCollision(uint32_t nodeId)
{
    g_collisions++;

    if (g_eventFile != nullptr)
    {
        (*g_eventFile)
            << std::fixed
            << std::setprecision(6)
            << Simulator::Now().GetSeconds()
            << ",COLLISION,"
            << nodeId
            << ",,"
            << "\n";
    }
}


// ============================================================
// DELAY
// ============================================================

static void
TraceDelay(uint32_t delayMs)
{
    g_totalDelayMs += delayMs;
    g_delaySamples++;
}


// ============================================================
// QUEUE
// ============================================================

static void
TraceQueue(uint32_t queueSize)
{
    g_totalQueueSize += queueSize;
    g_queueSamples++;
}


// ============================================================
// WRITE ROUTE FILE
//
// Aqua-Sim static routing format:
//
// current_node:destination_node:next_hop
//
// We use actual Aqua-Sim addresses rather than assuming
// node ID == AquaSimAddress.
// ============================================================

static std::string
CreateRouteFile(
    const std::string& route,
    const std::vector<uint32_t>& addressValues,
    uint32_t nodes)
{
    std::string filename;

    if (route == "A")
    {
        filename = "route-A.txt";
    }
    else
    {
        filename = "route-B.txt";
    }

    std::ofstream routeFile(filename);

    if (!routeFile.is_open())
    {
        NS_FATAL_ERROR(
            "Could not create route file: "
            << filename);
    }

    uint32_t sinkIndex = nodes - 1;

    /*
     * Route A:
     *
     * 0 -> 1 -> 2 -> ... -> sink
     *
     * Route B:
     *
     * 0 -> alternate half -> ... -> sink
     */

    std::vector<uint32_t> path;

    if (route == "A")
    {
        for (uint32_t i = 0; i < nodes; ++i)
        {
            path.push_back(i);
        }
    }
    else
    {
        path.push_back(0);

        if (nodes > 4)
        {
            uint32_t mid = nodes / 2;

            if (mid != 0 && mid != sinkIndex)
            {
                path.push_back(mid);
            }

            if (mid + 1 < sinkIndex)
            {
                path.push_back(mid + 1);
            }
        }

        if (path.back() != sinkIndex)
        {
            path.push_back(sinkIndex);
        }
    }

    /*
     * Remove accidental duplicate nodes.
     */
    std::vector<uint32_t> cleanPath;

    for (uint32_t node : path)
    {
        bool alreadyPresent = false;

        for (uint32_t existing : cleanPath)
        {
            if (existing == node)
            {
                alreadyPresent = true;
                break;
            }
        }

        if (!alreadyPresent)
        {
            cleanPath.push_back(node);
        }
    }

    /*
     * Each node on the path needs:
     *
     * current : sink : next-hop
     */
    for (size_t i = 0; i + 1 < cleanPath.size(); ++i)
    {
        uint32_t current = cleanPath[i];
        uint32_t nextHop = cleanPath[i + 1];

        routeFile
            << addressValues[current]
            << ":"
            << addressValues[sinkIndex]
            << ":"
            << addressValues[nextHop]
            << "\n";
    }

    routeFile.close();

    std::cout
        << "\nRoute "
        << route
        << " path: ";

    for (size_t i = 0; i < cleanPath.size(); ++i)
    {
        std::cout
            << "Node "
            << cleanPath[i];

        if (i + 1 < cleanPath.size())
        {
            std::cout << " -> ";
        }
    }

    std::cout << "\n";

    return filename;
}


// ============================================================
// MAIN
// ============================================================

int
main(int argc, char* argv[])
{
    // --------------------------------------------------------
    // Default parameters
    // --------------------------------------------------------

    std::string mac = "aloha";

    std::string route = "A";

    uint32_t nodes = 8;

    double simStop = 30.0;

    uint32_t packetSize = 512;

    double dataRate = 80000.0;

    double transmissionRange = 1500.0;

    double txPower = 20.0;

    uint32_t seed = 12345;

    uint64_t run = 1;


    // --------------------------------------------------------
    // Command line
    // --------------------------------------------------------

    CommandLine cmd;

    cmd.AddValue(
        "mac",
        "MAC protocol: aloha or tdma",
        mac);

    cmd.AddValue(
        "route",
        "Fixed route: A or B",
        route);

    cmd.AddValue(
        "nodes",
        "Number of underwater nodes",
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


    // --------------------------------------------------------
    // Validation
    // --------------------------------------------------------

    if (mac != "aloha" && mac != "tdma")
    {
        NS_FATAL_ERROR(
            "Invalid MAC. Use --mac=aloha or --mac=tdma");
    }

    if (route != "A" && route != "B")
    {
        NS_FATAL_ERROR(
            "Invalid route. Use --route=A or --route=B");
    }

    if (nodes < 4)
    {
        NS_FATAL_ERROR(
            "Use at least 4 nodes.");
    }


    // --------------------------------------------------------
    // Reproducibility
    // --------------------------------------------------------

    SeedManager::SetSeed(seed);

    SeedManager::SetRun(run);


    // --------------------------------------------------------
    // Event file
    // --------------------------------------------------------

    std::string eventFile;

    if (route == "A")
    {
        eventFile = "route-A-events.csv";
    }
    else
    {
        eventFile = "route-B-events.csv";
    }

    std::ofstream events(eventFile);

    if (!events.is_open())
    {
        NS_FATAL_ERROR(
            "Could not open event file: "
            << eventFile);
    }

    events
        << "time,event,node,packet,noise\n";

    g_eventFile = &events;


    // --------------------------------------------------------
    // Reset statistics
    // --------------------------------------------------------

    g_txPackets = 0;
    g_rxPackets = 0;

    g_phyTxPackets = 0;
    g_phyRxPackets = 0;

    g_collisions = 0;

    g_totalDelayMs = 0;
    g_delaySamples = 0;

    g_totalQueueSize = 0;
    g_queueSamples = 0;
    g_deliveredPacketUids.clear();


    // --------------------------------------------------------
    // Configuration
    // --------------------------------------------------------

    std::cout << "\n";

    std::cout
        << "============================================\n";

    std::cout
        << "        UWSN TWO-ROUTE BASELINE\n";

    std::cout
        << "============================================\n";

    std::cout
        << "MAC Protocol       : "
        << mac
        << "\n";

    std::cout
        << "Route              : "
        << route
        << "\n";

    std::cout
        << "Nodes              : "
        << nodes
        << "\n";

    std::cout
        << "Source             : Node 0\n";

    std::cout
        << "Sink               : Node "
        << nodes - 1
        << "\n";

    std::cout
        << "Simulation Time    : "
        << simStop
        << " s\n";

    std::cout
        << "Packet Size        : "
        << packetSize
        << " bytes\n";

    std::cout
        << "Data Rate          : "
        << dataRate
        << " bps\n";

    std::cout
        << "Transmission Range : "
        << transmissionRange
        << " m\n";

    std::cout
        << "TX Power           : "
        << txPower
        << " W\n";

    std::cout
        << "Seed               : "
        << seed
        << "\n";

    std::cout
        << "Run                : "
        << run
        << "\n";

    std::cout
        << "Event File         : "
        << eventFile
        << "\n";

    std::cout
        << "============================================\n";


    // --------------------------------------------------------
    // Create nodes
    // --------------------------------------------------------

    NodeContainer nodesContainer;

    nodesContainer.Create(nodes);


    // --------------------------------------------------------
    // Packet sockets
    // --------------------------------------------------------

    PacketSocketHelper socketHelper;

    socketHelper.Install(nodesContainer);


    // --------------------------------------------------------
    // Aqua-Sim channel
    // --------------------------------------------------------

    AquaSimChannelHelper channel =
        AquaSimChannelHelper::Default();

    channel.SetPropagation(
        "ns3::AquaSimRangePropagation");


    AquaSimHelper aquaHelper =
        AquaSimHelper::Default();

    aquaHelper.SetChannel(
        channel.Create());


    // --------------------------------------------------------
    // MAC
    // --------------------------------------------------------

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


    // --------------------------------------------------------
    // STATIC ROUTING
    // --------------------------------------------------------

    aquaHelper.SetRouting(
        "ns3::AquaSimStaticRouting");


    // --------------------------------------------------------
    // PHY
    // --------------------------------------------------------

    aquaHelper.SetPhy(
        "ns3::AquaSimPhyCmn",
        "PT",
        DoubleValue(txPower));


    // --------------------------------------------------------
    // Mobility and devices
    // --------------------------------------------------------

    MobilityHelper mobility;

    Ptr<ListPositionAllocator> positionAllocator =
        CreateObject<ListPositionAllocator>();

    NetDeviceContainer devices;


    /*
     * Actual Aqua-Sim addresses.
     *
     * We store them because static routing uses
     * AquaSimAddress values rather than Node IDs.
     */

    std::vector<uint32_t> addressValues;

    addressValues.resize(nodes);


    // --------------------------------------------------------
    // Create underwater devices
    // --------------------------------------------------------

    for (uint32_t i = 0;
         i < nodes;
         ++i)
    {
        Ptr<AquaSimNetDevice> device =
            CreateObject<AquaSimNetDevice>();

        devices.Add(
            aquaHelper.Create(
                nodesContainer.Get(i),
                device));


        // ----------------------------------------------------
        // Store Aqua-Sim address
        // ----------------------------------------------------

        addressValues[i] =
            AquaSimAddress::ConvertFrom(
                device->GetAddress()).GetAsInt();


        // ----------------------------------------------------
        // 3D position
        // ----------------------------------------------------

        double x =
            50.0 + (i % 5) * 100.0;

        double y =
            50.0 + (i / 5) * 100.0;

        double z =
            -20.0 - (i % 4) * 20.0;

        positionAllocator->Add(
            Vector(x, y, z));


        // ----------------------------------------------------
        // PHY range
        // ----------------------------------------------------

        device->GetPhy()->SetTransRange(
            transmissionRange);


        // ----------------------------------------------------
        // REAL PHY traces
        // ----------------------------------------------------

        Ptr<AquaSimPhy> phy =
            device->GetPhy();


        phy->TraceConnectWithoutContext(
            "Tx",
            MakeBoundCallback(
                &TracePhyTx,
                i));


        phy->TraceConnectWithoutContext(
            "Rx",
            MakeBoundCallback(
                &TracePhyRx,
                i));


        phy->TraceConnectWithoutContext(
            "RxColl",
            MakeBoundCallback(
                &TraceCollision,
                i));


        // ----------------------------------------------------
        // TDMA slot
        // ----------------------------------------------------

        if (mac == "tdma")
        {
            device->GetMac()->SetAttribute(
                "TdmaSlotNumber",
                UintegerValue(i));
        }
    }


    // --------------------------------------------------------
    // Install mobility
    // --------------------------------------------------------

    mobility.SetPositionAllocator(
        positionAllocator);

    mobility.SetMobilityModel(
        "ns3::ConstantPositionMobilityModel");

    mobility.Install(
        nodesContainer);


    // --------------------------------------------------------
    // Create route table
    // --------------------------------------------------------

    std::string routeFile =
        CreateRouteFile(
            route,
            addressValues,
            nodes);


    // --------------------------------------------------------
    // Load route table into each static routing object
    //
    // Important:
    // The routing object needs its NetDevice first.
    // Therefore the route file is loaded AFTER devices exist.
    // --------------------------------------------------------

    for (uint32_t i = 0;
         i < nodes;
         ++i)
    {
        Ptr<AquaSimNetDevice> device =
            DynamicCast<AquaSimNetDevice>(
                devices.Get(i));

        Ptr<AquaSimStaticRouting> routing =
            DynamicCast<AquaSimStaticRouting>(
                device->GetRouting());

        if (routing == nullptr)
        {
            NS_FATAL_ERROR(
                "Static routing object was not created.");
        }

        std::vector<char> routePath(
            routeFile.begin(),
            routeFile.end());

        routePath.push_back('\0');

        routing->SetRouteTable(
            routePath.data());
    }


    // --------------------------------------------------------
    // Print addresses
    // --------------------------------------------------------

    std::cout
        << "\nAqua-Sim addresses:\n";

    for (uint32_t i = 0;
         i < nodes;
         ++i)
    {
        std::cout
            << "Node "
            << i
            << " -> Address "
            << addressValues[i]
            << "\n";
    }


    // --------------------------------------------------------
    // Explicit source -> sink socket
    // --------------------------------------------------------

    PacketSocketAddress socket;

    socket.SetAllDevices();

    socket.SetPhysicalAddress(
        devices.Get(nodes - 1)->GetAddress());

    socket.SetProtocol(0);


    // --------------------------------------------------------
    // Source application
    // --------------------------------------------------------

    OnOffHelper app(
        "ns3::PacketSocketFactory",
        Address(socket));


    /*
     * Exponential ON/OFF traffic.
     *
     * This preserves the stochastic traffic behaviour
     * from the original baseline.
     */

    double meanOn =
        (packetSize * 8.0) /
        dataRate;

    double meanOff =
        1.0 / 2.0;


    std::string onTime =
        "ns3::ExponentialRandomVariable[Mean=" +
        std::to_string(meanOn) +
        "]";


    std::string offTime =
        "ns3::ExponentialRandomVariable[Mean=" +
        std::to_string(meanOff) +
        "]";


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


    // --------------------------------------------------------
    // Install ONLY on source Node 0
    // --------------------------------------------------------

    ApplicationContainer sourceApplication =
        app.Install(
            nodesContainer.Get(0));


    sourceApplication.Start(
        Seconds(0.5));


    sourceApplication.Stop(
        Seconds(simStop));


    // --------------------------------------------------------
    // Sink socket
    // --------------------------------------------------------

    Ptr<Node> sinkNode =
        nodesContainer.Get(nodes - 1);


    TypeId psfid =
        TypeId::LookupByName(
            "ns3::PacketSocketFactory");


    Ptr<Socket> sinkSocket =
        Socket::CreateSocket(
            sinkNode,
            psfid);


    sinkSocket->Bind(socket);


    // --------------------------------------------------------
    // Application TX trace
    // --------------------------------------------------------

    Config::ConnectWithoutContext(
        "/NodeList/*/ApplicationList/*/$ns3::Application/Tx",
        MakeCallback(&TraceApplicationTx));


    // --------------------------------------------------------
    // SINK RX trace
    // --------------------------------------------------------
    //
    // RoutingRx is emitted at every node. Counting it globally
    // counts intermediate forwards as deliveries and can produce
    // PDR values above 100%.
    //
    // Connect only to the sink node.
    // --------------------------------------------------------

    std::string sinkRoutingRxPath =
        "/NodeList/" +
        std::to_string(nodes - 1) +
        "/DeviceList/*/$ns3::NetDevice/Mac/RoutingRx";

    Config::ConnectWithoutContext(
        sinkRoutingRxPath,
        MakeCallback(&TraceSinkRx));


    // --------------------------------------------------------
    // Queue trace
    // --------------------------------------------------------

    Config::ConnectWithoutContext(
        "/NodeList/*/DeviceList/*/$ns3::NetDevice/Mac/QueueSizeTrace",
        MakeCallback(&TraceQueue));


    // --------------------------------------------------------
    // Delay trace
    // --------------------------------------------------------

    Config::ConnectWithoutContext(
        "/NodeList/*/DeviceList/*/$ns3::NetDevice/Mac/E2EDelayTrace",
        MakeCallback(&TraceDelay));


    // --------------------------------------------------------
    // Run
    // --------------------------------------------------------

    std::cout
        << "\n----------- Running Simulation -----------\n";


    Simulator::Stop(
        Seconds(simStop));


    Simulator::Run();


    // ========================================================
    // RESULTS
    // ========================================================

    double pdr = 0.0;

    if (g_txPackets > 0)
    {
        pdr =
            100.0 *
            static_cast<double>(g_rxPackets) /
            static_cast<double>(g_txPackets);
    }


    double packetLoss =
        100.0 - pdr;


    double throughputKbps =
        (
            static_cast<double>(g_rxPackets) *
            packetSize *
            8.0
        )
        /
        simStop
        /
        1000.0;


    double averageDelayMs = 0.0;

    if (g_delaySamples > 0)
    {
        averageDelayMs =
            static_cast<double>(
                g_totalDelayMs)
            /
            static_cast<double>(
                g_delaySamples);
    }


    double averageQueue = 0.0;

    if (g_queueSamples > 0)
    {
        averageQueue =
            static_cast<double>(
                g_totalQueueSize)
            /
            static_cast<double>(
                g_queueSamples);
    }


    // --------------------------------------------------------
    // Print results
    // --------------------------------------------------------

    std::cout << "\n";

    std::cout
        << "============================================\n";

    std::cout
        << "                 RESULTS\n";

    std::cout
        << "============================================\n";

    std::cout
        << "MAC Protocol       : "
        << mac
        << "\n";

    std::cout
        << "Route              : "
        << route
        << "\n";

    std::cout
        << "Source             : Node 0\n";

    std::cout
        << "Sink               : Node "
        << nodes - 1
        << "\n";

    std::cout
        << "Application TX     : "
        << g_txPackets
        << "\n";

    std::cout
        << "Sink RX            : "
        << g_rxPackets
        << "\n";

    std::cout
        << "PHY TX             : "
        << g_phyTxPackets
        << "\n";

    std::cout
        << "PHY RX             : "
        << g_phyRxPackets
        << "\n";

    std::cout
        << "Collisions         : "
        << g_collisions
        << "\n";

    std::cout
        << std::fixed
        << std::setprecision(3);

    std::cout
        << "PDR                : "
        << pdr
        << " %\n";

    std::cout
        << "Packet Loss        : "
        << packetLoss
        << " %\n";

    std::cout
        << "Throughput         : "
        << throughputKbps
        << " kbps\n";

    std::cout
        << "Average Delay      : "
        << averageDelayMs
        << " ms\n";

    std::cout
        << "Average Queue      : "
        << averageQueue
        << "\n";

    std::cout
        << "============================================\n";


    // --------------------------------------------------------
    // Save aggregate result
    // --------------------------------------------------------

    std::string resultFile =
        "two-route-" +
        route +
        "-" +
        mac +
        ".csv";


    std::ofstream results(
        resultFile);


    if (!results.is_open())
    {
        NS_FATAL_ERROR(
            "Could not open result file: "
            << resultFile);
    }


    results
        << "route,mac,nodes,simStop,packetSize,dataRate,"
        << "txPackets,rxPackets,phyTx,phyRx,"
        << "collisions,pdr,packetLoss,throughputKbps,"
        << "averageDelayMs,averageQueue\n";


    results
        << route
        << ","
        << mac
        << ","
        << nodes
        << ","
        << simStop
        << ","
        << packetSize
        << ","
        << dataRate
        << ","
        << g_txPackets
        << ","
        << g_rxPackets
        << ","
        << g_phyTxPackets
        << ","
        << g_phyRxPackets
        << ","
        << g_collisions
        << ","
        << pdr
        << ","
        << packetLoss
        << ","
        << throughputKbps
        << ","
        << averageDelayMs
        << ","
        << averageQueue
        << "\n";


    results.close();


    // --------------------------------------------------------
    // Close event file
    // --------------------------------------------------------

    events.flush();

    events.close();

    g_eventFile = nullptr;


    // --------------------------------------------------------
    // Destroy
    // --------------------------------------------------------

    Simulator::Destroy();


    std::cout
        << "\nRoute file saved to: "
        << routeFile
        << "\n";


    std::cout
        << "Results saved to: "
        << resultFile
        << "\n";


    std::cout
        << "Events saved to: "
        << eventFile
        << "\n";


    std::cout
        << "Simulation finished successfully.\n";


    return 0;
}
